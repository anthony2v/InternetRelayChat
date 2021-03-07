from irc_core.connections import Connection
from irc_core.parser import parse_message
from unittest import mock
from irc_core.message_listener import MessageListener
import pytest
import asyncio

def test_message_listeners_can_be_bound():
    listener = MessageListener()
    
    mock_fn = mock.AsyncMock()

    listener.on('NICK')(mock_fn)

    listener.general_message_handlers['NICK'](mock.MagicMock())
    mock_fn.assert_called()

def test_handle_message_calls_parser():
    listener = MessageListener()

    mock_connection = mock.MagicMock(spec = Connection)
    msg = b"NICK\r\n"

    with mock.patch("irc_core.message_listener.parse_message", return_value = (None, None, None)) as parse_message:
        asyncio.run(listener.handle_message(
            connection = mock_connection,
            message = msg
        ))

        parse_message.assert_called_with(msg)

@pytest.mark.asyncio
async def test_bound_message_listener_is_called():
    listener = MessageListener()
    
    mock_fn = mock.AsyncMock()

    listener.on('NICK')(mock_fn)

    await listener.handle_message(mock.MagicMock(), b'NICK')

    mock_fn.assert_called()

@pytest.mark.asyncio
async def test_messages_with_no_bound_function_are_dropped():
    listener = MessageListener()
    
    mock_fn = mock.AsyncMock()

    listener.on('NICK')(mock_fn)

    await listener.handle_message(mock.MagicMock(), b'FREE')

    mock_fn.assert_not_called()

def test_parse_message_returns_command_name():
    listener = MessageListener()

    msg = b":WiZ NICK Kilroy\r\n"

    command, prefix, params = parse_message(msg)

    assert command == "NICK"
    assert prefix == "WiZ"
    assert params == ["Kilroy"]

    msg = b"NICK Wiz\r\n"

    command, prefix, params = parse_message(msg)

    assert command == "NICK"
    assert prefix == None
    assert params == ["Wiz"]

    msg = b":Angel PRIVMSG Wiz :Hello are you receiving this message ?\r\n"

    command, prefix, params = parse_message(msg)

    assert command == "PRIVMSG"
    assert prefix == "Angel"
    assert params == ["Wiz", "Hello are you receiving this message ?"]
