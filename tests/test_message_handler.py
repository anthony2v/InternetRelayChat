from server.server import Connection
from unittest import mock
from irc_core.message_handler import MessageHandler
import pytest

def test_message_handlers_can_be_bound():
    ch = MessageHandler()
    
    mock_fn = mock.MagicMock()

    @ch.command('NICK')
    def fn(send, *params, prefix = None):
        mock_fn()

    ch.cmds[b'NICK'](mock.MagicMock())
    mock_fn.assert_called()

def test_validators_can_be_bound():
    ch = MessageHandler()
    
    mock_fn = mock.MagicMock()

    @ch.validator('NICK')
    def fn(*params, prefix = None):
        mock_fn()

    ch.validators[b'NICK']()
    mock_fn.assert_called()

def test_handle_message_calls_parser():
    ch = MessageHandler()

    mock_connection = mock.MagicMock(spec = Connection)
    msg = b"NICK\r\n"

    ch._parse_message = mock.MagicMock(return_value = (None, None, None))

    ch.handle_message(
        connection = mock_connection,
        message = msg
    )

    ch._parse_message.assert_called_with(msg)

def test_parse_message_returns_command_name():
    ch = MessageHandler()

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

def test_bound_validator_called_with_parsed_message():
    ch = MessageHandler()
    
    mock_validate = mock.MagicMock()
    mock_command = mock.MagicMock()

    ch.validator('PRIVMSG')(mock_validate)
    ch.command('PRIVMSG')(mock_command)

    mock_connection = mock.MagicMock(spec = Connection)
    msg = b":Angel PRIVMSG Wiz :Hello are you receiving this message ?\r\n"

    ch.handle_message(
        connection = mock_connection,
        message = msg
    )

    mock_validate.assert_called_with([b"Wiz", b"Hello are you receiving this message ?"], prefix = b"Angel")

def test_when_validator_returns_false_handle_message_raises_an_error():
    ch = MessageHandler()
    
    mock_validate = mock.MagicMock(return_value = False)
    mock_command = mock.MagicMock()

    ch.validator('PRIVMSG')(mock_validate)
    ch.command('PRIVMSG')(mock_command)

    mock_connection = mock.MagicMock(spec = Connection)
    msg = b":Angel PRIVMSG Wiz :Hello are you receiving this message ?\r\n"

    with pytest.raises(ValueError):
        ch.handle_message(
            connection = mock_connection,
            message = msg
        )

    mock_command.assert_not_called()
    
def test_when_validator_returns_true():
    ch = MessageHandler()
    
    mock_validate = mock.MagicMock(return_value = True)
    mock_command = mock.MagicMock()

    ch.validator('PRIVMSG')(mock_validate)
    ch.command('PRIVMSG')(mock_command)

    mock_connection = mock.MagicMock(spec = Connection)
    msg = b":Angel PRIVMSG Wiz :Hello are you receiving this message ?\r\n"

    ch.handle_message(
            connection = mock_connection,
            message = msg
        )

    mock_command.assert_called()
    
    args = mock_command.call_args.args
    kwargs = mock_command.call_args.kwargs
    send = args[0]
    params = args[1:]
    prefix = kwargs["prefix"]

    assert callable(send)
    assert prefix == b"Angel"
    assert params == (b"Wiz", b"Hello are you receiving this message ?")
