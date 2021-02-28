import asyncio
from irc_client.client import Client

import pytest
from unittest import mock

def test_send_calls_connection_send_message():
    client = Client()
    client._connection = mock.MagicMock()

    client.send(b'NICK', b'one')
    client._connection.send_message.assert_called_with(b'NICK one')


@pytest.fixture
async def server():
    from irc_server.server import Server
    with Server() as s:
        s_task = asyncio.create_task(s.start())
        
        yield s

        # Cancel server task
        s_task.cancel()
        try:
            await s_task
        except:
            pass


@pytest.mark.asyncio
async def test_client_can_connect_to_server(server):
    server._accept_connection = mock.MagicMock()

    client = Client()
    client_task = asyncio.create_task(
        client.connect('0.0.0.0', server.port))

    await asyncio.sleep(0.1)

    assert client._connection is not None
    server._accept_connection.assert_called()

    await asyncio.sleep(0.1)

    client.disconnect()

    with pytest.raises(asyncio.exceptions.CancelledError):
        await client_task


@pytest.mark.asyncio
async def test_client_can_send_and_receive_messages_to_from_server(server):
    async def echo_message(conn, msg):
        conn.send_message(msg)

    server.handle_message = echo_message

    client = Client()
    
    client.handle_message = mock.AsyncMock()

    client_task = asyncio.create_task(
        client.connect('0.0.0.0', server.port))

    await asyncio.sleep(0.1)

    client.send(b'NICK', b'Drew')

    await asyncio.sleep(0.1)

    client.handle_message.assert_called()
    assert client.handle_message.call_args.args[1] == b'NICK Drew'

    client.disconnect()

    with pytest.raises(asyncio.exceptions.CancelledError):
        await client_task
