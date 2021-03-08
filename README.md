# IRC Client/Server
A minimal IRC client and server framework built by Anthony and Drew for COMP 445 Concordia University Winter 2021.

## Requirements
Requires Python 3.9+

## Installation
```
python setup.py install
```

## Usage
### Server
```
python server.py -h
```
### Client
```
python client.py -h
```

## Design Description
We wanted to have a multilevel architecture to fully encapsulate the socket logic to help with testability. This also allows us to work as much as possible with higher level domain objects (I.e., commands, parameters, prefixes) rather than raw byte strings. Easy extensibility was desired and so we chose to build an event-driven framework using decorators to register event callbacks. We were inspired by common frameworks like Flask (E.g., @app.route(“…”)) and Celery (E.g., @celery.task) as well as JavaScript’s on/off/once functions for events. This event-driven framework was highly compatible with asyncio coroutines and synchronization primitives. We used the select library with asyncio to allow for non-blocking socket operations.