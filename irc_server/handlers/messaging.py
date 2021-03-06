from irc_server import server
from irc_core.replies import ERR_NOTEXTTOSEND


@server.on(b'PRIVMSG')
async def relay_private_messages(connection, receivers, msg=None, prefix=None):
    if not connection.nickname or not connection.username:
        return

    if not msg:
        return server.send_to(connection, ERR_NOTEXTTOSEND, b"No text to send")

    receivers = receivers.split(b',')

    if b'#general' in receivers:
        server.send(b'PRIVMSG', b'#general', msg,
                    prefix=connection.nickname, exclude=connection)
