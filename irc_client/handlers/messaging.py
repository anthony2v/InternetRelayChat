from irc_client import client


@client.on('PRIVMSG')
async def receive_message(connection, receivers, msg, prefix=None):
    client.add_msg(prefix, msg)


@client.on('QUIT')
async def client_quit(connection, msg, prefix=None):
    client.add_msg(prefix, "has left the chat: %s" % msg)
