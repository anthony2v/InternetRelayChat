from irc_server import server
from irc_server.handlers import *
import asyncio

async def main():
    with server:
        await server.start()


if __name__ == "__main__":
    asyncio.run(main())
    