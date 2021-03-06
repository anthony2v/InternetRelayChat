import asyncio
from irc_client import client

from irc_client.handlers import *

from concurrent.futures import ThreadPoolExecutor

from irc_client.view import View

import argparse

from irc_core.logger import logger, handler

logger.removeHandler(handler)


async def main():
    with View() as view:
        view.add_subscriber(client)
        client.view = view

        view_task = asyncio.create_task(view.run())
        client_task = asyncio.create_task(client.connect("0.0.0.0", 6667))
            
        done, _ = await asyncio.wait([view_task, client_task], return_when=asyncio.FIRST_EXCEPTION)
    
        for f in done:
            f.result()


@client.on(b'PRIVMSG')
async def receive_message(connection, receivers, msg, prefix=None):
    client.view.add_msg(prefix.decode('ascii'), msg.decode('ascii'))


if __name__ == "__main__":
    asyncio.run(main())
