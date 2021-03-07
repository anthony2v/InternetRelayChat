from irc_client import client


@client.on('PING')
async def on_ping(connection, *params, prefix=None):
    client.send('PONG')
