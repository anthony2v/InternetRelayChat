from irc_core.logger import logger, handler
from .client import Client

client = Client()

# Logging to stdout breaks ncurses UI
logger.removeHandler(handler)
