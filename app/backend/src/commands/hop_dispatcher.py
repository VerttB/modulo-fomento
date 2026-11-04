import logging

from src.core.config import HopDispatcherConfig, settings
from src.services.hop_dispatcher import executar_disparador


if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    executar_disparador(HopDispatcherConfig())
