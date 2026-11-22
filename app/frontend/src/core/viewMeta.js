/**
 * Textos de apoio do cabeçalho por seção.
 *
 * O <h1> continua sendo o nome da seção (alinhado ao menu e ao breadcrumb,
 * o que preserva a leitura por leitores de tela). A frase narrativa abaixo
 * dele assume o tom editorial do protótipo do Observatório.
 */
export const viewSubtitles = {
  panorama: "Uma trajetória de apoio à formação científica na Bahia.",
  indicadores: "Números que mostram como o fomento se distribui entre modalidades, instituições e territórios.",
  territorios: "Onde a formação científica acontece, território por território.",
  bolsas: "Quem recebeu apoio e em que etapa da formação.",
  pesquisadores: "As pessoas por trás dos registros de bolsas.",
  projetos: "O que é financiado e como o conhecimento se organiza.",
  instituicoes: "A rede de instituições que sustenta a pesquisa baiana.",
  maria: "Pergunte em linguagem natural sobre bolsistas, projetos e territórios.",
  ingestoes: "Acompanhe a entrada de dados no observatório.",
};

export const DEFAULT_SUBTITLE = "Fomento à formação científica nos territórios da Bahia";

export const subtitleFor = (view) => viewSubtitles[view] || DEFAULT_SUBTITLE;
