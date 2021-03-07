import socket, select

from .logger import logger

import time


class Connection:
    """A higher-level representation of a socket connection to 
    encompass logic for reading and writing to the socket in
    a non-blocking way."""

    def __init__(self, socket_conn, addr):
        self._socket = socket_conn
        self.addr = addr
        self.nickname = None
        self.username = None
        self.real_name = None
        self.registered = False

        try:
            self.host = socket.gethostbyaddr(addr[0])[0]
        except:
            self.host = 'unknown'

        self._incoming_buffer = b''
        self._incoming_messages = []
        self._outgoing_messages = []
        self._last_message_time = time.time()

        self.ping_timeout = None

    def __str__(self) -> str:
        return f'Connection(addr={self.addr}, nickname={self.nickname}, host={self.host}, username={self.username}, real_name={self.real_name})'

    @property
    def time_since_last_message(self):
        return time.time() - self._last_message_time

    def shutdown(self):
        """Ensures a proper shutdown of the socket"""
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
        except:
            pass

    def _read_bytes(self):
        """Reads up to 512 bytes from the socket and adds them to
        the buffer.
        
        NOTE: Will raise a BlockingIOError if called directly
        """
        new_bytes = self._socket.recv(512)
        if not new_bytes:
            raise EOFError() # TODO Should this be thrown once the _incoming_buffer is empty?

        self._incoming_buffer += new_bytes

    def _get_messages(self):
        """Checks if there is any data ready to be read from the
        socket, and updates the list of incoming messages.
        
        NOTE: Messages are split at `\\r\\n`
        """
        read_available, *_ = select.select({self._socket}, {}, {}, 0)
        if read_available:
            self._read_bytes()
            *msgs, self._incoming_buffer = self._incoming_buffer.split(b'\r\n')
            self._incoming_messages += msgs
            self._outgoing_messages = []
            self._last_message_time = time.time()

    def next_message(self):
        """Returns the next complete message that is ready for processing.

        NOTE: An IndexError may result. Use has_messages() to check if
        there are any messages ready.
        """
        return self._incoming_messages.pop(0)

    def has_messages(self):
        """Checks the socket for data, and returns True if there are messages
        ready to be processed."""
        self._get_messages()

        return len(self._incoming_messages) > 0

    def send_message(self, msg):
        """Adds a message to the queue of outgoing messages.
        
        NOTE: Does not write to the socket. Use flush_messages() to 
        write all pending messages to the socket.

        Args:
            msg (bytes): The message to be sent. Does NOT need to be terminated
                with \\r\\n
        
        Raises:
            ValueError: A value error is raised if the length of the message if greater
                than 512 bytes (including the \\r\\n terminator)
        """
        if not msg.endswith(b'\r\n'):
            msg = msg + b'\r\n'

        if len(msg) > 512:
            raise ValueError(f'msg too long ({len(msg)})')

        self._outgoing_messages.append(msg)
    
    def flush_messages(self):
        """Writes all pending messages to the socket for delivery."""
        if self._outgoing_messages:
            msg = b''.join(self._outgoing_messages)
            self._outgoing_messages = []
            
            self._socket.sendall(msg)
