#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script
Processes documents and stores them in the RAG system
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from rag.document_processor import get_document_processor
from rag.chunker import get_text_chunker
from rag.embeddings import get_embedding_generator
from rag.semantic_search import get_semantic_search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def ingest_knowledge_base(
    knowledge_path: str = "/app/knowledge",
    replace_existing: bool = True
):
    """Ingest all documents from knowledge base directory

    Args:
        knowledge_path: Path to knowledge base directory
        replace_existing: Replace existing documents in database
    """
    logger.info("=" * 80)
    logger.info("KNOWLEDGE BASE INGESTION STARTED")
    logger.info("=" * 80)

    # Initialize components
    logger.info("Initializing RAG components...")
    doc_processor = get_document_processor()
    chunker = get_text_chunker()
    embedder = get_embedding_generator()
    search = get_semantic_search()

    # Step 1: Scan and process documents
    logger.info(f"\n📁 Scanning knowledge base: {knowledge_path}")
    documents = doc_processor.scan_knowledge_base()

    if not documents:
        logger.warning("⚠️  No documents found in knowledge base!")
        return

    logger.info(f"✅ Found {len(documents)} documents")

    # Print document summary
    logger.info("\nDocuments by type:")
    doc_types = {}
    for doc in documents:
        doc_type = doc.get('document_type', 'unknown')
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

    for doc_type, count in sorted(doc_types.items()):
        logger.info(f"  - {doc_type}: {count} documents")

    # Step 2: Chunk documents
    logger.info(f"\n📝 Chunking documents...")
    all_chunks = chunker.chunk_documents(documents)

    if not all_chunks:
        logger.warning("⚠️  No chunks created from documents!")
        return

    logger.info(f"✅ Created {len(all_chunks)} chunks")

    # Print chunk statistics
    total_tokens = sum(c.get('token_count', 0) for c in all_chunks)
    avg_tokens = total_tokens / len(all_chunks) if all_chunks else 0

    logger.info(f"\nChunk statistics:")
    logger.info(f"  - Total chunks: {len(all_chunks)}")
    logger.info(f"  - Total tokens: {total_tokens:,}")
    logger.info(f"  - Average tokens per chunk: {avg_tokens:.1f}")

    # Step 3: Generate embeddings
    logger.info(f"\n🧠 Generating embeddings...")
    embedded_chunks = await embedder.embed_chunks(all_chunks)

    if not embedded_chunks:
        logger.error("❌ Failed to generate embeddings!")
        return

    logger.info(f"✅ Generated {len(embedded_chunks)} embeddings")

    # Step 4: Store in database
    logger.info(f"\n💾 Storing chunks in database...")
    stored_count = await search.store_chunks(
        embedded_chunks,
        replace_existing=replace_existing
    )

    if stored_count == 0:
        logger.error("❌ Failed to store chunks in database!")
        return

    logger.info(f"✅ Stored {stored_count} chunks in database")

    # Step 5: Verify storage
    logger.info(f"\n🔍 Verifying storage...")
    doc_count = await search.get_document_count()
    chunk_count = await search.get_chunk_count()

    logger.info(f"✅ Knowledge base now contains:")
    logger.info(f"  - {doc_count} unique documents")
    logger.info(f"  - {chunk_count} total chunks")

    # Step 6: Test semantic search
    logger.info(f"\n🧪 Testing semantic search...")
    test_queries = [
        "probiotic certifications and testing",
        "electrolyte powder minimum order quantity",
        "organic certification cost"
    ]

    for query in test_queries:
        logger.info(f"\n  Query: '{query}'")

        results = await search.similarity_search(query, top_k=3)

        if results:
            logger.info(f"  Found {len(results)} results:")
            for i, result in enumerate(results[:3], 1):
                logger.info(
                    f"    {i}. {result['document_name']} "
                    f"({result['document_type']}) - "
                    f"Similarity: {result['similarity']:.3f}"
                )
        else:
            logger.warning(f"  No results found for query")

    logger.info("\n" + "=" * 80)
    logger.info("KNOWLEDGE BASE INGESTION COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest knowledge base documents into RAG system"
    )
    parser.add_argument(
        "--path",
        default="/app/knowledge",
        help="Path to knowledge base directory"
    )
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Don't replace existing documents (append mode)"
    )

    args = parser.parse_args()

    try:
        await ingest_knowledge_base(
            knowledge_path=args.path,
            replace_existing=not args.no_replace
        )

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
