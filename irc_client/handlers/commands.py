from irc_client import client
from irc_core import logger
from irc_core.replies import *


@client.on('PING')
async def on_ping(connection, *params, prefix=None):
    """Responds to a PING with a PONG"""
    client.send('PONG')

@client.on('NICK')
async def on_nick(connection, nick, prefix=None):
    if prefix == client.nickname:
        client.nickname = nick
    else:
        client.add_msg(prefix, "*changed their nickname to %s*" % nick)


@client.on('PRIVMSG')
async def receive_message(connection, receivers, msg, prefix=None):
    """Displays received messages in the View"""
    client.add_msg(prefix, msg)


@client.on('QUIT')
async def client_quit(connection, msg, prefix=None):
    """Displays a message when a user QUITs the chat"""
    client.add_msg(prefix, "*left the chat: %s*" % msg)


@client.on('JOIN')
async def client_join(connection, channel, prefix=None):
    """Displays a message when a user JOINs the chat.

    Begins listening for a NAMES reply, if the message was
    an echo of our own JOIN.
    """
    client.add_msg(channel, "%s has joined the chat!" % prefix)
    if prefix == client.nickname:
        listen_for_names()


def listen_for_names():
    """Prepares to receive and process a NAMES reply (also replies from JOIN)"""
    logger.info("Listening for names response")

    names = []

    @client.on(RPL_NAMEREPLY)
    async def receive_names(connection, channel, new_names, prefix=None):
        names.extend(new_names.split(' '))

    @client.once(RPL_ENDOFNAMES)
    async def end_of_names(connection, channel, prefix=None):
        # Deregister RPL_NAMERPLY callback
        client.off(RPL_NAMEREPLY, receive_names)

        client.add_msg(channel, "Members: ")
        for name in names:
            client.add_msg(channel, "    " + name)
