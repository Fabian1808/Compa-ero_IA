from __future__ import annotations
import hashlib
from typing import TYPE_CHECKING

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

if TYPE_CHECKING:
    from app.ai.provider import AIProvider
from app.config import settings


class QdrantService:
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider
        self.client: QdrantClient | None = None
        self.collection_name = "ai_workmate_memory"

    async def initialize(self) -> None:
        """Initialize Qdrant client and create collection if not exists."""
        self.client = QdrantClient(path=settings.qdrant_path)

        # Check if collection exists
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                await self._create_collection()
        except Exception:
            # If any error, try to create collection
            await self._create_collection()

    async def _create_collection(self) -> None:
        """Create the memory collection with vector config."""
        if not self.client:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=768,  # nomic-embed-text dimensions
                distance=qdrant_models.Distance.COSINE,
            ),
            optimizers_config=qdrant_models.OptimizersConfigDiff(
                indexing_threshold=10000,
            ),
        )

        # Create payload indexes for filtering
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="user_id",
            field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
        )
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="source_type",
            field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
        )
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="source_id",
            field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
        )
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="created_at",
            field_schema=qdrant_models.PayloadSchemaType.DATETIME,
        )

    @staticmethod
    def _generate_vector_id(user_id: str, source_type: str, source_id: str) -> str:
        """Generate deterministic vector ID for upsert operations."""
        content = f"{user_id}:{source_type}:{source_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    @staticmethod
    def _generate_content_hash(content: str) -> str:
        """Generate hash for content deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def upsert_memory(
        self,
        user_id: str,
        content: str,
        source_type: str,
        source_id: str,
        metadata: dict | None = None,
    ) -> str:
        """Upsert a memory entry with its embedding."""
        if not self.client:
            await self.initialize()

        # Generate embedding
        embedding_response = await self.ai_provider.create_embeddings([content])
        embedding = embedding_response.embeddings[0]

        vector_id = self._generate_vector_id(user_id, source_type, source_id)
        content_hash = self._generate_content_hash(content)

        point = qdrant_models.PointStruct(
            id=vector_id,
            vector=embedding,
            payload={
                "user_id": user_id,
                "content": content,
                "source_type": source_type,
                "source_id": source_id,
                "content_hash": content_hash,
                "metadata": metadata or {},
                "model": self.ai_provider._config.embed_model,
            },
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

        return vector_id

    async def delete_memory(self, user_id: str, source_type: str, source_id: str) -> bool:
        """Delete a memory entry by source."""
        if not self.client:
            return False

        vector_id = self._generate_vector_id(user_id, source_type, source_id)

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.PointIdsList(points=[vector_id]),
            )
        except Exception:
            return False
        return True

    async def search(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
        source_types: list[str] | None = None,
        score_threshold: float = 0.7,
    ) -> list[dict]:
        """Hybrid search: semantic + keyword filter."""
        if not self.client:
            await self.initialize()

        # Generate query embedding
        embedding_response = await self.ai_provider.create_embeddings([query])
        query_embedding = embedding_response.embeddings[0]

        # Build filter
        must_conditions = [
            qdrant_models.FieldCondition(
                key="user_id",
                match=qdrant_models.MatchValue(value=user_id),
            ),
        ]

        if source_types:
            must_conditions.append(
                qdrant_models.FieldCondition(
                    key="source_type",
                    match=qdrant_models.MatchAny(any=source_types),
                ),
            )

        search_filter = qdrant_models.Filter(must=must_conditions)

        # Semantic search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit * 2,  # Get more for hybrid re-ranking
            score_threshold=score_threshold,
            with_payload=True,
        )

        # Also do keyword search for exact matches
        keyword_results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=search_filter,
            limit=limit * 2,
            with_payload=True,
        )

        # Combine and deduplicate
        seen_ids = set()
        combined = []

        for point in results:
            if point.id not in seen_ids:
                seen_ids.add(point.id)
                combined.append({
                    "id": point.id,
                    "score": point.score,
                    "content": point.payload.get("content", ""),
                    "source_type": point.payload.get("source_type", ""),
                    "source_id": point.payload.get("source_id", ""),
                    "metadata": point.payload.get("metadata", {}),
                    "search_type": "semantic",
                })

        # Add keyword matches (simple contains check)
        query_lower = query.lower()
        for point in keyword_results[0]:
            if point.id not in seen_ids:
                content = point.payload.get("content", "").lower()
                if query_lower in content:
                    seen_ids.add(point.id)
                    combined.append({
                        "id": point.id,
                        "score": 0.95,  # High score for exact keyword match
                        "content": point.payload.get("content", ""),
                        "source_type": point.payload.get("source_type", ""),
                        "source_id": point.payload.get("source_id", ""),
                        "metadata": point.payload.get("metadata", {}),
                        "search_type": "keyword",
                    })

        # Sort by score and limit
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:limit]

    async def get_stats(self, user_id: str) -> dict:
        """Get memory statistics for a user."""
        if not self.client:
            await self.initialize()

        try:
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="user_id",
                            match=qdrant_models.MatchValue(value=user_id),
                        ),
                    ],
                ),
                exact=True,
            )
        except Exception:
            return {
                "total_vectors": 0,
                "by_source_type": {},
                "collection": self.collection_name,
            }

        # Count by source type
        source_types: list[str] = [
            "email", "task", "commitment", "followup",
            "meeting", "document", "chat"
        ]
        by_source: dict[str, int] = {}

        for st in source_types:
            try:
                cnt = self.client.count(
                    collection_name=self.collection_name,
                    count_filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="user_id",
                                match=qdrant_models.MatchValue(value=user_id)
                            ),
                            qdrant_models.FieldCondition(
                                key="source_type",
                                match=qdrant_models.MatchValue(value=st)
                            ),
                        ],
                    ),
                    exact=True,
                )
                by_source[st] = cnt.count
            except Exception:
                by_source[st] = 0

        return {
            "total_vectors": count_result.count,
            "by_source_type": by_source,
            "collection": self.collection_name,
        }

    async def clear_user_memory(self, user_id: str) -> bool:
        """Delete all memory for a user."""
        if not self.client:
            return False

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="user_id",
                                match=qdrant_models.MatchValue(value=user_id),
                            ),
                        ],
                    ),
                ),
            )
        except Exception:
            return False
        return True

    async def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            if not self.client:
                await self.initialize()
            _ = self.client.get_collections()
        except Exception:
            return False
        return True

