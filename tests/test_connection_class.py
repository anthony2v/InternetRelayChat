from irc_core.connections import Connection
import socket

from unittest import mock

import pytest


@mock.patch('irc_core.connections.socket.gethostbyaddr', return_value=('laptop1',))
def test_connection_gets_host_name(mock_gethostbyaddr):
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))
    
    mock_gethostbyaddr.assert_called_with('127.0.0.1')
    assert conn.host == 'laptop1'


def test_next_message_returns_first_message_in_buffer_and_removes_it():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))

    conn.messages = ['first message', 'second message']
    assert conn.next_message() == 'first message'
    assert conn.next_message() == 'second message'

    with pytest.raises(IndexError):
        conn.next_message()


def test_has_message_calls__get_messages():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))
    conn._get_messages = mock.MagicMock()

    conn.has_messages()

    conn._get_messages.assert_called()


def test_has_messages_returns_true_in_there_are_messages_in_the_buffer():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))
    conn._get_messages = mock.MagicMock()

    conn.messages = ['message 1']
    assert conn.has_messages()

    conn.messages = []
    assert not conn.has_messages()


def test_read_bytes_appends_new_bytes_to_buffer():
    mock_socket = mock.MagicMock()
    conn = Connection(mock_socket, ('127.0.0.1', 50000))
    
    conn.buffer = b'abcd'
    mock_socket.recv.return_value = b'efgh'

    conn._read_bytes()
    assert conn.buffer == b'abcdefgh'


def test_read_bytes_raises_EOFError_when_no_new_bytes_are_returned():
    mock_socket = mock.MagicMock()
    conn = Connection(mock_socket, ('127.0.0.1', 50000))
    
    mock_socket.recv.return_value=''

    with pytest.raises(EOFError):
        conn._read_bytes()

def test_socket_recv_returns_empty_string_on_eof():
    """Tests the assumption that when a socket disconnects, then the paired
    sockets recv method will return an empty string."""
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    s2.send(b'hello')
    assert s1.recv(64) == b'hello'

    with pytest.raises(BlockingIOError):
        s1.recv(64)

    s2.close()

    assert s1.recv(64) == b''


def test_connection_shutdown():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))
    conn.shutdown()

    assert s1.recv(8) == b''

def test_connection_shutdown_on_closed_socket_does_not_throw_error():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))
    conn.shutdown()
    conn.shutdown()

def test_get_messages_can_be_called_even_when_no_bytes_are_ready_to_be_read():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))
    conn._get_messages()
    assert conn.messages == []
    assert conn.buffer == b''


def test_get_messages_splits_messages_at_crlf_and_adds_then_to_messages():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))

    s1.sendall(b'abcd\r\nefgh\r\n')

    conn._get_messages()

    assert conn.messages == [b'abcd', b'efgh']


def test_get_messages_puts_any_bytes_after_last_crlf_into_buffer():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))

    s1.sendall(b'abcd\r\nefgh')

    conn._get_messages()

    assert conn.messages == [b'abcd']
    assert conn.buffer == b'efgh'


def test_get_messages_bytes_already_in_buffer_are_prefixed_to_first_message():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))
    conn.buffer = b'abcd'

    s1.sendall(b'efgh\r\n')

    conn._get_messages()
    assert conn.messages == [b'abcdefgh']
    assert conn.buffer == b''
