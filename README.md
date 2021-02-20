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
