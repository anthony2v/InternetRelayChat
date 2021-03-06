from irc_core.connections import Connection
from irc_server import server
from irc_core.replies import ERR_NICKCOLLISION


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
async def set_user_info(connection: Connection, username, host_name, server_name, real_name, prefix=None):
    connection.username = username
    connection.real_name = real_name
    connection.host = host_name

@server.on(b'NICK')
async def set_nickname(connection, nickname, prefix=None):
    # TODO Check for nick name collisions

    previous_nickname = connection.nickname

    lowercase_nickname = nickname_to_lowercase(nickname)
    if lowercase_nickname in registered_nicknames:
        return server.send_to(connection, ERR_NICKCOLLISION, nickname, b'Nickname collision KILL')

    registered_nicknames.add(lowercase_nickname)
    connection.nickname = nickname

    if previous_nickname is not None:
        registered_nicknames.discard(
            nickname_to_lowercase(previous_nickname))
        server.send(b'NICK', nickname, prefix=previous_nickname)


@server.on_disconnect
async def remove_nickname(connection):
    registered_nicknames.discard(connection.nickname)
