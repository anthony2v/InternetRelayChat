from irc_client.client import Client

from unittest import mock

def test_send_calls_connection_send_message():
    client = Client()
    client._connection = mock.MagicMock()

    client.send(b'NICK', b'one')
    client._connection.send_message.assert_called_with(b'NICK one')
