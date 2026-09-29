from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


@dataclass
class SyncResult:
    items_processed: int = 0
    items_created: int = 0
    items_updated: int = 0
    items_deleted: int = 0
    errors: list[str] = None
    next_cursor: str | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class Connector(ABC, Generic[T]):
    """Base interface for all connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def required_scopes(self) -> list[str]:
        pass

    @abstractmethod
    async def authenticate(self, credentials: dict) -> bool:
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        pass

    @abstractmethod
    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        pass

    @abstractmethod
    async def get_item(self, item_id: str) -> T | None:
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 50) -> list[T]:
        pass