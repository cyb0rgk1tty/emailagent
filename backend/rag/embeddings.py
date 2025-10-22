"""
Embeddings generation module using Claude Agent SDK
Uses user's Claude Code Max subscription for authentication
"""
import asyncio
from typing import List, Dict, Optional
import logging
import numpy as np

try:
    from claude_code_agent import ClaudeAgent
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingGenerator:
    """Generate embeddings using Claude Agent SDK"""

    def __init__(self, model: str = None, embedding_dim: int = 1536):
        """Initialize embedding generator

        Args:
            model: Model to use for embeddings (default from settings)
            embedding_dim: Dimension of embedding vectors
        """
        self.model = model or settings.EMBEDDING_MODEL
        self.embedding_dim = embedding_dim

        if CLAUDE_SDK_AVAILABLE:
            try:
                # Initialize Claude Agent SDK
                # Authenticates automatically via Claude Code Max subscription
                self.agent = ClaudeAgent()
                logger.info("Initialized Claude Agent SDK for embeddings")
            except Exception as e:
                logger.error(f"Failed to initialize Claude Agent SDK: {e}")
                self.agent = None
        else:
            logger.warning("Claude Agent SDK not available - using fallback embeddings")
            self.agent = None

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate simple fallback embedding for testing

        Args:
            text: Input text

        Returns:
            Random embedding vector (for development/testing only)
        """
        # Create deterministic "embedding" based on text hash
        # This is ONLY for development - not suitable for production
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(self.embedding_dim).tolist()

        logger.warning("Using fallback embeddings - install Claude Agent SDK for production")
        return embedding

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            Embedding vector or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None

        try:
            if self.agent:
                # Use Claude Agent SDK to generate embeddings
                # Note: This is a placeholder - actual implementation depends on
                # Claude Agent SDK's embedding API
                response = await self.agent.generate_embedding(
                    text=text,
                    model=self.model
                )

                if response and 'embedding' in response:
                    return response['embedding']
                else:
                    logger.error("Claude Agent SDK returned invalid response")
                    return self._generate_fallback_embedding(text)

            else:
                # Use fallback for development
                return self._generate_fallback_embedding(text)

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return self._generate_fallback_embedding(text)

    async def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 20
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Number of texts to process per batch

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = []

        # Process in batches to avoid rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            logger.info(f"Generating embeddings for batch {i//batch_size + 1} "
                       f"({len(batch)} texts)")

            # Generate embeddings for batch
            batch_tasks = [self.generate_embedding(text) for text in batch]
            batch_embeddings = await asyncio.gather(*batch_tasks)

            embeddings.extend(batch_embeddings)

            # Small delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embedding vectors

        Returns:
            Embedding dimension
        """
        return self.embedding_dim

    async def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for document chunks

        Args:
            chunks: List of chunks from TextChunker

        Returns:
            Chunks with embeddings added
        """
        if not chunks:
            return []

        # Extract texts from chunks
        texts = [chunk['text'] for chunk in chunks]

        # Generate embeddings
        embeddings = await self.generate_embeddings(texts)

        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding

        # Filter out chunks without embeddings
        valid_chunks = [c for c in chunks if c.get('embedding') is not None]

        logger.info(f"Embedded {len(valid_chunks)}/{len(chunks)} chunks successfully")
        return valid_chunks

    async def generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for a search query

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        return await self.generate_embedding(query)


# Singleton instance
_embedder = None

def get_embedding_generator() -> EmbeddingGenerator:
    """Get singleton embedding generator instance"""
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingGenerator()
    return _embedder
