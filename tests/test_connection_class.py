from irc_core.connections import Connection
import socket

from unittest import mock

import pytest


@mock.patch('irc_core.connections.socket.gethostbyaddr', return_value=('laptop1',))
def test_connection_gets_host_name(mock_gethostbyaddr):
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))
    
    mock_gethostbyaddr.assert_called_with('127.0.0.1')
    assert conn.host == 'laptop1'


def test_next_message_returns_first_message_in__incoming_buffer_and_removes_it():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))

    conn._incoming_messages = [b'first message', b'second message']
    assert conn.next_message() == b'first message'
    assert conn.next_message() == b'second message'

    with pytest.raises(IndexError):
        conn.next_message()


def test_has_message_calls__get_messages():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))
    conn._get_messages = mock.MagicMock()

    conn.has_messages()

    conn._get_messages.assert_called()


def test_has_messages_returns_true_in_there_are_messages_in_the__incoming_buffer():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))
    conn._get_messages = mock.MagicMock()

    conn._incoming_messages = [b'message 1']
    assert conn.has_messages()

    conn._incoming_messages = []
    assert not conn.has_messages()


def test_read_bytes_appends_new_bytes_to__incoming_buffer():
    mock_socket = mock.MagicMock()
    conn = Connection(mock_socket, ('127.0.0.1', 50000))
    
    conn._incoming_buffer = b'abcd'
    mock_socket.recv.return_value = b'efgh'

    conn._read_bytes()
    assert conn._incoming_buffer == b'abcdefgh'


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
    assert conn._incoming_messages == []
    assert conn._incoming_buffer == b''


def test_get_messages_splits_messages_at_crlf_and_adds_then_to_messages():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))

    s1.sendall(b'abcd\r\nefgh\r\n')

    conn._get_messages()

    assert conn._incoming_messages == [b'abcd', b'efgh']


def test_get_messages_puts_any_bytes_after_last_crlf_into__incoming_buffer():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))

    s1.sendall(b'abcd\r\nefgh')

    conn._get_messages()

    assert conn._incoming_messages == [b'abcd']
    assert conn._incoming_buffer == b'efgh'


def test_get_messages_bytes_already_in__incoming_buffer_are_prefixed_to_first_message():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))
    conn._incoming_buffer = b'abcd'

    s1.sendall(b'efgh\r\n')

    conn._get_messages()
    assert conn._incoming_messages == [b'abcdefgh']
    assert conn._incoming_buffer == b''


def test_send_message_adds_message_to_list_of_outgoing_messages():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))
    
    conn.send_message(b'test')

    assert b'test\r\n' in conn._outgoing_messages


def test_send_message_raises_value_error_when_len_msg_gt_512():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))

    with pytest.raises(ValueError):
        conn.send_message(b't' * 513)


def test_flush_messages_sends_all_buffered_messages():
    conn = Connection(mock.MagicMock(), ('127.0.0.1', 50000))

    conn.send_message(b'abcd')
    conn.send_message(b'efgh')

    conn.flush_messages()

    conn._socket.sendall.assert_called_with(b'abcd\r\nefgh\r\n')

def test_flush_messages_with_socket_pair():
    s1, s2 = socket.socketpair()
    s1.setblocking(False)
    s2.setblocking(False)

    conn = Connection(s2, ('127.0.0.1', 50000))

    conn.send_message(b'abcd')
    conn.send_message(b'efgh')

    conn.flush_messages()

    data = s1.recv(512)
    assert data == b'abcd\r\nefgh\r\n'
