import logging

from .db import init_db
from .security.csrf import init_csrf
from .security.logging import RedactingFilter


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def init_extensions(app):
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    logging.getLogger().addFilter(RedactingFilter())
    init_db(app)
    init_csrf(app)
