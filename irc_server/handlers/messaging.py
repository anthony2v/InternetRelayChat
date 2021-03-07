from irc_server import server
from irc_core.replies import ERR_NOTEXTTOSEND
from irc_core import logger
from .register import channel_membership


@server.on('PRIVMSG')
async def relay_private_messages(connection, receivers, msg=None, prefix=None):
    if not connection.nickname or not connection.username:
        return

    if not msg:
        return server.send_to(connection, ERR_NOTEXTTOSEND, "No text to send")

    receivers = receivers.split(',')

    for receiver in receivers:
        if receiver[0] in {'#', '&'}:
            for conn in channel_membership[receiver] - {connection}:
                server.send_to(conn, 'PRIVMSG', receiver, msg,
                    prefix=connection.nickname)
