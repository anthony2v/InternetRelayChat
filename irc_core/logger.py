import logging
import sys


logger = logging.getLogger("irc_core")

handler = logging.StreamHandler(sys.stdout)
handler.flush = sys.stdout.flush

logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
