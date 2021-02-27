from irc_core.connections import Connection
from unittest import mock
from irc_core.message_listener import MessageListener
import pytest
import asyncio

def test_message_listeners_can_be_bound():
    ch = MessageListener()
    
    mock_fn = mock.MagicMock()

    @ch.on('NICK')
    def fn(send, *params, prefix = None):
        mock_fn()

    ch.cmds[b'NICK'](mock.MagicMock())
    mock_fn.assert_called()

def test_handle_message_calls_parser():
    ch = MessageListener()

    mock_connection = mock.MagicMock(spec = Connection)
    msg = b"NICK\r\n"

    ch._parse_message = mock.MagicMock(return_value = (None, None, None))

    asyncio.run(ch.handle_message(
        connection = mock_connection,
        message = msg
    ))

    ch._parse_message.assert_called_with(msg)

def test_parse_message_returns_command_name():
    ch = MessageListener()

    msg = b":WiZ NICK Kilroy\r\n"

    command, prefix, params = ch._parse_message(msg)

    assert command == b"NICK"
    assert prefix == b"WiZ"
    assert params == [b"Kilroy"]

    msg = b"NICK Wiz\r\n"

    command, prefix, params = ch._parse_message(msg)

    assert command == b"NICK"
    assert prefix == None
    assert params == [b"Wiz"]

    msg = b":Angel PRIVMSG Wiz :Hello are you receiving this message ?\r\n"

    command, prefix, params = ch._parse_message(msg)
    print(params)
    assert command == b"PRIVMSG"
    assert prefix == b"Angel"
    assert params == [b"Wiz", b"Hello are you receiving this message ?"]
