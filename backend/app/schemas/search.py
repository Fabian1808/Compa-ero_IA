from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    source_types: list[str] | None = None


class SearchResult(BaseModel):
    id: str
    score: float
    content: str
    source_type: str
    source_id: str
    metadata: dict[str, Any]
    search_type: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
    took_ms: int


class MemoryStatsResponse(BaseModel):
    total_vectors: int
    by_source_type: dict[str, int]
    collection: str


class ReindexRequest(BaseModel):
    pass


class ReindexResponse(BaseModel):
    email: int
    task: int
    commitment: int
    followup: int
    meeting: int
    project: int

