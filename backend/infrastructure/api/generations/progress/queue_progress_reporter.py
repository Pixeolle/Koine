from backend.application.ports.progress_reporter import ProgressReporter, ProgressEventType
from backend.domain.services.progress_broker import ProgressBroker


class QueueProgressReporter(ProgressReporter):

    def __init__(self, documentation_id: str, broker: ProgressBroker):
        self._documentation_id = documentation_id
        self._broker = broker

    async def report(self, event_type: ProgressEventType, **data) -> None:
        await self._broker.publish(self._documentation_id, {"type": event_type, **data})
        return
