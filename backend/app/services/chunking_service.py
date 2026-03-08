from typing import List, Dict, Any
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting documents into chunks for embedding"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", ".", " ", ""]

    def chunk_text(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata

        Returns:
            List of chunks with text, metadata, and id
        """
        if not text:
            return []

        chunks = []
        current_position = 0
        chunk_index = 0

        while current_position < len(text):
            end_position = min(current_position + self.chunk_size, len(text))
            split_pos = self._find_split_position(text, current_position, end_position)

            # Ensure we make progress - if split_pos didn't move forward, use end_position
            if split_pos <= current_position:
                split_pos = end_position

            chunk_text = text[current_position:split_pos].strip()

            if chunk_text:
                chunks.append({
                    "id": f"{document_id}_chunk_{chunk_index}",
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "start_pos": current_position,
                        "end_pos": split_pos
                    }
                })
                chunk_index += 1

            # Move to next chunk with overlap
            # Ensure we always move forward at least 1 character
            next_position = split_pos - self.chunk_overlap
            current_position = max(next_position, current_position + 1)

            # If we've reached the end, stop
            if current_position >= len(text):
                break

        logger.info(f"Split into {len(chunks)} chunks")
        return chunks

    def _find_split_position(self, text: str, start: int, end: int) -> int:
        """Find the best position to split text"""
        if end >= len(text):
            return end

        for sep in self.separators:
            split_pos = text.rfind(sep, start, end)
            if split_pos != -1:
                return split_pos + len(sep)

        return end

    def chunk_by_semantic_units(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Split text by semantic units (paragraphs)

        Better for legal documents with clear structure
        """
        chunks = []
        paragraphs = re.split(r'\n\n+', text)

        current_chunk = ""
        chunk_index = 0
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_len = len(para)

            if para_len > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, document_id, chunk_index
                    ))
                    chunk_index += 1
                    current_chunk = ""
                    current_length = 0

                # Split long paragraph
                sub_chunks = self.chunk_text(para, document_id)
                chunks.extend(sub_chunks)
                continue

            if current_length + para_len > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk, document_id, chunk_index
                ))
                chunk_index += 1
                current_chunk = para
                current_length = para_len
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
                current_length += para_len + (2 if current_chunk != para else 0)

        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, document_id, chunk_index
            ))

        return chunks

    def _create_chunk(self, text: str, document_id: str, index: int) -> Dict[str, Any]:
        """Create a chunk dict with metadata"""
        return {
            "id": f"{document_id}_chunk_{index}",
            "text": text,
            "metadata": {
                "document_id": document_id,
                "chunk_index": index,
                "char_count": len(text)
            }
        }


# Singleton
_chunking_service = None


def get_chunking_service() -> ChunkingService:
    """Get or create chunking service"""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
