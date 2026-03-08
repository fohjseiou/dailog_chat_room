from typing import List, Dict, Any, Optional
from pathlib import Path
import pypdf
import docx
import logging

from app.services.chunking_service import get_chunking_service
from app.services.embedding_service import get_embedding_service
from app.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for processing and uploading documents to knowledge base"""

    def __init__(self):
        self.chunking_service = get_chunking_service()
        self.embedding_service = get_embedding_service()
        self.chroma_service = get_chroma_service()

    async def process_file(
        self,
        file_path: str,
        title: str,
        category: str,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a file and add to knowledge base

        Args:
            file_path: Path to the file
            title: Document title
            category: One of 'law', 'case', 'contract', 'interpretation'
            source: Optional source information

        Returns:
            Document info with chunk count
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        # Extract text based on file type
        if suffix == '.pdf':
            text = self._extract_text_from_pdf(path)
        elif suffix == '.docx':
            text = self._extract_text_from_docx(path)
        elif suffix == '.txt':
            text = path.read_text(encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        if not text or len(text.strip()) < 10:
            raise ValueError("Document appears to be empty or too short")

        # Generate document ID
        document_id = f"{category}_{path.stem}_{hash(text)}"

        # Chunk the text
        chunks = self.chunking_service.chunk_by_semantic_units(text, document_id)

        # Generate embeddings for all chunks
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embedding_service.generate_embeddings_batch(texts)

        # Prepare metadata for each chunk
        metadatas = [
            {
                **chunk["metadata"],
                "title": title,
                "category": category,
                "source": source or path.name
            }
            for chunk in chunks
        ]

        # Store in ChromaDB
        ids = [chunk["id"] for chunk in chunks]
        await self.chroma_service.add_documents(texts, embeddings, metadatas, ids)

        logger.info(f"Processed {path.name}: {len(chunks)} chunks added")

        return {
            "document_id": document_id,
            "title": title,
            "category": category,
            "chunk_count": len(chunks),
            "source": source or path.name
        }

    def _extract_text_from_pdf(self, path: Path) -> str:
        """Extract text from PDF file"""
        try:
            reader = pypdf.PdfReader(path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def _extract_text_from_docx(self, path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(path)
            text_parts = []
            for para in doc.paragraphs:
                if para.text:
                    text_parts.append(para.text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            raise

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search knowledge base with semantic query"""
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Build where filter
        where_filter = {"category": category} if category else None

        # Search ChromaDB
        results = await self.chroma_service.search(
            query_embedding=query_embedding,
            n_results=n_results,
            where=where_filter
        )

        # Format results
        formatted_results = []
        for i, doc in enumerate(results.get("documents", [])):
            metadata = results.get("metadatas", [])[i]
            distance = results.get("distances", [])[i]
            formatted_results.append({
                "text": doc,
                "metadata": metadata,
                "score": 1 - distance,  # Convert distance to similarity score
                "distance": distance
            })

        return formatted_results

    async def delete_document(self, document_id: str) -> None:
        """Delete a document and all its chunks"""
        await self.chroma_service.delete_by_document_id(document_id)
        logger.info(f"Deleted document {document_id}")


# Singleton
_document_service = None


def get_document_service() -> DocumentService:
    """Get or create document service"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
