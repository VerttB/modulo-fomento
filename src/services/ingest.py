import httpx
import logging
import time
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.enums import AreaConhecimentoTipo, PesquisadorStatus
from src.core.exceptions import ExternalLookupError, IngestFormatError
from src.models import (
    AreaConhecimento,
    Bolsa,
    Departamento,
    Instituicao,
    PalavraChave,
    Projeto,
    Unidade,
    Pesquisador,
)
from src.schemas.ingest import IngestResponse
from src.services.ingest_lookup import consultar_pesquisador, salvar_pesquisador
from src.services.ingest_reader import (
    ler_planilha,
    mapear_colunas,
    normalizar,
    normalizar_cpf,
    parse_data,
    texto_linha,
)

TIMEOUT_API_SEGUNDOS = 20.0

logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)


def _obter_area(
    db: Session,
    termo: str | None,
    tipo: AreaConhecimentoTipo,
    pai: AreaConhecimento | None,
) -> tuple[AreaConhecimento | None, bool]:
    if not termo:
        return None, False
    termo_normalizado = normalizar(termo)
    pai_id = pai.id if pai else None
    area = db.scalar(
        select(AreaConhecimento).where(
            AreaConhecimento.tipo == tipo,
            AreaConhecimento.termo_normalizado == termo_normalizado,
            AreaConhecimento.pai_id == pai_id,
        )
    )
    if area:
        return area, False
    area = AreaConhecimento(
        termo=termo,
        termo_normalizado=termo_normalizado,
        tipo=tipo,
        pai_id=pai_id,
    )
    db.add(area)
    db.flush()
    return area, True


def _obter_instituicao(
    db: Session, nome: str | None, cep: str | None, sigla: str | None
) -> Instituicao:
    if sigla:
        instituicao = db.scalar(select(Instituicao).where(Instituicao.sigla == sigla))
        if instituicao is not None:
            return instituicao
        # Mesma instituição com outra sigla: reaproveita pelo nome em vez
        # de criar duplicada (nome é único) e estourar UniqueViolation.
        if nome:
            instituicao = db.scalar(select(Instituicao).where(Instituicao.nome == nome))
            if instituicao is not None:
                if instituicao.sigla is None:
                    instituicao.sigla = sigla
                    db.flush()
                return instituicao
            instituicao = Instituicao(nome=nome, cep=cep, sigla=sigla)
            db.add(instituicao)
            db.flush()
            return instituicao
    if nome:
        instituicao = db.scalar(select(Instituicao).where(Instituicao.nome == nome))
        if instituicao is None:
            instituicao = Instituicao(nome=nome, cep=cep, sigla=sigla)
            db.add(instituicao)
            db.flush()
        return instituicao
    instituicao = db.scalar(
        select(Instituicao).where(
            Instituicao.sigla.is_(None), Instituicao.nome.is_(None)
        )
    )
    if instituicao is None:
        instituicao = Instituicao(nome=nome, cep=cep, sigla=sigla)
        db.add(instituicao)
        db.flush()
    return instituicao


def _obter_departamento(
    db: Session,
    nome: str | None,
    unidade: str | None,
    cep: str | None,
    instituicao_id: int,
    grande_area_id: int | None = None,
) -> Departamento:
    departamento = db.scalar(
        select(Departamento).where(
            Departamento.instituicao_id == instituicao_id,
            Departamento.nome == nome,
        )
    )
    if departamento is None:
        departamento = Departamento(
            nome=nome,
            unidade=unidade,
            cep=cep,
            instituicao_id=instituicao_id,
            grande_area_id=grande_area_id,
        )
        db.add(departamento)
        db.flush()
    elif departamento.grande_area_id is None and grande_area_id is not None:
        departamento.grande_area_id = grande_area_id
        db.flush()
    return departamento


def _obter_unidade(
    db: Session, nome: str | None, cep: str | None, departamento: Departamento
) -> Unidade:
    # Uma unidade pode pertencer a vários departamentos: reutiliza a
    # unidade existente e apenas garante o vínculo com o departamento atual.
    if nome:
        unidade = db.scalar(select(Unidade).where(Unidade.nome == nome))
    else:
        unidade = db.scalar(
            select(Unidade)
            .join(Unidade.departamentos)
            .where(Unidade.nome.is_(None), Departamento.id == departamento.id)
        )
    if unidade is None:
        unidade = Unidade(nome=nome, cep=cep)
        unidade.departamentos.append(departamento)
        db.add(unidade)
        db.flush()
    elif departamento not in unidade.departamentos:
        unidade.departamentos.append(departamento)
        db.flush()
    return unidade


