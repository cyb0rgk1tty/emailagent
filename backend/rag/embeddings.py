"""
Embeddings generation module using OpenRouter API
Uses OpenRouter's OpenAI-compatible embeddings endpoint
"""
import asyncio
from typing import List, Dict, Optional
import logging
import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# OpenRouter embeddings configuration
OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "openai/text-embedding-3-small"
DEFAULT_EMBEDDING_DIM = 1536


class EmbeddingGenerator:
    """Generate embeddings using OpenRouter API"""

    def __init__(self, model: str = None, embedding_dim: int = None):
        """Initialize embedding generator

        Args:
            model: Model to use for embeddings (default: openai/text-embedding-3-small)
            embedding_dim: Dimension of embedding vectors (default: 1536)
        """
        self.model = model or DEFAULT_EMBEDDING_MODEL
        self.embedding_dim = embedding_dim or DEFAULT_EMBEDDING_DIM
        self.api_key = settings.OPENROUTER_API_KEY

        if not self.api_key:
            logger.error("OPENROUTER_API_KEY not set - embeddings will fail")
        else:
            logger.info(f"Initialized OpenRouter embeddings with model: {self.model}")

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

        if not self.api_key:
            logger.error("Cannot generate embedding: OPENROUTER_API_KEY not set")
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    OPENROUTER_EMBEDDINGS_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://emailagent.local",
                        "X-Title": "EmailAgent RAG"
                    },
                    json={
                        "model": self.model,
                        "input": text
                    }
                )

                if response.status_code != 200:
                    logger.error(
                        f"OpenRouter embeddings API error: {response.status_code} - {response.text}"
                    )
                    return None

                data = response.json()

                if "data" in data and len(data["data"]) > 0:
                    embedding = data["data"][0].get("embedding")
                    if embedding:
                        return embedding

                logger.error(f"Invalid response format from OpenRouter: {data}")
                return None

        except httpx.TimeoutException:
            logger.error("OpenRouter embeddings request timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            return None

    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in a single API call

        Args:
            texts: List of input texts (max 20 recommended)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        if not self.api_key:
            logger.error("Cannot generate embeddings: OPENROUTER_API_KEY not set")
            return [None] * len(texts)

        # Filter out empty texts but keep track of indices
        valid_indices = []
        valid_texts = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_indices.append(i)
                valid_texts.append(text)

        if not valid_texts:
            return [None] * len(texts)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    OPENROUTER_EMBEDDINGS_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://emailagent.local",
                        "X-Title": "EmailAgent RAG"
                    },
                    json={
                        "model": self.model,
                        "input": valid_texts
                    }
                )

                if response.status_code != 200:
                    logger.error(
                        f"OpenRouter embeddings API error: {response.status_code} - {response.text}"
                    )
                    return [None] * len(texts)

                data = response.json()

                if "data" not in data:
                    logger.error(f"Invalid response format from OpenRouter: {data}")
                    return [None] * len(texts)

                # Build result list with None for invalid texts
                results = [None] * len(texts)
                for item in data["data"]:
                    index_in_valid = item.get("index", 0)
                    if index_in_valid < len(valid_indices):
                        original_index = valid_indices[index_in_valid]
                        results[original_index] = item.get("embedding")

                return results

        except httpx.TimeoutException:
            logger.error("OpenRouter embeddings batch request timed out")
            return [None] * len(texts)
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {e}", exc_info=True)
            return [None] * len(texts)

    async def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 20
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Number of texts to process per batch (max 20 recommended)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = []

        # Process in batches to avoid rate limits and payload size limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            logger.info(
                f"Generating embeddings for batch {i//batch_size + 1} ({len(batch)} texts)"
            )

            # Use batch API for efficiency
            batch_embeddings = await self.generate_embeddings_batch(batch)
            embeddings.extend(batch_embeddings)

            # Small delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)

        successful = sum(1 for e in embeddings if e is not None)
        logger.info(f"Generated {successful}/{len(embeddings)} embeddings successfully")
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
