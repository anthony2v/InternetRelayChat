from typing import DefaultDict
from irc_server import server

from irc_core.replies import *
from irc_core.connections import Connection

from irc_core import logger


ALLOWED_IN_NICKNAME = set(R"abcdefghijklmnopqrstuvwxyz0123456789-[]\|`^{}")

# Tracks all registered nicknames
registered_nicknames = set()

# Tracks channel membership (just #global for now)
channel_membership = DefaultDict(set)

# Used to assign anonymous nicknames
number_of_anons = -1


def _random_nickname():
    """generates an anonymous nickname in case of nick collision for
    a user who is not yet registered."""
    global number_of_anons
    number_of_anons += 1
    return f"anon{number_of_anons}"


def assign_random_nickname(connection):
    """assigns a random nickname to a connection"""
    connection.nickname = _random_nickname()
    registered_nicknames.add(connection.nickname)


def nickname_to_lowercase(nickname):
    """converts a nickname to lowercase, respecting
    the rules of IRC"""

    nickname = nickname.lower()
    nickname = nickname.translate({
        '[': '{',
        ']': '}',
        '\\': '|',
    })

    return nickname


def validate_nickname(nickname):
    """Validate that the nickname is acceptable.

    A nickname must have a length between 1 and 9 characters,
    it must start with a letter, and contain only letters,
    numbers and the allowed special characters.
    """
    right_length = 1 <= len(nickname) <= 9
    right_chars = set(nickname).issubset(ALLOWED_IN_NICKNAME)
    return right_length and right_chars and nickname[0].isalpha()


@server.on('USER')
async def set_user_info(connection: Connection, *params, prefix=None):
    """Handles user registration when a USER command is received."""

    if connection.registered:
        logger.error('ERR_ALREADYREGISTERED %s params=%s connection=%s',
                     'USER', params, connection)
        return server.send_to(connection, ERR_ALREADYREGISTERED, 'You may not reregister')

    if len(params) != 4:
        logger.error('ERR_NEEDMOREPARAMS %s params=%s connection=%s',
                     'USER', params, connection)
        return server.send_to(connection, ERR_NEEDMOREPARAMS, 'USER', 'Not enough parameters')

    username, host_name, _, real_name = params
    connection.username = username
    connection.real_name = real_name
    connection.host = host_name

    if connection.nickname is None:
        assign_random_nickname(connection)

    connection.registered = True
    add_to_channel(connection, "#global")


@server.on('NICK')
async def set_nickname(connection, *params, prefix=None):
    """Handles setting the connection's nickname when a NICK command
    is received."""

    logger.info('attempting to set nickname for %s', connection)

    if not params:
        logger.error('ERR_NONICKNAMEGIVEN %s params=%s connection=%s',
                     'NICK', params, connection)
        return server.send_to(connection, ERR_NONICKNAMEGIVEN, 'No nickname given')

    nickname = params[0]

    previous_nickname = connection.nickname

    lowercase_nickname = nickname_to_lowercase(nickname)

    if not validate_nickname(lowercase_nickname):
        logger.error('ERR_ERRONEUSNICKNAME %s params=%s connection=%s',
                     'NICK', params, connection)
        return server.send_to(connection, ERR_ERRONEUSNICKNAME, nickname, 'Erroneus nickname')

    if lowercase_nickname in registered_nicknames:
        if previous_nickname is None:
            logger.error('ERR_NICKCOLLISION %s params=%s connection=%s',
                         'NICK', params, connection)
            return server.send_to(connection, ERR_NICKCOLLISION, nickname, 'Nickname collision KILL')
        else:
            logger.error('ERR_NICKNAMEINUSE %s params=%s connection=%s',
                         'NICK', params, connection)
            return server.send_to(connection, ERR_NICKNAMEINUSE, nickname, 'Nickname is already in use')

    registered_nicknames.add(lowercase_nickname)
    connection.nickname = nickname

    if previous_nickname is not None:
        registered_nicknames.discard(
            nickname_to_lowercase(previous_nickname))
        server.send('NICK', nickname, prefix=previous_nickname)

    logger.info('successfully set nickname for %s (previously %s)',
                connection, previous_nickname)


@server.on('QUIT')
async def on_quit(connection, msg=None, prefix=None):
    """Handles disconnecting a client when a QUIT command is received."""

    logger.info('received quit from %s', connection)

    if msg is None:
        msg = connection.nickname

    await server.remove_connection(connection, msg=msg)


@server.on_disconnect
async def deregister_connection(connection):
    """Removes client from membership lists when the client either
    disconnects with a QUIT or the socket is closed."""

    logger.info("deregistering %s", connection)
    registered_nicknames.discard(nickname_to_lowercase(connection.nickname))
    for members in channel_membership.values():
        members.discard(connection)


def add_to_channel(connection, channel_name):
    """Adds a connection to a channel's member set"""

    logger.info("adding %s to channel %s", connection, channel_name)
    channel_membership[channel_name].add(connection)

    # Notify other users in the channel that a new user has joined
    for conn in channel_membership[channel_name]:
        server.send_to(conn, 'JOIN', channel_name, prefix=connection.nickname)

    # Send the user who joined the list of all users in the channel
    send_names_to_connection(connection, channel_name)


def send_names_to_connection(connection, channel_name):
    """Uses a RPL_NAMEREPLY to send the list of channel members
    to a connection."""

    logger.info("sending members list for channel %s to %s",
                channel_name, connection)

    members = list(
        conn.nickname for conn in channel_membership[channel_name] if conn.nickname is not None)

    # If many clients are part of a channel, then the list of names could
    # exceed the max message length, therefore we must be cabable of sending
    # the names in batches
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
        server.send_to(connection, RPL_NAMEREPLY,
                       channel_name, ' '.join(batch))

    # Notify the client of the end of the list of names
    server.send_to(connection, RPL_ENDOFNAMES, channel_name)
