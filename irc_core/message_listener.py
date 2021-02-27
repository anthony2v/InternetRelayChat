from .connections import Connection
from .logger import logger
from functools import partial
from typing import Callable, List, Optional


class MessageListener:
    def __init__(self):
        self.cmds = {}
        self.general_message_handlers = {}
        self.specific_message_handlers = {}
    
    def notify_message(self, connection: Connection, msg: bytes) -> None:
        """Used to parse a received message and pass it to any bound callbacks."""
        pass

    def on(self, msg, from_ = None) -> Callable[[Connection, List[bytes], Optional[bytes]], None]: # replaces `command`
        """Bind a callback to a specific message type."""
        pass

    def off(self, msg, func) -> None:
        """Unbind a callback for a specific message type."""
        pass

    def once(self, msg) -> Callable[[Connection, List[bytes], Optional[bytes]], None]:
        """Bind a callback for a specific message type, and then unbind after one message has been processed."""
        pass

    def command(self, cmd):
        if type(cmd) == str:
            cmd = cmd.encode()
        def _decorator(func):
            self.cmds[cmd] = func
            return func
        return _decorator
    
    async def handle_message(self, connection, message):
        logger.info("MessageHandler: received message %s", message)
        cmd, prefix, params = self._parse_message(message)
        if cmd not in self.cmds:
            logger.info("MessageHandler: received unknown message type %s", cmd)
            return

        valid = True
        if cmd in self.validators:
            valid = await self.validators[cmd](params, prefix = prefix)

        if not valid:
            # TODO return reply to client
            raise ValueError()

        send = partial(self.send, connection)
        await self.cmds[cmd](send, *params, prefix = prefix)
        pass

    def _parse_message(self, message):
        message = message.replace(b"\r\n", b"")

        prefix = None
        if message.startswith(b':'):
            first_space = message.index(b' ')
            prefix = message[1:first_space]
            message = message[first_space+1:].lstrip(b' ')

        trailing_start = message.find(b':')
        trailing = []
        if trailing_start != -1:   
            trailing.append(message[trailing_start+1:])
            message = message[:trailing_start]

        cmd, *params = message.split(b' ')
        params = list(p for p in params if p)

        params += trailing
        return cmd, prefix, params

    def send(self, connection, message, **kwargs):
        pass