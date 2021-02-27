import socket
import select

from .logger import logger


class Connection:

    def __init__(self, socket_conn, addr):
        self.socket = socket_conn
        self.addr = addr
        self.host, *_ = socket.gethostbyaddr(addr[0])
        self.buffer = b''
        self.messages = []

    def shutdown(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass

    def _read_bytes(self):
        new_bytes = self.socket.recv(512)
        if not new_bytes:
            raise EOFError() # TODO Should this be thrown once the buffer is empty?

        self.buffer += new_bytes

    def _get_messages(self):
        read_available, *_ = select.select({self.socket}, {}, {}, 0)
        if read_available:
            self._read_bytes()
            *msgs, self.buffer = self.buffer.split(b'\r\n')
            self.messages += msgs

    def next_message(self):
        return self.messages.pop(0)

    def has_messages(self):
        self._get_messages()

        return len(self.messages) > 0
