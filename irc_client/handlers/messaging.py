from irc_client import client


@client.on(b'PRIVMSG')
async def receive_message(connection, receivers, msg, prefix=None):
    client.add_msg(prefix.decode('ascii'), msg.decode('ascii'))


@client.on(b'QUIT')
async def client_quit(connection, msg, prefix=None):
    msg = msg.decode('ascii')
    prefix = prefix.decode('ascii')
    client.add_msg(prefix, "has left the chat: %s" % msg)
