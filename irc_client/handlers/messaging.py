from irc_client import client

@client.on(b'PRIVMSG')
async def receive_message(connection, receivers, msg, prefix=None):
    client.add_msg(prefix.decode('ascii'), msg.decode('ascii'))