def _obter_projeto(
    db: Session, nome: str | None, resumo: str | None, grande: str | None, subarea: str | None
) -> tuple[Projeto, bool]:
    projeto = db.scalar(
        select(Projeto).where(Projeto.nome == nome, Projeto.resumo == resumo)
    )
    if projeto:
        if not projeto.grande_area and grande:
            projeto.grande_area = grande
            db.flush()
        if not projeto.subarea and subarea:
            projeto.subarea = subarea
            db.flush()
        return projeto, False
    projeto = Projeto(
        nome=nome,
        resumo=resumo,
        grande_area=grande,
        subarea=subarea,
    )
    db.add(projeto)
    db.flush()
    return projeto, True


def _adicionar_palavras_chave(
    db: Session, row: list, indices: dict[str, int], projeto: Projeto
) -> int:
    criadas = 0
    for numero in range(1, 5):
        termo = texto_linha(row, indices, f"pal chave{numero}")
        if not termo:
            continue
        termo_normalizado = normalizar(termo)
        palavra = db.scalar(
            select(PalavraChave).where(
                PalavraChave.termo_normalizado == termo_normalizado
            )
        )
        if palavra is None:
            palavra = PalavraChave(
                termo=termo,
                termo_normalizado=termo_normalizado,
            )
            db.add(palavra)
            db.flush()
            criadas += 1
        if palavra not in projeto.palavras_chave:
            projeto.palavras_chave.append(palavra)
    return criadas


def _preparar_linhas(
    rows: list[list],
    indices: dict[str, int],
    epoch,
) -> tuple[list[tuple[int, list, str, object, object, object]], int, list[str]]:
    preparadas = []
    chaves_vistas: set[tuple] = set()
    duplicadas = 0

    for numero, row in enumerate(rows[1:], start=2):
        if not any(valor is not None and str(valor).strip() for valor in row):
            continue
        try:
            # Único campo obrigatório do ingest: só o CPF aponta erro quando vazio.
            cpf_bruto = texto_linha(row, indices, "cpf_pesquisador")
            if not cpf_bruto:
                raise IngestFormatError("CPF do pesquisador vazio.")
            cpf = normalizar_cpf(cpf_bruto)
            inicio = parse_data(texto_linha(row, indices, "data inicial"), epoch)
            saida = parse_data(texto_linha(row, indices, "data final 1"), epoch)
            termino = parse_data(texto_linha(row, indices, "data final 2"), epoch)
            if inicio and saida and saida < inicio:
                raise IngestFormatError("A primeira Data Final não pode ser anterior à Data Inicial.")
            if inicio and termino and termino < inicio:
                raise IngestFormatError("A última Data Final não pode ser anterior à Data Inicial.")

            chave = (cpf, inicio, saida, termino)
            if chave in chaves_vistas:
                duplicadas += 1
                continue

            chaves_vistas.add(chave)
            preparadas.append((numero, row, cpf, inicio, saida, termino))
        except IngestFormatError as error:
            raise IngestFormatError(f"Linha {numero}: {error}") from error

    periodos_por_cpf: dict[str, list[tuple[object, object, int]]] = {}
    for numero, _, cpf, inicio, _, termino in preparadas:
        if inicio is None:
            continue
        periodos_por_cpf.setdefault(cpf, []).append((inicio, termino, numero))

    numeros_ignorados: set[int] = set()
    erros: list[str] = []

    for cpf, periodos in periodos_por_cpf.items():
        periodos.sort(key=lambda periodo: periodo[0])
        fim_anterior = None
        linha_anterior = None
        for inicio, termino, numero in periodos:
            if linha_anterior is not None and (
                fim_anterior is None or inicio < fim_anterior
            ):
                # Sobreposição não aborta o ingest: a linha posterior é
                # ignorada (sem inserção) e as demais seguem normalmente.
                numeros_ignorados.add(numero)
                erros.append(
                    f"O CPF {cpf} possui bolsas sobrepostas nas linhas "
                    f"{linha_anterior} e {numero}."
                )
                continue
            fim_anterior = termino
            linha_anterior = numero

    if not preparadas:
        raise IngestFormatError("O arquivo não contém linhas de dados.")
    if numeros_ignorados:
        preparadas = [item for item in preparadas if item[0] not in numeros_ignorados]
        erros.sort(key=lambda mensagem: mensagem)
    return preparadas, duplicadas, erros


