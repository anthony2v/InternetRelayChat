from unittest import mock
from irc_core.command_handler import CommandHandler

def test_command_handlers_can_be_bound():
    ch = CommandHandler()
    
    mock_fn = mock.MagicMock()

    @ch.command('NICK')
    def fn():
        mock_fn()

    ch.cmds['NICK']()
    mock_fn.assert_called()

def test_validators_can_be_bound():
    ch = CommandHandler()
    
    mock_fn = mock.MagicMock()

    @ch.validator('NICK')
    def fn():
        mock_fn()

    ch.validators['NICK']()
    mock_fn.assert_called()
