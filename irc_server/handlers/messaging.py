from irc_server import server
from irc_core.replies import ERR_NOTEXTTOSEND


@server.on('PRIVMSG')
async def relay_private_messages(connection, receivers, msg=None, prefix=None):
    if not connection.nickname or not connection.username:
        return

    if not msg:
        return server.send_to(connection, ERR_NOTEXTTOSEND, "No text to send")

    receivers = receivers.split(b',')

    if '#global' in receivers:
        server.send('PRIVMSG', '#global', msg,
                    prefix=connection.nickname, exclude=connection)
