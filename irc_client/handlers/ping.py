from irc_client import client

@client.on(b'PING')
async def on_ping(connection, *params, prefix = None):
    client.send(b'PONG')