import asyncio, socket

from irc_core import MessageListener, Connection, logger
from irc_core.parser import serialize_message


class Server(MessageListener):

    def __init__(self, host='', port=3000):
        self.host = host
        self.port = port
        self._socket = None
        self._connections = []

    async def _accept_connections(self):
        while True:
            try:
                conn, addr = self._socket.accept()
                self._connections.append(
                    Connection(conn, addr))
                logger.info(f'accepted connection from {addr}')
            except BlockingIOError:
                # Wait 10 miliseconds before checking for connections
                await asyncio.sleep(0.01)

    async def _process_messages(self):
        while True:
            processing = []
            
            # Read connections
            for connection in self._connections:
                try:
                    ready = connection.has_messages()
                except EOFError:
                    self.remove_connection(connection)
                else:
                    if ready:
                        msg = connection.next_message()
                        processing.append(
                            self.handle_message(connection, msg))

            # Wait for all messages to finish processing
            await asyncio.gather(*processing)

            # Write to connections
            for connection in self._connections:
                connection.flush_messages()

            await asyncio.sleep(0.01) # Wait 10 milliseconds before checking messages

    def __enter__(self):
        self._socket = socket.create_server((self.host, self.port))
        self._socket.setblocking(False)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info('shutting down server')

        self.accept_connection_task.cancel()
        self.process_messages_task.cancel()

        self._socket.shutdown(socket.SHUT_RD)

        for connection in self._connections:
            connection.shutdown()
        self._connections.clear()

        
        self._socket.close()

    async def start(self):
        if not self._socket:
            raise Exception('socket must be opened first (use with statement)')

        logger.info('starting server')

        self.accept_connection_task = asyncio.create_task(self._accept_connections())
        self.process_messages_task = asyncio.create_task(self._process_messages())

        await asyncio.gather(self.accept_connection_task, self.process_messages_task)

    def remove_connection(self, connection):
        self._connections.remove(connection)
        connection.shutdown()

    def send(self, msg: bytes, *params: bytes, prefix = None, exclude = None):
        if prefix is None:
            prefix = f'{self.host}:{self.port}'.encode()

        message = serialize_message(msg, *params, prefix = prefix)

        for connection in self._connections:
            if connection == exclude:
                continue

            connection.send_message(message)
