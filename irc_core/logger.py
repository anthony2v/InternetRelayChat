import logging

"""TODO fix logger info printing"""
logger = logging.getLogger("irc_core")
logger.setLevel(logging.INFO)
logger.info = print
logger.error = print
logger.warning = print