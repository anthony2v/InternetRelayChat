from time import time
from typing import DefaultDict
from irc_server import server

from irc_core.replies import *
from irc_core.connections import Connection

from irc_core import logger


registered_nicknames = set()
channel_membership = DefaultDict(set)
number_of_anons = -1


def random_nickname():
    global number_of_anons
    number_of_anons += 1
    return f"anon{number_of_anons}"


def nickname_to_lowercase(nickname):
    nickname = nickname.lower()
    nickname = nickname.translate({
        '[': '{',
        ']': '}',
        '\\': '|',
    })

    return nickname


@server.on('USER')
async def set_user_info(connection: Connection, *params, prefix=None):
    if connection.registered:
        logger.error('ERR_ALREADYREGISTERED %s params=%s connection=%s',
                     'USER', params, connection)
        return server.send_to(connection, ERR_ALREADYREGISTERED, 'You may not reregister')

    if len(params) != 4:
        logger.error('ERR_NEEDMOREPARAMS %s params=%s connection=%s',
                     'USER', params, connection)
        return server.send_to(connection, ERR_NEEDMOREPARAMS, 'USER', 'Not enough parameters')

    username, host_name, server_name, real_name = params
    connection.username = username
    connection.real_name = real_name
    connection.host = host_name
    if connection.nickname is None:
        connection.nickname = random_nickname()
        registered_nicknames.add(connection.nickname)
    connection.registered = True
    add_to_channel(connection, "#global")


@server.on('NICK')
async def set_nickname(connection, *params, prefix=None):
    # TODO Check for nick name collisions

    if not params:
        logger.error('ERR_NONICKNAMEGIVEN %s params=%s connection=%s',
                     'NICK', params, connection)
        return server.send_to(connection, ERR_NONICKNAMEGIVEN, 'No nickname given')

    nickname = params[0]

    previous_nickname = connection.nickname

    lowercase_nickname = nickname_to_lowercase(nickname)
    if lowercase_nickname in registered_nicknames:
        logger.error('ERR_NICKCOLLISION %s params=%s connection=%s',
                     'NICK', params, connection)
        return server.send_to(connection, ERR_NICKCOLLISION, nickname, 'Nickname collision KILL')

    registered_nicknames.add(lowercase_nickname)
    connection.nickname = nickname

    if previous_nickname is not None:
        registered_nicknames.discard(
            nickname_to_lowercase(previous_nickname))
        server.send('NICK', nickname, prefix=previous_nickname)


@server.on('QUIT')
async def on_quit(connection, msg=None, prefix=None):
    if msg is None:
        msg = connection.nickname
    
    await server.remove_connection(connection, msg=msg)


@server.on_disconnect
async def remove_nickname(connection):
    logger.info("Deregistering %s", connection)
    registered_nicknames.discard(nickname_to_lowercase(connection.nickname))
    for members in channel_membership.values():
        members.discard(connection)


def add_to_channel(connection, channel_name):
    logger.info("Adding %s to %s", connection, channel_name)
    channel_membership[channel_name].add(connection)
    for conn in channel_membership[channel_name]:
        server.send_to(conn, 'JOIN', channel_name, prefix=connection.nickname)

    send_names_to_connection(connection, channel_name)


def send_names_to_connection(connection, channel_name):
    logger.info("Sending members list to %s", connection)
    members = list(conn.nickname for conn in channel_membership[channel_name] if conn.nickname is not None)
    batches = []
    batch = []
    batch_length = 0
    batch_size = 506 - len(channel_name) - 1
    for member in members:
        if batch_length + len(member) + 1 >= batch_size:
            batches.append(batch)
            batch = []
            batch_length = 0
        batch.append(member)
        batch_length += len(member) + 1
    batches.append(batch)
    
    for batch in batches:
        server.send_to(connection, RPL_NAMEREPLY, channel_name, ' '.join(batch))
    
    server.send_to(connection, RPL_ENDOFNAMES, channel_name)
        