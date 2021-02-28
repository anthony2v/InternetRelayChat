from irc_core import MessageListener, Connection
from irc_core.parser import serialize_message

import socket, asyncio


class Client(MessageListener):

    def __init__(self):
        self._connection = None
        self.host = None

        self._process_msg_task = None

    def _connect(self, host, port=6667):
        conn_socket = socket.create_connection((host, port))
        conn_socket.setblocking(False)
        
        self._connection = Connection(conn_socket, host)

    async def _process_messages(self):
        while True:
            try:
                ready = self._connection.has_messages()
            except EOFError:
                await self.disconnect()
                break
            else:
                if ready:
                    msg = self._connection.next_message()
                    await self.handle_message(self._connection, msg)
            
            self._connection.flush_messages()
            
            await asyncio.sleep(0.01)
        
        # TODO UI Event: Connection closed unexpectedly?

    def disconnect(self):
        if self._connection is not None:
            self._connection.shutdown()
        if self._process_msg_task is not None:
            self._process_msg_task.cancel()

    async def connect(self, host, port):
        self._connect(host, port)

        self._process_msg_task = asyncio.create_task(self._process_messages())

        await self._process_msg_task

    def send(self, msg: bytes, *params: bytes):
        message = serialize_message(msg, *params)
        
        if self._connection is not None:
            self._connection.send_message(message)
