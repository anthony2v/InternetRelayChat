import asyncio
import socket
from irc_server.server import Server

import pytest
from unittest import mock

def test_server_send_sends_message_to_all_connections_when_no_exclude():
    server = Server()

    server._connections = [
        mock.MagicMock() for _ in range(5)
    ]

    server.send(b'PING')

    for conn in server._connections:
        conn.send_message.asset_called_with(b'::6667 PING')

def test_server_send_sends_message_to_all_connections_except_the_one_specified_by_exclude():
    server = Server()

    exclude = mock.MagicMock()
    server._connections = [
        mock.MagicMock() for _ in range(5)
    ] + [exclude]

    server.send(b'PING', exclude=exclude)

    for conn in server._connections:
        if conn != exclude:
            conn.send_message.assert_called_with(b'::6667 PING')
        else:
            conn.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_remove_connection():
    server = Server()
    
    connection = mock.MagicMock()
    server._connections = [connection]

    await server.remove_connection(connection)
    
    assert server._connections == []
    connection.shutdown.assert_called()


@pytest.mark.asyncio
async def test_server_accepts_connections():
    with Server('0.0.0.0', port=6667) as server:
        server_task = asyncio.create_task(server.start())

        s = socket.create_connection(('0.0.0.0', 6667))

        # Sleep to allow time for connection to be accepted
        await asyncio.sleep(0.1)

        # Cancel server task
        server_task.cancel()
        try:
            await server_task
        except:
            pass

        # Shut down test client
        s.shutdown(socket.SHUT_RDWR)
        s.close()

        assert len(server._connections) == 1


@pytest.mark.asyncio
async def test_server_processes_messages():
    with Server('0.0.0.0', port=6667) as server:
        server.handle_message = mock.AsyncMock()

        server_task = asyncio.create_task(server.start())

        s = socket.create_connection(('0.0.0.0', 6667))
        s.sendall(b'NICK\r\n')

        # Sleep to allow time for connection to be accepted
        await asyncio.sleep(0.1)

        # Cancel server task
        server_task.cancel()
        try:
            await server_task
        except:
            pass

        # Shut down test client
        s.shutdown(socket.SHUT_RDWR)
        s.close()

        server.handle_message.assert_called_with(server._connections[0], b'NICK')


@pytest.mark.asyncio
async def test_server_writes_back_messages():
    with Server('0.0.0.0', port=6667) as server:
        server.handle_message = mock.AsyncMock()

        server_task = asyncio.create_task(server.start())

        s = socket.create_connection(('0.0.0.0', 6667))
        s.settimeout(1.0)
        s.sendall(b'PING\r\n')
        
        # Sleep to allow time for connection to be accepted
        await asyncio.sleep(0.1)
        server._connections[0].send_message(b'PONG')

        await asyncio.sleep(0.1)
        
        assert s.recv(512) == b'PONG\r\n'

        # Shut down test client
        s.shutdown(socket.SHUT_RDWR)
        s.close()

        # Cancel server task
        server_task.cancel()
        try:
            await server_task
        except:
            pass



