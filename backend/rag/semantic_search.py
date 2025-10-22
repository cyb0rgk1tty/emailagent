"""
Semantic search module using pgvector
Stores and retrieves document embeddings for RAG
"""
from typing import List, Dict, Optional
import logging
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from models.database import DocumentEmbedding
from rag.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)


class SemanticSearch:
    """Semantic search using pgvector similarity"""

    def __init__(self, top_k: int = 10):
        """Initialize semantic search

        Args:
            top_k: Number of top results to return
        """
        self.top_k = top_k
        self.embedder = get_embedding_generator()

    async def store_chunk(
        self,
        session: AsyncSession,
        chunk: Dict
    ) -> Optional[DocumentEmbedding]:
        """Store a document chunk with its embedding

        Args:
            session: Database session
            chunk: Chunk data with embedding

        Returns:
            Created DocumentEmbedding record
        """
        try:
            embedding_record = DocumentEmbedding(
                document_name=chunk.get('document_name', ''),
                document_type=chunk.get('document_type', 'capability'),
                section_title=chunk.get('section_title'),
                chunk_text=chunk.get('text', ''),
                chunk_index=chunk.get('chunk_index', 0),
                embedding=chunk.get('embedding'),
                doc_metadata=chunk.get('metadata', {}),
                is_active=True,
                version=1
            )

            session.add(embedding_record)
            await session.flush()

            logger.debug(f"Stored chunk: {embedding_record.document_name} "
                        f"(section: {embedding_record.section_title})")

            return embedding_record

        except Exception as e:
            logger.error(f"Error storing chunk: {e}")
            return None

    async def store_chunks(
        self,
        chunks: List[Dict],
        replace_existing: bool = False
    ) -> int:
        """Store multiple document chunks in database

        Args:
            chunks: List of chunks with embeddings
            replace_existing: If True, deactivate existing chunks for these documents

        Returns:
            Number of chunks stored
        """
        if not chunks:
            return 0

        stored_count = 0

        async with get_db_session() as session:
            try:
                # Optionally deactivate existing chunks
                if replace_existing:
                    document_names = list(set(c.get('document_name') for c in chunks))

                    for doc_name in document_names:
                        result = await session.execute(
                            select(DocumentEmbedding).where(
                                DocumentEmbedding.document_name == doc_name,
                                DocumentEmbedding.is_active == True
                            )
                        )
                        existing_chunks = result.scalars().all()

                        for chunk in existing_chunks:
                            chunk.is_active = False

                        logger.info(f"Deactivated {len(existing_chunks)} existing chunks "
                                  f"for {doc_name}")

                # Store new chunks
                for chunk in chunks:
                    record = await self.store_chunk(session, chunk)
                    if record:
                        stored_count += 1

                await session.commit()

                logger.info(f"Stored {stored_count}/{len(chunks)} chunks in database")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error storing chunks: {e}")

        return stored_count

    async def similarity_search(
        self,
        query: str,
        top_k: int = None,
        document_type: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """Perform semantic similarity search

        Args:
            query: Search query text
            top_k: Number of results to return (default: self.top_k)
            document_type: Filter by document type
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of matching chunks with similarity scores
        """
        k = top_k or self.top_k

        try:
            # Generate query embedding
            query_embedding = await self.embedder.generate_query_embedding(query)

            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            async with get_db_session() as session:
                # Build similarity search query
                # Using cosine similarity: 1 - (embedding <=> query_embedding)
                similarity_expr = text("1 - (embedding <=> :query_embedding)")

                query_stmt = (
                    select(
                        DocumentEmbedding,
                        similarity_expr.label('similarity')
                    )
                    .where(DocumentEmbedding.is_active == True)
                    .order_by(text("similarity DESC"))
                    .limit(k)
                )

                # Add document type filter if specified
                if document_type:
                    query_stmt = query_stmt.where(
                        DocumentEmbedding.document_type == document_type
                    )

                # Execute query with parameters
                result = await session.execute(
                    query_stmt,
                    {"query_embedding": str(query_embedding)}
                )

                rows = result.all()

                # Format results
                results = []
                for row in rows:
                    chunk, similarity = row

                    # Filter by minimum similarity
                    if similarity < min_similarity:
                        continue

                    results.append({
                        'text': chunk.chunk_text,
                        'document_name': chunk.document_name,
                        'document_type': chunk.document_type,
                        'section_title': chunk.section_title,
                        'chunk_index': chunk.chunk_index,
                        'similarity': float(similarity),
                        'metadata': chunk.doc_metadata
                    })

                logger.info(f"Similarity search returned {len(results)} results for: {query[:50]}")
                return results

        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []

    async def get_document_count(self) -> int:
        """Get count of active documents in knowledge base

        Returns:
            Number of unique active documents
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(DocumentEmbedding.document_name)
                    .where(DocumentEmbedding.is_active == True)
                    .distinct()
                )

                documents = result.scalars().all()
                return len(documents)

        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    async def get_chunk_count(self) -> int:
        """Get count of active chunks in knowledge base

        Returns:
            Number of active chunks
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(DocumentEmbedding)
                    .where(DocumentEmbedding.is_active == True)
                )

                chunks = result.scalars().all()
                return len(chunks)

        except Exception as e:
            logger.error(f"Error getting chunk count: {e}")
            return 0

    async def delete_document(self, document_name: str) -> int:
        """Delete a document from the knowledge base

        Args:
            document_name: Name of document to delete

        Returns:
            Number of chunks deleted
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(DocumentEmbedding).where(
                        DocumentEmbedding.document_name == document_name,
                        DocumentEmbedding.is_active == True
                    )
                )

                chunks = result.scalars().all()

                for chunk in chunks:
                    chunk.is_active = False

                await session.commit()

                logger.info(f"Deleted {len(chunks)} chunks for document: {document_name}")
                return len(chunks)

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return 0

    async def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 3000,
        document_types: Optional[List[str]] = None
    ) -> str:
        """Get relevant context for a query, formatted for RAG

        Args:
            query: Search query
            max_tokens: Maximum tokens to include in context
            document_types: Filter by document types

        Returns:
            Formatted context string
        """
        # Perform searches across document types
        all_results = []

        if document_types:
            for doc_type in document_types:
                results = await self.similarity_search(
                    query=query,
                    top_k=5,
                    document_type=doc_type
                )
                all_results.extend(results)
        else:
            all_results = await self.similarity_search(query=query, top_k=self.top_k)

        # Sort by similarity
        all_results.sort(key=lambda x: x['similarity'], reverse=True)

        # Build context string
        context_parts = []
        current_tokens = 0

        for result in all_results:
            chunk_text = result['text']
            doc_name = result['document_name']
            section = result.get('section_title', 'N/A')

            # Estimate tokens (rough: 1 token ≈ 4 characters)
            chunk_tokens = len(chunk_text) // 4

            if current_tokens + chunk_tokens > max_tokens:
                break

            # Format chunk with metadata
            formatted_chunk = f"""
--- Source: {doc_name} | Section: {section} | Similarity: {result['similarity']:.3f} ---
{chunk_text}
"""

            context_parts.append(formatted_chunk)
            current_tokens += chunk_tokens

        if not context_parts:
            return "No relevant context found in knowledge base."

        context = "\n\n".join(context_parts)

        logger.info(f"Generated context: {len(context_parts)} chunks, ~{current_tokens} tokens")
        return context


# Singleton instance
_search = None

def get_semantic_search(top_k: int = 10) -> SemanticSearch:
    """Get semantic search instance

    Args:
        top_k: Number of top results to return

    Returns:
        SemanticSearch instance
    """
    global _search
    if _search is None:
        _search = SemanticSearch(top_k=top_k)
    return _search
