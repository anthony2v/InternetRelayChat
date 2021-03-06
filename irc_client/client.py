from irc_core import MessageListener, Connection
from irc_core.parser import serialize_message

import socket, asyncio


class Client(MessageListener):
    """A MessageListener class with additional functionality
    for connecting to a Server and sending/receiving messages
    to and from it."""

    def __init__(self):
        super().__init__()

        self._connection = None

        self._process_msg_task = None

    def _connect(self, host, port=6667):
        """Creates a socket connection to the server and wraps it in
        a Connection instance.
        
        Args:
            host (str): The IP of the server to connect to.
            port (int): The port to connect on.
        """
        conn_socket = socket.create_connection((host, port))
        conn_socket.setblocking(False)
        
        self._connection = Connection(conn_socket, (host, port))

    async def _process_messages(self):
        """A co-routine to process messages received from the server,
        and write back responses asynchronously."""
        while True:
            # Read messages
            try:
                ready = self._connection.has_messages()
            except EOFError:
                self.disconnect()
                break
            else:
                if ready:
                    msg = self._connection.next_message()
                    # TODO Wrap with error handling so client doesn't crash on bad message
                    await self.handle_message(self._connection, msg)
            
            # Write all pending message back to the server
            self._connection.flush_messages()
            
            await asyncio.sleep(0.01)
        
        # TODO UI Event: Connection closed unexpectedly?

    def disconnect(self):
        """Disconnect from the server and handle shutdown and cleanup of
        the connection."""
        if self._connection is not None:
            self._connection.shutdown()
        if self._process_msg_task is not None:
            self._process_msg_task.cancel()

    async def connect(self, host, port):
        """Connect the client to a server and begin processing messages.
        
        Args:
            host (str): The IP of the server to connect to
            port (int): The port number to connect on
        """
        self._connect(host, port)

        self._process_msg_task = asyncio.create_task(self._process_messages())

        await self._process_msg_task

    def send(self, msg: bytes, *params: bytes):
        """Serialize and send a message to the server connection.

        Args:
            msg (bytes): The type of message to send (i.e NICK, PRIVMSG, etc..)
            *params (bytes): Any number of parameters to the message.
                NOTE Only the last parameter may include spaces (0x20)
        """
        message = serialize_message(msg, *params)
        
        if self._connection is not None:
            self._connection.send_message(message)
