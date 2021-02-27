from irc_server.server import Server

from unittest import mock


def test_server_send_sends_message_to_all_connections_when_no_exclude():
    server = Server()

    server._connections = [
        mock.MagicMock() for _ in range(5)
    ]

    server.send(b'PING')

    for conn in server._connections:
        conn.send_message.asset_called_with(b'PING')

def test_server_send_sends_message_to_all_connections_except_the_one_specified_by_exclude():
    server = Server()

    exclude = mock.MagicMock()
    server._connections = [
        mock.MagicMock() for _ in range(5)
    ] + [exclude]

    server.send(b'PING', exclude=exclude)

    for conn in server._connections:
        if conn != exclude:
            conn.send_message.assert_called_with(b'PING')
        else:
            conn.send_message.assert_not_called()
