import asyncio
from irc_client import client

from irc_client.handlers import *

import threading

def get_inputs(client_task):
    while not client_task.done():
        message = input("> ").encode()
        client._connection.send_message(message)

async def main():
    client_task = asyncio.create_task(client.connect("0.0.0.0", 6667))
    input_thread = threading.Thread(target=get_inputs, args=(client_task,))
    input_thread.start()

    await client_task

if __name__ == "__main__":
    asyncio.run(main())
    