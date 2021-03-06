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
        self.view.add_msg('SYSTEM', 'Connecting to %s:%s' % (host, port))
        self._connect(host, port)

        self._process_msg_task = asyncio.create_task(self._process_messages())

        await self._prompt_nickname()
        await self._prompt_realname()

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
            self.view.add_msg(self.username, msg)
            self.send(b'PRIVMSG', b'#general', enc_msg)

    async def _prompt_nickname(self):        
        self.view.add_msg('SYSTEM', 'Please enter your nickname:')

        evt = asyncio.Event()

        @self.add_update_callback
        def callback(msg):
            self.nickname = msg
            evt.set()
            return True

        await evt.wait()
        evt.clear()

        self.send(b'NICK', self.nickname.encode('ascii'))

        @self.once(ERR_NICKCOLLISION)
        async def on_nick_collision(connection, nick, *params, prefix=None):
            self.view.add_msg('SYSTEM', 'Nickname taken: %s' % nick.decode('ascii'))
            evt.set()
        
        await asyncio.sleep(1)
        self.rm_update_callback(callback)
        
        if evt.is_set():
            return await self._prompt_nickname()
            
        self.view.add_msg('SYSTEM', 'Nickname accepted: %s' % self.nickname)
        self.off(ERR_NICKCOLLISION, on_nick_collision)

    async def _prompt_realname(self):
        self.view.add_msg('SYSTEM', 'Please enter your real name:')

        evt = asyncio.Event()

        @self.add_update_callback
        def callback(msg):
            self.realname = msg
            evt.set()
            return True

        await evt.wait()
        evt.clear()

        self.send(b'USER',
                    self.username.encode('ascii'),
                    self.hostname.encode('ascii'),
                    self._connection.host.encode('ascii'),
                    self.realname.encode('ascii'),
                    )
        
        @self.once(ERR_ALREADYREGISTERED)
        async def on_already_registered(connection, nick, *params, prefix=None):
            self.view.add_msg('SYSTEM', 'User already registered: %s@%s' % (self.username, self.hostname))
            evt.set()
        
        await asyncio.sleep(1)
        self.rm_update_callback(callback)
        
        if evt.is_set():
            return exit(1)

        self.view.add_msg('SYSTEM', 'Welcome %s!' % self.realname)
        self.off(ERR_ALREADYREGISTERED, on_already_registered)
