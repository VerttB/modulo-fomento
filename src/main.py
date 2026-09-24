from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.exceptions import ApplicationError
from src.routes import router

app = FastAPI(
    title="Módulo de Fomento",
    version="0.1.0",
    description="API de gerenciamento de projetos e bolsas de fomento.",
)

app.include_router(router, prefix="/api")


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, error: ApplicationError):
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": str(error)},
    )


@app.get("/", tags=["Saúde"])
def health_check() -> dict[str, str]:
    """Confirma que a API está disponível sem consultar o banco."""
    return {"status": "ok"}
