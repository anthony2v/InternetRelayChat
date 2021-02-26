class MessageHandler:
    def __init__(self):
        self.cmds = {}
        self.validators = {}
    
    def command(self, cmd):
        def _decorator(func):
            self.cmds[cmd] = func
            return func
        return _decorator
    
    def validator(self, cmd):
        def _decorator(func):
            self.validators[cmd] = func
            return func
        return _decorator
    
    def handle_message(self, connection, message):
        self._parse_message(message)
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