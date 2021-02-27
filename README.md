# Design Ideas

## Classes
BaseConnection < UnregisteredConnection
               < RegisteredConnection   < ~ServerConnection~
                                        < ClientConnection


Message  < NumericReply                < ErrorReply      < ErrorNeedMoreParams
                                                         < ErrorPasswordMismatch
                                                           ... etc.
                                       < ReplyYoureOper
                                         ... etc.
         < Command      < NickCommand
                        < UserCommand
                        < JoinCommand
                          ... etc.


## Command Decorator

Handles parsing received commands, and handles replying

```python
import functools
import logging
import asyncio

def parse_message(message):
    return ,,

class ConnectionManager:

    def bind(self, command_name, handler):
        self.bindings[command_name].append(handler)

    def on_message_received(self, connection, message):
        command, prefix, args = parse_message()
        return self.bindings[command](connection, prefix, *args)


def command(name):
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(connection: Connection, prefix, *args) -> Reply:
            logging.info(f'received command from connection {connection}')
            
            try:
                return await func(connection, prefix, *params)
            except ErrorReply as err:
                logging.warning(...)
                return connection.send(err)
            except Exception as exc:
                err = ErrorUnknownError()
                return connerction.send(err)

        connection_manager.bind(name, wrapper)

        return wrapper

    return decorator


@command('NICK')
async def some_command_handler(connection: BaseConnection, prefix, nickname) -> Reply:
    # This doesn't actually happend, just an example of syntax
    replies = await OperCommand(user, password).send_to_all(from_=connection, prefix=prefix)

    connection.send()

    if all(reply.ok for reply in replies):
        return ReplyNicknameConfirmed()
    else:
        raise ReplyNicknameConflict()
```

command decorator:
    - error handling
        - if ErrorReply is raised, then the reply will be sent to the connection
        - uncaught exceptions are logged, and an ErrorReply is sent along the connection
        - 


## Required Messages

- 4.1.2 NICK
- 4.1.3 USER
- 4.1.6 QUIT

- 4.2.5 NAMES

- 4.4.1 PRIVMSG
- 4.4.2 NOTICE ???

- 4.5.1 WHO ???
- 4.5.2 WHOIS ???
- 4.5.3 WHOWAS ???

- 4.6.2 PING
- 4.6.3 PONG

# Required Replies
- ERR_NONICKNAMEGIVEN
- ERR_ERRONEUSNICKNAME
- ERR_NICKNAMEINUSE What is the difference between this and NICKCOLLISION??
- ERR_NICKCOLLISION
- ERR_NOSUCHNICK
- ERR_WASNOSUCHNICK

- ERR_NEEDMOREPARAMS
- ERR_ALREADYREGISTERED

- ERR_NORECIPIENT
- ERR_NOTEXTTOSEND
- ERR_CANNOTSENDTOCHAN

- ERR_NOORIGIN
- ERR_NOSUCHSERVER ???

- ERR_UNKNOWNCOMMAND

- RPL_NAMREPLY
- RPL_ENDOFNAMES

- RPL_WHOREPLY
- RPL_ENDOFWHO

- RPL_WHOISUSER
- RPL_AWAY
- RPL_WHOISIDLE
- RPL_ENDOFWHOIS

- RPL_WHOWASUSER
- RPL_ENDOFWHOWAS



1. Receiving a message must be able to generate multiple replies
2. At least on client side, send a message and then expect multiple replies

```python

mh = MessageHandler()

# Server

@mh.on(b'NAMES')
def names_handler(...):
    for user in registered_users:
        yield NameReply(user...)

    yield EndOfNamesReply()


async def send_ping(nickname):
    mh.send_to(nickname, PING)

    timeout = asyncio.sleep(5)
    
    @server.once(b'PONG', from_=nickname)
    def on_pong(...):
        timeout.cancel()
    
    await timeout
    
    server.disconnect(nickname)


# Client-side
# User types: /names
async def get_names():
    mh.send(NamesMessage())

    names = []
    
    finished = asyncio.Event()

    @mh.on(RPL_NAMEREPLY)
    def on_name_reply(...):
        new_names = params[-1]
        names += new_names.split(b' ')

    @mh.once(RPL_ENDOFNAMES)
    def on_end_of_names(...):
        mh.off(RPL_NAMEREPLY, on_name_reply)
        finished.set()
    
    await finished.wait()
    return names

await get_names()


class MessageListener:

    def notify_message(self, connection: Connection, msg: bytes) -> None:
        """Used to parse a received message and pass it to any bound callbacks."""
        pass

    def on(self, msg) -> Callable[[Connection, List[bytes], Optional[bytes]], None]: # replaces `command`
        """Bind a callback to a specific message type."""
        pass

    def off(self, msg, func) -> None:
        """Unbind a callback for a specific message type."""
        pass

    def once(self, msg) -> Callable[[Connection, List[bytes], Optional[bytes]], None]:
        """Bind a callback for a specific message type, and then unbind after one message has been processed."""
        pass


class Client(MessageListener):

    def send(self, msg: bytes, *params: bytes):
        """Serializes and sends a message to the server"""
        pass


class Server(MessageListener):

    def send(self, msg: bytes, *params: bytes, prefix = None, exclude = None: Connection):
        pass


# Client-side
@client.on('PING')
def on_ping(connection, *params, prefix=None):
    server.send('PONG')

# Server-side
@server.on('PING')
def on_ping(connection, *params, prefix=None):
    connection.send('PING')

@server.on('PRIVMSG')
def on_private_message(connection, *params, prefix=None):
    if prefix is None:
        prefix = connection.nickname
    server.send('PRIVMSG', *params, prefix=prefix, exclude=connection)

```
