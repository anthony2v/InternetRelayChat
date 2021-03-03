from irc_client import client

@client.on(b'PING')
def on_ping(connection, *params, prefix = None):
    client.send(b'PONG')