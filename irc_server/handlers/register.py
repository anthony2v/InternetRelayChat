from irc_server import server

from irc_core.replies import *
from irc_core.connections import Connection

from irc_core import logger


registered_nicknames = set()


def nickname_to_lowercase(nickname):
    nickname = nickname.decode('ascii')
    nickname = nickname.lower()
    nickname = nickname.translate({
        '[': '{',
        ']': '}',
        '\\': '|',
    })

    return nickname.encode('ascii')


@server.on(b'USER')
async def set_user_info(connection: Connection, *params, prefix=None):
    if connection.registered:
        logger.error('ERR_ALREADYREGISTERED %s params=%s connection=%s',
                     'USER', params, connection)
        return server.send_to(connection, ERR_ALREADYREGISTERED, b'You may not reregister')

    if len(params) != 4:
        logger.error('ERR_NEEDMOREPARAMS %s params=%s connection=%s',
                     'USER', params, connection)
        return server.send_to(connection, ERR_NEEDMOREPARAMS, b'USER', b'Not enough parameters')

    username, host_name, server_name, real_name = params
    connection.username = username
    connection.real_name = real_name
    connection.host = host_name
    connection.registered = True


@server.on(b'NICK')
async def set_nickname(connection, *params, prefix=None):
    # TODO Check for nick name collisions

    if not params:
        logger.error('ERR_NONICKNAMEGIVEN %s params=%s connection=%s',
                     'NICK', params, connection)
        return server.send_to(connection, ERR_NONICKNAMEGIVEN, b'No nickname given')

    nickname = params[0]

    previous_nickname = connection.nickname

    lowercase_nickname = nickname_to_lowercase(nickname)
    if lowercase_nickname in registered_nicknames:
        logger.error('ERR_NICKCOLLISION %s params=%s connection=%s',
                     'NICK', params, connection)
        return server.send_to(connection, ERR_NICKCOLLISION, nickname, b'Nickname collision KILL')

    registered_nicknames.add(lowercase_nickname)
    connection.nickname = nickname

    if previous_nickname is not None:
        registered_nicknames.discard(
            nickname_to_lowercase(previous_nickname))
        server.send(b'NICK', nickname, prefix=previous_nickname)


@server.on(b'QUIT')
async def on_quit(connection, msg=None, prefix=None):
    if msg is None:
        msg = connection.nickname
    
    await server.remove_connection(connection, msg=msg)


@server.on_disconnect
async def remove_nickname(connection):
    registered_nicknames.discard(connection.nickname)
