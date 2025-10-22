"""
Knowledge Base API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from database import get_db
from models.database import DocumentEmbedding
from models.schemas import DocumentInfo, RAGQuery, RAGResponse, RAGResult

router = APIRouter()


@router.get("/documents")
async def get_documents(db: AsyncSession = Depends(get_db)):
    """Get all documents in knowledge base"""
    # Get document summary stats
    result = await db.execute(
        select(
            DocumentEmbedding.document_name,
            DocumentEmbedding.document_type,
            DocumentEmbedding.version,
            func.count(DocumentEmbedding.id).label('chunk_count'),
            func.max(DocumentEmbedding.updated_at).label('last_updated'),
            DocumentEmbedding.is_active
        )
        .where(DocumentEmbedding.is_active == True)
        .group_by(
            DocumentEmbedding.document_name,
            DocumentEmbedding.document_type,
            DocumentEmbedding.version,
            DocumentEmbedding.is_active
        )
    )

    documents = []
    for row in result.all():
        documents.append(DocumentInfo(
            document_name=row.document_name,
            document_type=row.document_type,
            chunk_count=row.chunk_count,
            version=row.version,
            last_updated=row.last_updated,
            is_active=row.is_active
        ))

    return {"documents": documents}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "faq",
    db: AsyncSession = Depends(get_db)
):
    """Upload a new document to knowledge base"""
    # Placeholder - actual implementation in Phase 2
    return {
        "message": "Document upload will be fully implemented in Phase 2",
        "filename": file.filename,
        "document_type": document_type
    }


@router.post("/reindex")
async def reindex_knowledge_base(db: AsyncSession = Depends(get_db)):
    """Re-index all documents in knowledge base"""
    # Placeholder - actual implementation in Phase 2
    return {
        "message": "Knowledge base re-indexing will be implemented in Phase 2",
        "status": "pending"
    }


@router.post("/query", response_model=RAGResponse)
async def query_knowledge_base(
    query: RAGQuery,
    db: AsyncSession = Depends(get_db)
):
    """Query knowledge base using RAG"""
    # Placeholder - actual RAG implementation in Phase 2
    # For now, return empty results
    return RAGResponse(
        query=query.query,
        results=[],
        total_results=0
    )


@router.delete("/documents/{document_name}")
async def delete_document(
    document_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a document (soft delete)"""
    result = await db.execute(
        select(DocumentEmbedding).where(DocumentEmbedding.document_name == document_name)
    )
    embeddings = result.scalars().all()

    if not embeddings:
        raise HTTPException(status_code=404, detail="Document not found")

    for embedding in embeddings:
        embedding.is_active = False

    await db.commit()

    return {
        "message": f"Document '{document_name}' deactivated successfully",
        "chunks_affected": len(embeddings)
    }


@router.get("/stats")
async def get_knowledge_stats(db: AsyncSession = Depends(get_db)):
    """Get knowledge base statistics"""
    total_docs_result = await db.execute(
        select(func.count(func.distinct(DocumentEmbedding.document_name)))
        .where(DocumentEmbedding.is_active == True)
    )
    total_docs = total_docs_result.scalar() or 0

    total_chunks_result = await db.execute(
        select(func.count(DocumentEmbedding.id))
        .where(DocumentEmbedding.is_active == True)
    )
    total_chunks = total_chunks_result.scalar() or 0

    by_type_result = await db.execute(
        select(DocumentEmbedding.document_type, func.count(func.distinct(DocumentEmbedding.document_name)))
        .where(DocumentEmbedding.is_active == True)
        .group_by(DocumentEmbedding.document_type)
    )
    by_type = {row[0]: row[1] for row in by_type_result.all()}

    return {
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "documents_by_type": by_type
    }
