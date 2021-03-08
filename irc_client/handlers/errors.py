from irc_client import client
from irc_core.replies import *

from irc_core import logger


@client.on(ERR_NICKCOLLISION)
async def on_nick_collision(connection, nick, *params, prefix=None):
    client.add_msg('SYSTEM', "Nickname taken: %s" % nick)
    client.add_msg('SYSTEM', "You have been assigned an anonymous nickname""")
    client.add_msg('SYSTEM', "Type '/NICK ' followed by your nickname to choose a new one""")


@client.on(ERR_NICKNAMEINUSE)
async def on_nick_in_use(connection, nick, *params, prefix=None):
    client.add_msg('SYSTEM', "Unable to set nickname. Nickname taken: %s" % nick)
    client.add_msg(
        'SYSTEM', "Type '/NICK ' followed by a nickname to try again""")


@client.on(ERR_ERRONEUSNICKNAME)
async def on_nick_error(connection, nick, *params, prefix=None):
    client.add_msg(
        'SYSTEM', "Unable to set nickname. Invalid nickname: %s" % nick)
    client.add_msg(
        'SYSTEM', "Nicknames must respect the following rules:")
    client.add_msg(
        'SYSTEM', "   1. Between 1 and 9 characters long")
    client.add_msg(
        'SYSTEM', "   2. Start with a letter")
    client.add_msg(
        'SYSTEM', R"   3. Contain only letters, numbers, and the following special characters: -[]\|`^{}")
    client.add_msg(
        'SYSTEM', "Type '/NICK ' followed by a nickname to try again""")


@client.on(ERR_NEEDMOREPARAMS)
async def on_need_more_params(connection, cmd, msg, prefix=None):
    client.add_msg('SYSTEM', "Error in cmd %s: %s" % (cmd, msg))


@client.on(ERR_ALREADYREGISTERED)
async def on_already_registered(connection, msg, prefix=None):
    client.add_msg('SYSTEM', "Error: %s" % msg)
