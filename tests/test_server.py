from irc_server.server import Server

from unittest import mock


def test_server_send_sends_message_to_all_connections_when_no_exclude():
    server = Server()

    server.connections = [
        mock.MagicMock() for _ in range(5)
    ]

    server.send(b'PING')

    for conn in server.connections:
        conn.send_message.asset_called_with(b'PING')
