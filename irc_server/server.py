import asyncio
import socket
from asyncio.exceptions import CancelledError

from irc_core import MessageListener, Connection, logger
from irc_core.parser import serialize_message


class Server(MessageListener):
    """A MessageListener class with additional functionality
    for accepting socket connections, and reading and writing
    to/from them."""

    PING_INTERVAL = 60  # seconds
    PONG_TIMEOUT = 5  # seconds

    def __init__(self, host='', port=6667):
        """

        Args:
            host (str): The host IP to bind the server to
            port (int): The port to listen for connections on
        """
        super().__init__()
        self.host = host
        self.port = port
        self._socket = None
        self._connections = []
        self._connect_listeners = []
        self._disconnect_listeners = []

    def on_connect(self, func):
        self._connect_listeners.append(func)
        return func

    def on_disconnect(self, func):
        self._disconnect_listeners.append(func)
        return func

    async def _accept_connections(self):
        """Co-routine to listen for new connections to the server."""
        while True:
            try:
                conn, addr = self._socket.accept()
                self._accept_connection(conn, addr)
                logger.info(f'accepted connection from {addr}')
            except BlockingIOError:
                # Wait 10 miliseconds before checking for connections
                await asyncio.sleep(0.01)

    def _accept_connection(self, conn, addr):
        """Accept and process a raw socket connection."""
        connection = Connection(conn, addr)
        self._connections.append(connection)
        for connect_listener in self._connect_listeners:
            connect_listener(connection)

    async def _process_messages(self):
        """Co-routine to read incoming messages, handle them, and then
        write back any responses.

        Messages from distinct connections are processed 'in parallel' as
        asyncio co-routines.

        If multiple messages are received from a single connection, they
        will be processed in series.
        """
        while True:
            processing = []

            # Read connections
            for connection in self._connections:
                try:
                    ready = connection.has_messages()
                except EOFError:
                    await self.remove_connection(connection)
                else:
                    if ready:
                        msg = connection.next_message()
                        processing.append(
                            self.handle_message(connection, msg))

                if connection.time_since_last_message > self.PING_INTERVAL and not connection.ping_timeout:
                    self.ping(connection)

            # Wait for all messages to finish processing
            # TODO Wrap in try-except so that errors handling messages don't crash the server
            await asyncio.gather(*processing)

            # Write to connections
            for connection in self._connections:
                connection.flush_messages()

            # Wait 10 milliseconds before checking messages
            await asyncio.sleep(0.01)

    def __enter__(self):
        """Context-manager which creates the server socket."""
        logger.info("Creating server at %s:%s ..." % (self.host, self.port))
        self._socket = socket.create_server((self.host, self.port))
        self._socket.setblocking(False)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ensures clean shutdown of all connections when the program
        leaves the scope of the context-manager."""
        logger.info('shutting down server')

        self._accept_connections_task.cancel()
        self._process_message_task.cancel()

        self._socket.shutdown(socket.SHUT_RD)

        for connection in self._connections:
            connection.shutdown()
        self._connections.clear()

        self._socket.close()

    async def start(self):
        """Start the server.

        Begins listening for new connections and messages to process
        """
        if not self._socket:
            raise Exception('socket must be opened first (use with statement)')

        self._accept_connections_task = asyncio.create_task(
            self._accept_connections())
        self._process_message_task = asyncio.create_task(
            self._process_messages())

        logger.info('...server is ready!')

        await asyncio.gather(self._accept_connections_task, self._process_message_task)

    async def remove_connection(self, connection):
        """Handles shutdown and cleanup of dead connections."""
        logger.info('removing connection %s', connection)

        for disconnect_listener in self._disconnect_listeners:
            await disconnect_listener(connection)
        self._connections.remove(connection)
        connection.shutdown()

    def ping(self, connection):
        logger.info('pinging %s', connection)
        self.send_to(connection, b'PING')
        connection.flush_messages()

        async def on_timeout(future):
            try:
                future.exception()
            except CancelledError:
                pass
            else:
                connection.ping_timeout = None
                await self.remove_connection(connection)

        connection.ping_timeout = timeout = asyncio.create_task(
            asyncio.sleep(self.PONG_TIMEOUT))
        timeout.add_done_callback(on_timeout)

        @self.once(b'PONG', from_=connection)
        async def on_pong(*args, **kwargs):
            connection.ping_timeout = None
            timeout.cancel()

    def send_to(self, connection: Connection, msg: bytes, *params: bytes, prefix=None):
        return self.send(msg, *params, prefix=prefix, to=connection)

    def send(self, msg: bytes, *params: bytes, prefix=None, exclude=None, to=None):
        """Serializes a message, and sends it to the appropriate connections.

        By default, will send to all connections.

        Args:
            msg (bytes): The type of message to send (i.e NICK, PRIVMSG, etc...)
            *params (bytes): Any number of parameters to the message.
                NOTE: Only the last parameter may include a space (0x20)
            prefix (bytes): Optional prefix indicating who sent the message. If prefix
                is None, then the prefix will be set to the name of the server.
            exclude (Connection): Optionally exclude a connection from being sent to.
                Useful when the message should not be echoed back to the client which sent it.
            to (Connection): Optionally send only to a specific connection
        """
        if prefix is None:
            prefix = f'{self.host}:{self.port}'.encode()

        message = serialize_message(msg, *params, prefix=prefix)

        if to is not None:
            to.send_message(message)
        else:
            for connection in self._connections:
                if connection == exclude:
                    continue

                connection.send_message(message)
