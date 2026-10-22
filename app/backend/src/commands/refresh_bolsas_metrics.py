from src.core.database import engine
from src.use_cases.v1.reports.bolsas import refresh_bolsas_metrics


def main() -> None:
    refresh_bolsas_metrics(engine)
    print("View materializada de bolsas atualizada.")


if __name__ == "__main__":
    main()
