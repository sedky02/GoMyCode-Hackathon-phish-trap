import asyncio
import json

_subscribers: set[asyncio.Queue] = set()


def publish(event: str, data: dict) -> None:
    msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
    for q in list(_subscribers):
        q.put_nowait(msg)


async def stream():
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.add(q)
    try:
        yield ": connected\n\n"
        while True:
            try:
                yield await asyncio.wait_for(q.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ": ping\n\n"
    finally:
        _subscribers.discard(q)
