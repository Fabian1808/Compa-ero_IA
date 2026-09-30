from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Optional, Dict, Any
import uuid
import hashlib
import json
from app.config import settings
from app.ai.provider import AIProvider


class VectorStore:
    """Qdrant vector store for semantic memory."""

    def __init__(self, path: str = None):
        self.path = path or settings.qdrant_path
        self._client: Optional[QdrantClient] = None
        self.collection_name = "ai_workmate_memory"

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(path=self.path)
            self._ensure_collection()
        return self._client

    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=768,  # nomic-embed-text dimensions
                    distance=Distance.COSINE,
                ),
            )

    def upsert_embeddings(
        self,
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: List[str] = None
    ) -> bool:
        """Insert or update embeddings with payloads."""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in embeddings]

        points = [
            PointStruct(
                id=id_,
                vector=vector,
                payload=payload
            )
            for id_, vector, payload in zip(ids, embeddings, payloads)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )
        return True

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        query_filter = None
        if filter_conditions:
            must_conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_conditions.items()
            ]
            query_filter = Filter(must=must_conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
            with_vectors=False,
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    def delete(self, ids: List[str]) -> bool:
        """Delete embeddings by IDs."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=ids),
            wait=True
        )
        return True

    def delete_by_filter(self, filter_conditions: Dict[str, Any]) -> bool:
        """Delete embeddings matching filter."""
        must_conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filter_conditions.items()
        ]
        query_filter = Filter(must=must_conditions)

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=query_filter),
            wait=True
        )
        return True

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        info = self.client.get_collection(self.collection_name)
        return {
            "name": info.config.params.vectors.size,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
        }

    def scroll_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Scroll through all points."""
        results = []
        offset = None
        while True:
            records, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            results.extend([
                {"id": r.id, "payload": r.payload}
                for r in records
            ])
            if next_offset is None:
                break
            offset = next_offset
        return results