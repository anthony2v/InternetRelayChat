from unittest import mock
from irc_core.message_handler import MessageHandler

def test_message_handlers_can_be_bound():
    ch = MessageHandler()
    
    mock_fn = mock.MagicMock()

    @ch.command('NICK')
    def fn():
        mock_fn()

    ch.cmds['NICK']()
    mock_fn.assert_called()

def test_validators_can_be_bound():
    ch = MessageHandler()
    
    mock_fn = mock.MagicMock()

    @ch.validator('NICK')
    def fn():
        mock_fn()

    ch.validators['NICK']()
    mock_fn.assert_called()
