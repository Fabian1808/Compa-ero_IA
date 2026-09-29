from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Awaitable
from blinker import Signal
from app.events.events import EventType, Event


class EventBus:
    def __init__(self):
        self._signals: dict[EventType, Signal] = {}

    def _get_signal(self, event_type: EventType) -> Signal:
        if event_type not in self._signals:
            self._signals[event_type] = Signal(event_type.value)
        return self._signals[event_type]

    def on(self, event_type: EventType, handler: Callable[[Event], Awaitable[None]]) -> None:
        signal = self._get_signal(event_type)
        signal.connect(handler)

    def off(self, event_type: EventType, handler: Callable[[Event], Awaitable[None]]) -> None:
        if event_type in self._signals:
            self._signals[event_type].disconnect(handler)

    async def emit(self, event_type: EventType, payload: dict[str, Any], user_id: str | None = None, correlation_id: str | None = None) -> None:
        event = Event(
            type=event_type,
            payload=payload,
            user_id=user_id,
            correlation_id=correlation_id,
        )
        signal = self._get_signal(event_type)
        await signal.send_async(event)


event_bus = EventBus()