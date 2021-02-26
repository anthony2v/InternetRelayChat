from .logger import logger
from functools import partial

class MessageHandler:
    def __init__(self):
        self.cmds = {}
        self.validators = {}
    
    def command(self, cmd):
        if type(cmd) == str:
            cmd = cmd.encode()
        def _decorator(func):
            self.cmds[cmd] = func
            return func
        return _decorator
    
    def validator(self, cmd):
        if type(cmd) == str:
            cmd = cmd.encode()
        def _decorator(func):
            self.validators[cmd] = func
            return func
        return _decorator
    
    def handle_message(self, connection, message):
        logger.info("MessageHandler: received message %s", message)
        cmd, prefix, params = self._parse_message(message)
        if cmd not in self.cmds:
            logger.info("MessageHandler: received unknown message type %s", cmd)
            return

        valid = True
        if cmd in self.validators:
            valid = self.validators[cmd](params, prefix = prefix)

        if not valid:
            # TODO return reply to client
            raise ValueError()

        send = partial(self.send, connection)
        self.cmds[cmd](send, *params, prefix = prefix)
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