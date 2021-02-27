from irc_core import MessageListener, Connection
from irc_core.parser import serialize_message


class Client(MessageListener):

    def __init__(self):
        self._connection = None
        self.host = None

    def send(self, msg: bytes, *params: bytes):
        message = serialize_message(msg, *params)
        
        if self._connection is not None:
            self._connection.send_message(message)
