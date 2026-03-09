from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting documents into chunks using LangChain"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        # Ensure chunk_overlap is not larger than chunk_size
        self.chunk_overlap = min(chunk_overlap, chunk_size - 1) if chunk_size > 1 else 0

        # LangChain RecursiveCharacterTextSplitter
        # 默认分隔符按优先级排序
        default_separators = ["\n\n", "\n", "。", ".", " ", ""]
        self.splitter = RecursiveCharacterTextSplitter(
            separators=separators or default_separators,
            chunk_size=chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            keep_separator=True  # 保持分隔符以维护语义
        )

    def chunk_text(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata

        Note: Metadata structure changed from old implementation:
        - Removed: start_pos, end_pos (not used by document_service)
        - Kept: document_id, chunk_index, char_count

        Returns:
            List of chunks with text, metadata, and id
        """
        if not text:
            return []

        # 使用 LangChain 切分器
        texts = self.splitter.split_text(text)

        chunks = []
        for idx, chunk_text in enumerate(texts):
            stripped_text = chunk_text.strip()
            if stripped_text:
                chunks.append({
                    "id": f"{document_id}_chunk_{idx}",
                    "text": stripped_text,
                    "metadata": {
                        "document_id": document_id,
                        "chunk_index": idx,
                        "char_count": len(stripped_text)
                    }
                })

        logger.info(f"Split into {len(chunks)} chunks")
        return chunks

    def chunk_by_semantic_units(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Split text by semantic units (paragraphs)

        For LangChain, we use the same method as chunk_text
        since RecursiveCharacterTextSplitter already handles
        semantic boundaries well.
        """
        return self.chunk_text(text, document_id)


# Singleton
_chunking_service = None


def get_chunking_service() -> ChunkingService:
    """Get or create chunking service"""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
