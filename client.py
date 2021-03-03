import asyncio
from irc_client import client
from irc_client.handlers import *

async def get_inputs():
    while True:
        message = input(">").encode()
        client._connection.send_message(message)
        await asyncio.sleep(0.1)

async def main():
    client_task = asyncio.create_task(client.connect("0.0.0.0", 6667))
    get_inputs_task = asyncio.create_task(get_inputs())

    await client_task
    await get_inputs_task

if __name__ == "__main__":
    asyncio.run(main())
    