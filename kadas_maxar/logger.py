import logging
import os
import sys
import traceback

LOG_LEVELS = {
    "STANDARD": logging.INFO,
    "DEBUG": logging.DEBUG,
    "ERRORS": logging.ERROR,
    "WARNING": logging.WARNING,
    "CRITICAL": logging.CRITICAL,
}


class CriticalFileHandler(logging.FileHandler):
    """
    FileHandler che scrive stacktrace completo per errori CRITICAL.
    """

    def emit(self, record):
        if record.levelno >= logging.CRITICAL and record.exc_info:
            record.msg = f"{record.msg}\n{''.join(traceback.format_exception(*record.exc_info))}"
        super().emit(record)


def get_logger(level="DEBUG", log_to_console=False):
    """
    Restituisce un logger configurato per il plugin.
    - Scrive su file (percorso da KADAS_MAXAR_LOG o ~/.kadas/maxar.log)
    - Permette diversi livelli di dettaglio ('STANDARD', 'DEBUG', 'ERRORS', 'WARNING', 'CRITICAL')
    - Logga stacktrace completo per errori CRITICAL
    - Opzionalmente logga anche su console (utile per debug)
    """
    log_path = os.environ.get('KADAS_MAXAR_LOG', os.path.expanduser('~/.kadas/maxar.log'))
    log_dir = os.path.dirname(log_path)
    try:
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    except Exception:
        pass

    logger = logging.getLogger('kadas_maxar')
    logger.propagate = False  # Evita doppio logging se root logger è configurato

    # Rimuovi eventuali handler duplicati
    for h in list(logger.handlers):
        logger.removeHandler(h)

    # File handler con stacktrace per CRITICAL
    try:
        fh = CriticalFileHandler(log_path, mode='a', encoding='utf-8')
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass

    # Console handler opzionale
    if log_to_console:
        ch = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    logger.debug(f"Logger inizializzato con livello {level.upper()} (file: {log_path})")
    return logger
