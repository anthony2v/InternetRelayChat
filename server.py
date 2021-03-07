import asyncio
import argparse

async def main(args):
    from irc_server import server
    from irc_server import handlers
    
    server.host = args.ip
    server.port = args.port

    with server:
        await server.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, default='127.0.0.1',
                        help='The IP to bind the server to.')
    parser.add_argument('--port', type=int, default=6667,
                        help='The port to bind the server to.')

    args = parser.parse_args()

    asyncio.run(main(args))
    
