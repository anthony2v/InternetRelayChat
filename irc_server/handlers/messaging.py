from irc_server import server
from irc_core.replies import ERR_NOTEXTTOSEND
from irc_core import logger
from .register import channel_membership


@server.on('PRIVMSG')
async def relay_private_messages(connection, receivers, msg=None, prefix=None):
    """Handles forwarding messages to the appropriate clients when a PRIVMSG is
    received.
    
    NOTE: Currently only supports sending to channels.
    """
    if not connection.registered:
        return # Ignore PRIVMSG from clients who are not yet fully registered

    if not msg:
        return server.send_to(connection, ERR_NOTEXTTOSEND, "No text to send")

    receivers = receivers.split(',')

    for receiver in receivers:
        if receiver[0] in {'#', '&'}:
            for conn in channel_membership[receiver] - {connection}:
                server.send_to(conn, 'PRIVMSG', receiver, msg,
                    prefix=connection.nickname)
