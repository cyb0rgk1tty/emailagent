"""
Text chunking module for RAG system
Uses tiktoken for accurate token counting
"""
import re
from typing import List, Dict
import logging

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TextChunker:
    """Split text into chunks with configurable size and overlap"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        encoding_name: str = "cl100k_base"  # Claude/GPT-4 encoding
    ):
        """Initialize text chunker

        Args:
            chunk_size: Maximum tokens per chunk (default from settings)
            chunk_overlap: Token overlap between chunks (default from settings)
            encoding_name: Tiktoken encoding to use
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        # Initialize tiktoken encoder
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoder = tiktoken.get_encoding(encoding_name)
                logger.info(f"Initialized tiktoken with {encoding_name} encoding")
            except Exception as e:
                logger.warning(f"Failed to load tiktoken encoding: {e}, using fallback")
                self.encoder = None
        else:
            logger.warning("tiktoken not available - using character-based fallback")
            self.encoder = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        if self.encoder:
            return len(self.encoder.encode(text))
        else:
            # Fallback: rough approximation (1 token ≈ 4 characters)
            return len(text) // 4

    def split_by_tokens(self, text: str) -> List[str]:
        """Split text into chunks by token count

        Args:
            text: Input text

        Returns:
            List of text chunks
        """
        if not text.strip():
            return []

        # If text fits in one chunk, return as-is
        token_count = self.count_tokens(text)
        if token_count <= self.chunk_size:
            return [text]

        chunks = []

        if self.encoder:
            # Use tiktoken for precise token-based splitting
            tokens = self.encoder.encode(text)
            start = 0

            while start < len(tokens):
                # Get chunk of tokens
                end = min(start + self.chunk_size, len(tokens))
                chunk_tokens = tokens[start:end]

                # Decode back to text
                chunk_text = self.encoder.decode(chunk_tokens)
                chunks.append(chunk_text)

                # Move to next chunk with overlap
                start += self.chunk_size - self.chunk_overlap

        else:
            # Fallback: character-based chunking
            char_chunk_size = self.chunk_size * 4  # Approximate conversion
            char_overlap = self.chunk_overlap * 4

            start = 0
            while start < len(text):
                end = min(start + char_chunk_size, len(text))
                chunks.append(text[start:end])
                start += char_chunk_size - char_overlap

        return chunks

    def split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into semantic chunks by paragraphs, then by tokens if needed

        Args:
            text: Input text

        Returns:
            List of text chunks
        """
        if not text.strip():
            return []

        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""
        current_tokens = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_tokens = self.count_tokens(para)

            # If single paragraph exceeds chunk size, split it by tokens
            if para_tokens > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0

                # Split large paragraph into token-based chunks
                para_chunks = self.split_by_tokens(para)
                chunks.extend(para_chunks)
                continue

            # Check if adding this paragraph exceeds chunk size
            test_chunk = current_chunk + "\n\n" + para if current_chunk else para
            test_tokens = self.count_tokens(test_chunk)

            if test_tokens > self.chunk_size:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())

                current_chunk = para
                current_tokens = para_tokens
            else:
                # Add paragraph to current chunk
                current_chunk = test_chunk
                current_tokens = test_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def split_by_sections(self, sections: List[Dict[str, str]]) -> List[Dict]:
        """Split document sections into chunks

        Args:
            sections: List of sections with 'title' and 'content'

        Returns:
            List of chunks with metadata
        """
        all_chunks = []

        for idx, section in enumerate(sections):
            title = section.get('title', '')
            content = section.get('content', '')

            if not content.strip():
                continue

            # Split section content into chunks
            content_chunks = self.split_by_paragraphs(content)

            for chunk_idx, chunk_text in enumerate(content_chunks):
                all_chunks.append({
                    'text': chunk_text,
                    'section_title': title,
                    'section_index': idx,
                    'chunk_index': chunk_idx,
                    'token_count': self.count_tokens(chunk_text)
                })

        return all_chunks

    def chunk_document(self, document: Dict) -> List[Dict]:
        """Chunk a processed document into embeddings-ready chunks

        Args:
            document: Processed document from DocumentProcessor

        Returns:
            List of chunks ready for embedding
        """
        sections = document.get('sections', [])

        if not sections:
            # Fall back to splitting full text
            full_text = document.get('full_text', '')
            chunks = self.split_by_paragraphs(full_text)

            return [{
                'text': chunk,
                'section_title': None,
                'section_index': 0,
                'chunk_index': idx,
                'token_count': self.count_tokens(chunk),
                'document_name': document.get('file_name', ''),
                'document_type': document.get('document_type', 'capability'),
                'metadata': document.get('metadata', {})
            } for idx, chunk in enumerate(chunks)]

        # Split by sections
        chunks = self.split_by_sections(sections)

        # Add document metadata to each chunk
        for chunk in chunks:
            chunk['document_name'] = document.get('file_name', '')
            chunk['document_type'] = document.get('document_type', 'capability')
            chunk['metadata'] = document.get('metadata', {})

        logger.info(
            f"Chunked document '{document.get('file_name')}': "
            f"{len(chunks)} chunks created"
        )

        return chunks

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Chunk multiple documents

        Args:
            documents: List of processed documents

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []

        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks


# Singleton instance
_chunker = None

def get_text_chunker() -> TextChunker:
    """Get singleton text chunker instance"""
    global _chunker
    if _chunker is None:
        _chunker = TextChunker()
    return _chunker
