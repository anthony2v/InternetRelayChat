import asyncio
from asyncio.coroutines import iscoroutinefunction
from .connections import Connection
from .logger import logger
from .parser import parse_message
from typing import Callable, List, Optional


class MessageListener:
    """
    Allows binding callbacks to specific command / reply
    strings, and even specific connections.

    Inspired by the syntax of popular python frameworks
    like Flash (e.x @app.route(...) decorator), Celery (e.x @app.task decorator)
    and Javascript's on, off, and once Event functions.
    """

    def __init__(self):
        self.general_message_handlers = {}  # Manages message handlers from any connection
        # Manages message handlers only for a specific connection
        self.specific_message_handlers = {}

    # replaces `command`
    def on(self, msg, from_=None) -> Callable[[Connection, List[bytes], Optional[bytes]], None]:
        """Bind a callback to a specific message type."""
        def _decorator(func):
            if not iscoroutinefunction(func):
                logger.error(
                    'attempted to bind non-coroutine func %s to msg %s', func, msg)
                return func

            logger.debug('binding msg %s to %s', msg, func)
            if from_ is None:
                self.general_message_handlers[msg] = func
            else:
                self.specific_message_handlers[(msg, from_)] = func
            return func
        return _decorator

    def off(self, msg, func, from_=None) -> None:
        """Unbind a callback for a specific message type."""
        if from_ is None:
            self.general_message_handlers.pop(msg, None)
        else:
            self.specific_message_handlers.pop((msg, from_), None)

    def once(self, msg, from_=None) -> Callable[[Connection, List[bytes], Optional[bytes]], None]:
        """Bind a callback for a specific message type, and then
        unbind after one message has been processed."""
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
        """Used to parse a received message and pass it to any bound callbacks."""
        logger.debug("received message %s from %s", message, connection)
        cmd, prefix, params = parse_message(message)

        general_func = self.general_message_handlers.get(cmd)
        specific_func = self.specific_message_handlers.get((cmd, connection))

        bound_funcs = []
        if general_func:
            bound_funcs.append(general_func)
        if specific_func:
            bound_funcs.append(specific_func)

        if not bound_funcs:
            logger.warning("received unknown message type %s", cmd)
            return

        futures = [
            f(connection, *params, prefix=prefix)
            for f in bound_funcs
        ]
        await asyncio.gather(*futures)
