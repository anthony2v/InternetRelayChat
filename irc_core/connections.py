import socket, select

from .logger import logger


class Connection:

    def __init__(self, socket_conn, addr):
        self._socket = socket_conn
        self.addr = addr
        self.nickname = None
        self.host = socket.gethostbyaddr(addr[0])[0]
        self._incoming_buffer = b''
        self._incoming_messages = []
        self._outgoing_messages = []

    def shutdown(self):
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
        except:
            pass

    def _read_bytes(self):
        new_bytes = self._socket.recv(512)
        if not new_bytes:
            raise EOFError() # TODO Should this be thrown once the _incoming_buffer is empty?

        self._incoming_buffer += new_bytes

    def _get_messages(self):
        read_available, *_ = select.select({self._socket}, {}, {}, 0)
        if read_available:
            self._read_bytes()
            *msgs, self._incoming_buffer = self._incoming_buffer.split(b'\r\n')
            self._incoming_messages += msgs
            self._outgoing_messages = []

    def next_message(self):
        return self._incoming_messages.pop(0)

    def has_messages(self):
        self._get_messages()

        return len(self._incoming_messages) > 0

    def send_message(self, msg):
        self._outgoing_messages.append(msg)
