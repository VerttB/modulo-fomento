class ApplicationError(Exception):
    """Erro de domínio que pode ser convertido em uma resposta HTTP."""

    status_code = 400


class ResourceNotFoundError(ApplicationError):
    status_code = 404


class DomainValidationError(ApplicationError):
    status_code = 422


class IngestFormatError(ApplicationError):
    status_code = 422


class ExternalLookupError(ApplicationError):
    status_code = 502
