import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.exceptions import ApplicationError
from src.routes import router

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app = FastAPI(
    title="Módulo de Fomento",
    version="1.0.0",
    description="API de gerenciamento de projetos e bolsas de fomento.",
)

app.include_router(router, prefix="/api/v1")


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, error: ApplicationError):
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": str(error)},
    )


@app.get("/", tags=["Saúde"])
@app.get("/health", tags=["Saúde"])
def health_check() -> dict[str, str]:
    """Confirma que a API está disponível sem consultar o banco."""
    return {"status": "ok"}
