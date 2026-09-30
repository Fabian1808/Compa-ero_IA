import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.memory.service import MemoryService
from app.models.ai_memory import AIMemory, Embedding
from app.models.user import User
from app.schemas.search import (
    MemoryStatsResponse,
    ReindexRequest,
    ReindexResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)

router = APIRouter(prefix="/search", tags=["search"])


def get_user_id(db: AsyncSession) -> str:
    """Get first user ID - in production would come from auth."""
    user_result = db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """Global semantic search across all indexed memory."""
    start_time = time.time()

    user_id = get_user_id(db)
    memory_service = MemoryService(db, user_id)
    await memory_service.initialize()

    results = await memory_service.search(
        query=request.query,
        limit=request.limit,
        source_types=request.source_types,
    )

    took_ms = int((time.time() - start_time) * 1000)

    search_results = [
        SearchResult(
            id=r["id"],
            score=r["score"],
            content=r["content"][:500],  # Truncate for response
            source_type=r["source_type"],
            source_id=r["source_id"],
            metadata=r["metadata"],
            search_type=r["search_type"],
        )
        for r in results
    ]

    return SearchResponse(
        query=request.query,
        results=search_results,
        total=len(search_results),
        took_ms=took_ms,
    )


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(db: AsyncSession = Depends(get_db)):
    """Get memory statistics for the current user."""
    user_id = get_user_id(db)
    memory_service = MemoryService(db, user_id)
    await memory_service.initialize()

    stats = await memory_service.get_stats()

    return MemoryStatsResponse(
        total_vectors=stats.get("total_vectors", 0),
        by_source_type=stats.get("by_source_type", {}),
        collection=stats.get("collection", ""),
    )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_memory(request: ReindexRequest, db: AsyncSession = Depends(get_db)):
    """Reindex all user data from SQL to Qdrant."""
    user_id = get_user_id(db)
    memory_service = MemoryService(db, user_id)

    counts = await memory_service.reindex_all()

    return ReindexResponse(
        email=counts.get("email", 0),
        task=counts.get("task", 0),
        commitment=counts.get("commitment", 0),
        followup=counts.get("followup", 0),
        meeting=counts.get("meeting", 0),
        project=counts.get("project", 0),
    )


@router.delete("/source/{source_type}/{source_id}")
async def delete_memory_source(
    source_type: str,
    source_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific memory entry by source."""
    user_id = get_user_id(db)
    memory_service = MemoryService(db, user_id)
    await memory_service.initialize()

    success = await memory_service.delete_by_source(source_type, source_id)

    if not success:
        raise HTTPException(status_code=404, detail="Memory entry not found")

    return {"success": True, "source_type": source_type, "source_id": source_id}


@router.delete("/clear")
async def clear_user_memory(db: AsyncSession = Depends(get_db)):
    """Clear all memory for the current user."""
    user_id = get_user_id(db)
    memory_service = MemoryService(db, user_id)
    await memory_service.initialize()

    success = await memory_service.qdrant.clear_user_memory(user_id)

    # Also clear SQL tracking
    # Delete embeddings
    stmt = select(Embedding).where(Embedding.user_id == user_id)
    result = await db.execute(stmt)
    embeddings = result.scalars().all()
    for emb in embeddings:
        await db.delete(emb)

    # Delete AI memories
    stmt = select(AIMemory).where(AIMemory.user_id == user_id)
    result = await db.execute(stmt)
    memories = result.scalars().all()
    for mem in memories:
        await db.delete(mem)

    await db.commit()

    return {"success": success, "message": "User memory cleared"}
