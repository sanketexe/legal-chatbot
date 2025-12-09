import logging
import sys


def configure_logging(level=logging.INFO):
    """Configure root logger for the project.

    This sets a StreamHandler with UTF-8 encoding where supported and a simple
    formatter. Calling multiple times is safe (it avoids adding duplicate
    handlers).
    """
    root = logging.getLogger()
    if root.handlers:
        # already configured
        return

    root.setLevel(level)

    handler = logging.StreamHandler(stream=sys.stdout)
    try:
        # some Python builds support setting encoding on the handler
        handler.stream.reconfigure(encoding='utf-8')
    except Exception:
        # ignore if not supported
        pass

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    root.addHandler(handler)


def get_logger(name: str):
    """Return a configured logger for the given module name."""
    configure_logging()
    return logging.getLogger(name)
