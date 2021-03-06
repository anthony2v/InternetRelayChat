import asyncio
from asyncio.coroutines import iscoroutinefunction
from .connections import Connection
from .logger import logger
from functools import partial
from typing import Callable, List, Optional


class MessageListener:
    def __init__(self):
        self.general_message_handlers = {}
        self.specific_message_handlers = {}
    
    def notify_message(self, connection: Connection, msg: bytes) -> None:
        """Used to parse a received message and pass it to any bound callbacks."""
        pass

    def on(self, msg, from_ = None) -> Callable[[Connection, List[bytes], Optional[bytes]], None]: # replaces `command`
        """Bind a callback to a specific message type."""
        if type(msg) == str:
            msg = msg.encode()
        def _decorator(func):
            if not iscoroutinefunction(func):
                logger.error('attempted to bind not coroutine func %s to msg %s', func, msg)
                return func

            logger.info('binding msg %s to %s', msg, func)
            if from_ is None:
                self.general_message_handlers[msg] = func
            else:
                self.specific_message_handlers[(msg, from_)] = func
            return func
        return _decorator

    def off(self, msg, func, from_ = None) -> None:
        """Unbind a callback for a specific message type."""
        if from_ is None:
            self.general_message_handlers.pop(msg, None)
        else:
            self.specific_message_handlers.pop((msg, from_), None)

    def once(self, msg, from_ = None) -> Callable[[Connection, List[bytes], Optional[bytes]], None]:
        """Bind a callback for a specific message type, and then unbind after one message has been processed."""
        if type(msg) == str:
            msg = msg.encode()
        def _decorator(func):
            def wrapper(*args, **kwargs):
                self.off(msg, wrapper, from_)
                return func(*args, **kwargs)
            if from_ is None:
                self.general_message_handlers[msg] = wrapper
            else:
                self.specific_message_handlers[(msg, from_)] = wrapper
            return wrapper
        return _decorator
    
    async def handle_message(self, connection, message):
        logger.info("MessageHandler: received message %s from %s", message, connection)
        cmd, prefix, params = self._parse_message(message)

        general_func = self.general_message_handlers.get(cmd)
        specific_func = self.specific_message_handlers.get((cmd, connection))
        
        bound_funcs = []
        if general_func:
            bound_funcs.append(general_func)
        if specific_func:
            bound_funcs.append(specific_func)

        if not bound_funcs:
            logger.warning("MessageHandler: received unknown message type %s", cmd)
            return
        
        futures = [
            f(connection, *params, prefix = prefix)
            for f in bound_funcs
        ]
        await asyncio.gather(*futures)

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