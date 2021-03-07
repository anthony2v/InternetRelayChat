import asyncio

import argparse




async def main(args):
    from irc_client import client
    from irc_client import handlers
    from irc_client.view import View

    with View() as view:
        view.add_subscriber(client)
        client.view = view

        view_task = asyncio.create_task(view.run())

        await client.prompt_user_info()

        client_task = asyncio.create_task(client.connect(args.host, args.port))
            
        done, _ = await asyncio.wait([view_task, client_task], return_when=asyncio.FIRST_EXCEPTION)
    
        for f in done:
            print(f.result())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='The IP of the server to connect to.')
    parser.add_argument('--port', type=int, default=6667,
                        help='The port to connect to the server on.')
    args = parser.parse_args()

    asyncio.run(main(args))
