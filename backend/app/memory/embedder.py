from typing import List, Optional
from app.ai.provider import AIProvider
from app.config import settings
import hashlib


class Embedder:
    """Service for creating and managing embeddings."""

    def __init__(self, ai_provider: AIProvider):
        self.provider = ai_provider
        self.model = settings.ollama_embed_model

    def _content_hash(self, text: str) -> str:
        """Generate SHA256 hash of content for deduplication."""
        return hashlib.sha256(text.encode()).hexdigest()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts."""
        if not texts:
            return []
        
        response = await self.provider.create_embeddings(texts)
        return response.embeddings

    async def embed_single(self, text: str) -> List[float]:
        """Create embedding for a single text."""
        embeddings = await self.embed_texts([text])
        return embeddings[0] if embeddings else []

    async def embed_and_store(
        self,
        texts: List[str],
        metadata: List[dict],
        user_id: str,
        vector_store
    ) -> List[str]:
        """Embed texts and store in vector store with metadata."""
        if not texts:
            return []

        # Create embeddings
        embeddings = await self.embed_texts(texts)
        
        # Prepare payloads with metadata
        payloads = []
        ids = []
        for i, (text, meta) in enumerate(zip(texts, metadata)):
            content_hash = self._content_hash(text)
            payload = {
                "user_id": user_id,
                "content": text,
                "content_hash": content_hash,
                **meta,
            }
            payloads.append(payload)
            ids.append(f"{user_id}_{content_hash}")

        # Upsert to vector store
        vector_store.upsert_embeddings(embeddings, payloads, ids)
        
        return ids

    async def search_similar(
        self,
        query: str,
        user_id: str,
        vector_store,
        limit: int = 10,
        score_threshold: float = 0.7,
        filter_metadata: dict = None
    ) -> List[dict]:
        """Search for similar content."""
        query_embedding = await self.embed_single(query)
        
        if not query_embedding:
            return []

        filter_conditions = {"user_id": user_id}
        if filter_metadata:
            filter_conditions.update(filter_metadata)

        results = vector_store.search(
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions=filter_conditions
        )

        return results