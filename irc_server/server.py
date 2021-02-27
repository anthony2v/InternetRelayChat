from irc_core import MessageListener, Connection
from irc_core.parser import serialize_message


class Server(MessageListener):

    def __init__(self):
        self.connections = []
        self.host = None

    def send(self, msg: bytes, *params: bytes, prefix = None, exclude = None):
        if prefix is None:
            prefix = self.host

        message = serialize_message(msg, *params, prefix = prefix)

        for connection in self.connections:
            if connection == exclude:
                continue

            connection.send_message(message)
