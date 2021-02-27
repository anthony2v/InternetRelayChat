from irc_core import MessageHandler, Connection


class Server(MessageHandler):

    def __init__(self):
        self.connections = {}

    def send(self, msg: bytes, *params: bytes, prefix = None, exclude = None):
        for connection in self.connections.values():
            if connection == exclude:
                continue

            connection