import http.client
import io
import json
import socket
import tarfile
from pathlib import Path
from uuid import UUID

from src.core.config import HopDispatcherConfig


class DockerHopError(RuntimeError):
    pass


class _UnixConnection(http.client.HTTPConnection):
    def __init__(self, path: Path, timeout):
        super().__init__("localhost", timeout=timeout)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(self.path))


class HopDocker:
    """Cria uma execução temporária do Hop usando a API local do Docker."""

    def __init__(self, config: HopDispatcherConfig):
        self.config = config

    def _request(self, method, path, body=None, content_type="application/json", timeout=30):
        connection = _UnixConnection(self.config.hop_docker_socket, timeout)
        try:
            connection.request(method, "/v1.43" + path, body=body, headers={"Content-Type": content_type})
            response = connection.getresponse()
            content = response.read()
            return response.status, content
        finally:
            connection.close()

    def _inspect(self, name):
        status, body = self._request("GET", f"/containers/{name}/json")
        if status == 404:
            return None
        if status != 200:
            raise DockerHopError(f"Inspeção do container falhou ({status}).")
        return json.loads(body)

    def _network(self):
        current = self._inspect(socket.gethostname())
        if not current:
            raise DockerHopError("Não foi possível identificar a rede do disparador.")
        networks = list(current["NetworkSettings"]["Networks"])
        if len(networks) != 1:
            raise DockerHopError("O disparador deve pertencer a uma única rede Docker.")
        return networks[0]

    def _project_archive(self):
        buffer = io.BytesIO()
        files = (
            "project-config.json",
            "metadata/workflow-run-configuration/local.json",
            "workflows/retomar_ingestao.hwf",
        )
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            for folder in ("project", "project/metadata", "project/metadata/workflow-run-configuration", "project/workflows"):
                entry = tarfile.TarInfo(folder)
                entry.type = tarfile.DIRTYPE
                entry.mode = 0o755
                archive.addfile(entry)
            for relative in files:
                archive.add(self.config.hop_project_path / relative, arcname=f"project/{relative}")
        return buffer.getvalue()

    def executar(self, ingestao_id: UUID) -> int:
        name = f"modulo-fomento-hop-{ingestao_id}"
        existing = self._inspect(name)
        if existing:
            labels = existing.get("Config", {}).get("Labels") or {}
            if labels.get("modulo-fomento.ingestao") != str(ingestao_id):
                raise DockerHopError("Nome de container ocupado por outro serviço.")
            state = existing["State"]["Status"]
            if state == "running":
                return self._wait(name)
            status, _ = self._request("DELETE", f"/containers/{name}?force=true")
            if status not in (204, 404):
                raise DockerHopError(f"Remoção do container temporário falhou ({status}).")

        config = {
            "Image": self.config.hop_job_image,
            "Labels": {"modulo-fomento.ingestao": str(ingestao_id)},
            "Env": [
                "HOP_PROJECT_FOLDER=/tmp/project",
                "HOP_PROJECT_NAME=modulo_fomento",
                "HOP_FILE_PATH=/tmp/project/workflows/retomar_ingestao.hwf",
                "HOP_RUN_CONFIG=local",
                f"HOP_INGEST_API_URL={self.config.hop_ingest_api_url}",
                f"HOP_INGESTAO_ID={ingestao_id}",
            ],
            "HostConfig": {"NetworkMode": self._network(), "AutoRemove": True},
        }
        status, body = self._request("POST", f"/containers/create?name={name}", json.dumps(config))
        if status != 201:
            raise DockerHopError(f"Criação do container Hop falhou ({status}).")
        identifier = json.loads(body)["Id"]
        try:
            status, _ = self._request(
                "PUT", f"/containers/{identifier}/archive?path=/tmp",
                self._project_archive(), "application/x-tar",
            )
            if status != 200:
                raise DockerHopError(f"Cópia do projeto Hop falhou ({status}).")
            status, _ = self._request("POST", f"/containers/{identifier}/start")
            if status not in (204, 304):
                raise DockerHopError(f"Inicialização do Hop falhou ({status}).")
        except Exception:
            self._request("DELETE", f"/containers/{identifier}?force=true")
            raise
        return self._wait(identifier)

    def _wait(self, identifier):
        status, body = self._request(
            "POST", f"/containers/{identifier}/wait?condition=not-running", timeout=None
        )
        if status != 200:
            raise DockerHopError(f"Acompanhamento do Hop falhou ({status}).")
        result = json.loads(body)
        if result.get("Error"):
            raise DockerHopError("O Docker informou falha ao aguardar o Hop.")
        return result["StatusCode"]
