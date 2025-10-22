"""
RAG (Retrieval-Augmented Generation) module
Handles document processing, embeddings, and semantic search
"""

from .semantic_search import get_semantic_search, SemanticSearch
from .embeddings import get_embedding_generator, EmbeddingGenerator
from .chunker import TextChunker
from .document_processor import DocumentProcessor

__all__ = [
    'get_semantic_search',
    'SemanticSearch',
    'get_embedding_generator',
    'EmbeddingGenerator',
    'TextChunker',
    'DocumentProcessor',
]
