import asyncio


class ProgressBroker:

    def __init__(self):
        self._history: dict[str, list[dict]] = {}
        self._subscribers: dict[str, list[asyncio.Queue[dict]]] = {}

    def start(self, documentation_id: str) -> None:
        self._history[documentation_id] = []
        self._subscribers[documentation_id] = []
        return

    async def publish(self, documentation_id: str, data: dict) -> None:
        if documentation_id not in self._history:
            self.start(documentation_id)
        self._history[documentation_id].append(data)
        subscribers = self._subscribers[documentation_id]
        for subscriber in subscribers:
            await subscriber.put(data)

        return

    def subscribe(self, documentation_id: str) -> tuple[list[dict], asyncio.Queue[dict]]:
        queue = asyncio.Queue()
        self._subscribers[documentation_id].append(queue)

        return self._history[documentation_id], queue

    def unsubscribe(self, documentation_id: str, queue: asyncio.Queue[dict]) -> None:
        if documentation_id in self._subscribers:
            self._subscribers[documentation_id].remove(queue)
        return

    def close(self, documentation_id: str) -> None:
        self._history.pop(documentation_id)
        self._subscribers.pop(documentation_id)
        return

    def is_available(self, documentation_id: str) -> bool:
        return documentation_id in self._subscribers