def _periodos_se_sobrepoem(
    inicio_a, fim_a, inicio_b, fim_b
) -> bool:
    if inicio_a is None or inicio_b is None:
        return False
    return (fim_a is None or inicio_b < fim_a) and (
        fim_b is None or inicio_a < fim_b
    )


def ingerir_arquivo(db: Session, nome_arquivo: str, conteudo: bytes) -> IngestResponse:
    marco_zero = time.perf_counter()
    logger.info("Ingestão iniciada: arquivo=%s (%d bytes)", nome_arquivo, len(conteudo))

    rows, epoch = ler_planilha(nome_arquivo, conteudo)
    if len(rows) < 2:
        raise IngestFormatError("O arquivo precisa conter cabeçalho e ao menos uma linha.")
    indices = mapear_colunas(rows[0])
    linhas, duplicadas, erros = _preparar_linhas(rows, indices, epoch)
    ignoradas = len(erros)
    logger.info(
        "Etapa 1/3 leitura concluída em %.1fs: %d linhas preparadas, %d duplicadas, %d ignoradas",
        time.perf_counter() - marco_zero, len(linhas), duplicadas, ignoradas,
    )

    # Etapa 2/3: converte todos os CPFs do documento para lattes de uma vez,
    # antes de qualquer inserção no banco.
    cpfs = list(dict.fromkeys(cpf for _, _, cpf, _, _, _ in linhas))
    logger.info("Etapa 2/3 identificação iniciada: %d CPFs distintos", len(cpfs))
    cache_api: dict[str, tuple[str | None, str | None, str | None]] = {}
    marco_identificacao = time.perf_counter()
    with httpx.Client(timeout=TIMEOUT_API_SEGUNDOS) as client:
        for posicao, cpf in enumerate(cpfs, start=1):
            try:
                cache_api[cpf] = consultar_pesquisador(client, cpf)
            except ExternalLookupError:
                # Serviço externo fora do ar (ou CPF não encontrado):
                # não aborta o ingest; o pesquisador fica pendente
                # e a linha é inserida normalmente.
                cache_api[cpf] = (None, None, None)
                erros.append(
                    f"CPF {cpf}: não foi possível consultar os serviços "
                    "externos de identificação; pesquisador mantido como pendente."
                )
            if posicao % 50 == 0 or posicao == len(cpfs):
                logger.info(
                    "Etapa 2/3 identificação: %d/%d CPFs (%.1fs)",
                    posicao, len(cpfs), time.perf_counter() - marco_identificacao,
                )
    logger.info(
        "Etapa 2/3 identificação concluída em %.1fs",
        time.perf_counter() - marco_identificacao,
    )

    contadores = {
        "projetos_criados": 0,
        "bolsas_criadas": 0,
        "pesquisadores_criados": 0,
        "pesquisadores_atualizados": 0,
        "pesquisadores_pendentes": 0,
        "palavras_chave_criadas": 0,
        "areas_criadas": 0,
    }
    lattes_processados: set[str] = set()
    periodos_pesquisadores: dict[str, list[tuple[object, object]]] = {}

    marco_persistencia = time.perf_counter()
    logger.info("Etapa 3/3 persistência iniciada: %d linhas", len(linhas))
    try:
        for posicao, (numero, row, cpf, inicio, saida, termino) in enumerate(linhas, start=1):
            titulo = texto_linha(row, indices, "titulo do projeto")
            resumo = texto_linha(row, indices, "resumo do projeto")
            grande = texto_linha(row, indices, "grande area")
            area_nome = texto_linha(row, indices, "area")
            subarea = texto_linha(row, indices, "subarea")
            instituicao_nome = texto_linha(row, indices, "instituicao")
            instituicao_cep = texto_linha(row, indices, "cep instituicao")
            sigla = texto_linha(row, indices, "sigla instituicao")
            unidade_nome = texto_linha(row, indices, "unidade")
            unidade_cep = texto_linha(row, indices, "cep unidade")
            departamento_nome = texto_linha(row, indices, "departamento")
            departamento_cep = texto_linha(row, indices, "cep departamento")
            modalidade = texto_linha(row, indices, "modalidade")
            curso = texto_linha(row, indices, "nome curso")

            if inicio is not None:
                lattes = cache_api[cpf][0] if cpf in cache_api and cache_api[cpf][0] else None
                # Usa lattes como chave para verificação de sobreposição no banco
                # Se não há lattes, usa o CPF como fallback (pesquisador não identificado externamente)
                chave_pesquisador = lattes or f"cpf:{cpf}"
                if chave_pesquisador not in periodos_pesquisadores:
                    if lattes:
                        existentes = db.execute(
                            select(Bolsa.quando_iniciou, Bolsa.quando_terminou)
                            .join(Pesquisador, Pesquisador.id == Bolsa.pesquisador_id)
                            .where(Pesquisador.lattes == lattes)
                        )
                        periodos_pesquisadores[chave_pesquisador] = list(existentes)
                    else:
                        # Sem lattes: não há como consultar o banco por CPF (não existe mais)
                        # Considera que não há bolsas existentes para este pesquisador
                        periodos_pesquisadores[chave_pesquisador] = []
                if any(
                    _periodos_se_sobrepoem(inicio, termino, inicio_existente, fim_existente)
                    for inicio_existente, fim_existente in periodos_pesquisadores[chave_pesquisador]
                ):
                    # Conflito com bolsa já existente: ignora só esta
                    # linha (sem inserção) e segue com as demais.
                    erros.append(
                        f"Linha {numero}: o pesquisador ({'lattes=' + lattes if lattes else 'cpf=' + cpf}) já possui uma bolsa ativa "
                        "no período informado."
                    )
                    ignoradas += 1
                    continue
                periodos_pesquisadores[chave_pesquisador].append((inicio, termino))

            pesquisador, criado = salvar_pesquisador(db, cpf, cache_api[cpf])
            # Usa lattes para controle de pesquisadores processados (ou CPF se não há lattes)
            chave_proc = lattes or f"cpf:{cpf}"
            if chave_proc not in lattes_processados:
                contadores[
                    "pesquisadores_criados" if criado else "pesquisadores_atualizados"
                ] += 1
                if pesquisador.status == PesquisadorStatus.PENDENTE:
                    contadores["pesquisadores_pendentes"] += 1
                lattes_processados.add(chave_proc)

            grande_obj, nova = _obter_area(
                db, grande, AreaConhecimentoTipo.GRANDE_AREA, None
            )
            contadores["areas_criadas"] += int(nova)
            area_obj, nova = (
                _obter_area(db, area_nome, AreaConhecimentoTipo.AREA, grande_obj)
                if grande_obj is not None
                else (None, False)
            )
            contadores["areas_criadas"] += int(nova)
            if area_obj is not None and subarea:
                _, nova = _obter_area(
                    db, subarea, AreaConhecimentoTipo.SUBAREA, area_obj
                )
                contadores["areas_criadas"] += int(nova)

            instituicao = _obter_instituicao(
                db, instituicao_nome, instituicao_cep, sigla
            )
            departamento = _obter_departamento(
                db,
                departamento_nome,
                unidade_nome,
                departamento_cep,
                instituicao.id,
                grande_obj.id if grande_obj is not None else None,
            )
            _obter_unidade(db, unidade_nome, unidade_cep, departamento)

            projeto, criado = _obter_projeto(db, titulo, resumo, grande, subarea)
            contadores["projetos_criados"] += int(criado)
            contadores["palavras_chave_criadas"] += _adicionar_palavras_chave(
                db, row, indices, projeto
            )

            db.add(
                Bolsa(
                    quando_iniciou=inicio,
                    data_saida_pesquisador=saida,
                    quando_terminou=termino,
                    modalidade=modalidade,
                    nome_curso=curso,
                    projeto_id=projeto.id,
                    instituicao_id=instituicao.id,
                    pesquisador_id=pesquisador.id,
                )
            )
            db.flush()
            contadores["bolsas_criadas"] += 1
            if posicao % 500 == 0:
                logger.info(
                    "Etapa 3/3 persistência: %d/%d linhas (%.1fs)",
                    posicao, len(linhas), time.perf_counter() - marco_persistencia,
                )
        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info(
        "Ingestão concluída em %.1fs: %d processadas, %d duplicadas, %d ignoradas, %d bolsas, %d pendentes",
        time.perf_counter() - marco_zero, contadores["bolsas_criadas"],
        duplicadas, ignoradas, contadores["bolsas_criadas"],
        contadores["pesquisadores_pendentes"],
    )
    return IngestResponse(
        linhas_processadas=contadores["bolsas_criadas"],
        linhas_duplicadas=duplicadas,
        linhas_ignoradas=ignoradas,
        erros=erros,
        **contadores,
    )
