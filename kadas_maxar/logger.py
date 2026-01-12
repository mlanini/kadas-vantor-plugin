import logging
import os


def get_logger():
    """Return a module-level logger writing to the path specified by
    KADAS_MAXAR_LOG env var or default ~/.kadas/maxar.log.
    Ensures the directory exists and avoids adding duplicate handlers.
    """
    log_path = os.environ.get('KADAS_MAXAR_LOG', os.path.expanduser('~/.kadas/maxar.log'))
    log_dir = os.path.dirname(log_path)
    try:
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    except Exception:
        # best-effort: if we can't create dir, return a silent logger
        logger = logging.getLogger('kadas_maxar')
        logger.setLevel(logging.INFO)
        return logger

    logger = logging.getLogger('kadas_maxar')
    # If handlers already configured, ensure we have a file handler pointing to desired path
    try:
        desired = os.path.abspath(log_path)
        needs_handler = True
        for h in list(logger.handlers):
            try:
                base = getattr(h, 'baseFilename', None)
                if base and os.path.abspath(base) == desired:
                    needs_handler = False
                    break
            except Exception:
                continue
        if needs_handler:
            # remove existing file handlers (but keep others)
            for h in list(logger.handlers):
                try:
                    if hasattr(h, 'baseFilename'):
                        logger.removeHandler(h)
                except Exception:
                    pass
            # add new file handler
            try:
                fh = logging.FileHandler(log_path, mode='a', encoding='utf-8')
                fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
                fh.setFormatter(fmt)
                logger.addHandler(fh)
            except Exception:
                pass
        logger.setLevel(logging.INFO)
    except Exception:
        logger.setLevel(logging.INFO)
    return logger
