from irc_core.replies import *
from irc_core import MessageListener, Connection, logger
from irc_core.parser import serialize_message

import socket, asyncio

from . import patterns

import os


class Client(MessageListener, patterns.Subscriber):
    """A MessageListener class with additional functionality
    for connecting to a Server and sending/receiving messages
    to and from it."""

    def __init__(self):
        super().__init__()

        self._connection = None

        self._process_msg_task = None
        self.view = None
        
        self.hostname = socket.gethostname()
        self.username = os.environ.get('USER', os.environ.get('USERNAME'))
        self.nickname = str()
        self.realname = str()
        
        self.server = None
        
        self._update_callbacks = []

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

    def add_msg(self, user, msg):
        logger.info("add_msg - [%s] %s", user, msg)
        if self.view is not None:
            self.add_msg(user, msg)

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

    async def prompt_user_info(self):
        await self._prompt_realname()
        await self._prompt_nickname()

        self.add_msg('SYSTEM', 'Welcome %s!' % self.realname)

    async def connect(self, host, port):
        """Connect the client to a server and begin processing messages.
        
        Args:
            host (str): The IP of the server to connect to
            port (int): The port number to connect on
        """
        self.add_msg('SYSTEM', 'Connecting to server %s:%s...' % (host, port))
        try:
            self._connect(host, port)
        except OSError as e:
            self.add_msg(
                'SYSTEM', 'Unable to connect to server %s:%s' % (host, port))
            self.add_msg(
                'SYSTEM', 'Exiting...')
    
            await asyncio.sleep(1)
            exit(e.errno)

        self.add_msg(
            'SYSTEM', 'Connected!')


        self._process_msg_task = asyncio.create_task(self._process_messages())

        self._register_with_server()

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

    def add_update_callback(self, func):
        self._update_callbacks.insert(0, func)
        return func

    def rm_update_callback(self, func):
        try:
            self._update_callbacks.remove(func)
        
        except ValueError:
            pass

    def update(self, msg):
        for callback in self._update_callbacks:
            if callback(msg):
                return

        enc_msg = msg.encode('ascii')

        if enc_msg.startswith(b'/'):  # Send raw message
            self._connection.send_message(enc_msg[1:])
        else:
            self.add_msg(self.nickname, msg)
            self.send(b'PRIVMSG', b'#global', enc_msg)

    def _register_with_server(self):
        self.send(b'NICK', self.nickname.encode('ascii'))
        self.send(b'USER',
                  self.username.encode('ascii'),
                  self.hostname.encode('ascii'),
                  self._connection.host.encode('ascii'),
                  self.realname.encode('ascii'),
                  )

    async def _prompt_nickname(self):        
        self.add_msg('SYSTEM', 'Please enter your nickname:')

        evt = asyncio.Event()

        @self.add_update_callback
        def callback(msg):
            self.nickname = msg
            evt.set()
            return True

        await evt.wait()
        self.rm_update_callback(callback)

    async def _prompt_realname(self):
        self.add_msg('SYSTEM', 'Please enter your real name:')

        evt = asyncio.Event()

        @self.add_update_callback
        def callback(msg):
            self.realname = msg
            evt.set()
            return True

        await evt.wait()
        self.rm_update_callback(callback)
