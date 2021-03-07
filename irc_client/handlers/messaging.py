from irc_client import client
from irc_core import logger
from irc_core.replies import *


@client.on('PRIVMSG')
async def receive_message(connection, receivers, msg, prefix=None):
    client.add_msg(prefix, msg)


@client.on('QUIT')
async def client_quit(connection, msg, prefix=None):
    client.add_msg(prefix, "has left the chat: %s" % msg)


@client.on('JOIN')
async def client_join(connection, channel, prefix=None):
    client.add_msg(channel, "%s has joined the chat." % prefix)
    if prefix == client.nickname:
        listen_for_names()


def listen_for_names():
    logger.info("Listening for names response.")

    names = []    

    @client.on(RPL_NAMEREPLY)
    async def receive_names(connection, channel, new_names, prefix=None):
        names.extend(new_names.split(' '))

    @client.once(RPL_ENDOFNAMES)
    async def end_of_names(connection, channel, prefix=None):
        client.off(RPL_NAMEREPLY, receive_names)
        client.add_msg(channel, "Members: ")
        for name in names:
            client.add_msg(channel, name)