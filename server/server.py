import asyncio
import socket
import select

import logging

logging.basicConfig(level=logging.DEBUG)


class Connection:
    
    def __init__(self, socket_conn, addr):
        self.socket = socket_conn
        self.addr = addr
        self.host, *_ = socket.gethostbyaddr(addr[0])
        self.buffer = b''
        self.messages = []

    def shutdown(self):
        try:
            self.socket.shutdown()
            self.socket.close()
        except:
            pass

    def _read_bytes(self):
        new_bytes = self.socket.recv(512)
        if not new_bytes:
            raise EOFError()

        self.buffer += new_bytes
    
    def _get_messages(self):
        self._read_bytes()

        *msgs, self.buffer = self.buffer.split(b'\r\n')
        self.messages += msgs

    def next_message(self):
        return self.messages.pop(0)

    def has_messages(self):
        read_available, *_ = select.select({self.socket}, {}, {}, 0)
        if read_available:
            self._get_messages()

        return len(self.messages) > 0

class ConnectionManager:

    def __init__(self):
        self.open_connections = set()

    async def _read_incoming_messages(self):
        logging.info('Reading incoming messages!')
        while True:
            for connection in self.open_connections:
                try:
                    if connection.has_messages():
                        msg = connection.next_message()
                        await self.handle_message(connection, msg)
                except EOFError:
                    await self.remove_connection(connection)
        
            await asyncio.sleep(0.01)

    async def shutdown_connections(self):
        for connection in self.open_connections:
            connection.shutdown()

    async def handle_message(self, connection, msg):
        print(msg)

    async def add_connection(self, connection):
        self.open_connections.add(connection)

    async def remove_connection(self, connection):
        logging.info(f'{connection.host} has left')
        self.open_connections.remove(connection)


class Server:
    
    def __init__(self, connection_manager, host='', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.connection_manager = connection_manager

    async def __aenter__(self):
        self.socket = socket.create_server((self.host, self.port))
        self.socket.setblocking(False)

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.connection_manager.shutdown_connections()
        self.shutdown()

    async def serve(self):
        if not self.socket:
            raise Exception('Socket must be opened first')

        connections_task = asyncio.create_task(self._accept_connections())
        messages_task = asyncio.create_task(self.connection_manager._read_incoming_messages())

        await connections_task
        await messages_task

    def shutdown(self):            
        try:
            self.socket.shutdown()
            self.socket.close()
        except:
            pass

    async def _accept_connections(self):
        logging.info('Accepting connections!')
        while True:
            try:
                conn, addr = self.socket.accept()
                logging.info(f'accepted connection from {addr}')
                await self.connection_manager.add_connection(
                    Connection(conn, addr))
            except BlockingIOError:
                await asyncio.sleep(0.01) # Check for new connections every 10 ms


async def main():
    cm = ConnectionManager()
    async with Server(cm, '0.0.0.0') as server:
        await asyncio.create_task(server.serve())


if __name__ == "__main__":
    asyncio.run(main())
