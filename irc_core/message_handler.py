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
