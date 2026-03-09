from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentUpdate, KnowledgeDocumentResponse
from app.services.document_service import get_document_service
from app.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for knowledge document CRUD operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.document_service = get_document_service()
        self.chroma_service = get_chroma_service()

    async def create_document(
        self,
        data: KnowledgeDocumentCreate,
        file_path: Optional[str] = None
    ) -> KnowledgeDocumentResponse:
        """
        Create a new knowledge document

        Args:
            data: Document metadata
            file_path: Optional path to file for processing

        Returns:
            Created document
        """
        # Validate category
        if data.category and data.category not in KnowledgeDocument.VALID_CATEGORIES:
            raise ValueError(f"Invalid category. Must be one of: {KnowledgeDocument.VALID_CATEGORIES}")

        # Create database record
        document = KnowledgeDocument(
            title=data.title,
            category=data.category,
            source=data.source,
            chunk_count=0
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        # Process file if provided
        if file_path:
            try:
                result = await self.document_service.process_file(
                    file_path=file_path,
                    title=data.title,
                    category=data.category or "general",
                    source=data.source
                )
                # Update chunk count
                document.chunk_count = result["chunk_count"]
                await self.db.commit()
                await self.db.refresh(document)
            except Exception as e:
                logger.error(f"Error processing file: {e}")
                # Clean up database record if file processing fails
                await self.db.delete(document)
                await self.db.commit()
                raise

        return KnowledgeDocumentResponse.model_validate(document)

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List documents with pagination and filtering

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            search: Search term for title/source
            category: Filter by category

        Returns:
            Dict with documents, total, page, page_size
        """
        # Build query
        query = select(KnowledgeDocument)

        # Apply filters
        conditions = []
        if search:
            conditions.append(or_(
                KnowledgeDocument.title.ilike(f"%{search}%"),
                KnowledgeDocument.source.ilike(f"%{search}%")
            ))
        if category:
            conditions.append(KnowledgeDocument.category == category)

        if conditions:
            query = query.where(*conditions)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(KnowledgeDocument.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        documents = result.scalars().all()

        return {
            "documents": [KnowledgeDocumentResponse.model_validate(d) for d in documents],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def get_document(self, document_id: str) -> Optional[KnowledgeDocumentResponse]:
        """
        Get a document by ID

        Args:
            document_id: Document ID

        Returns:
            Document or None
        """
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        return KnowledgeDocumentResponse.model_validate(document) if document else None

    async def update_document(
        self,
        document_id: str,
        data: KnowledgeDocumentUpdate
    ) -> KnowledgeDocumentResponse:
        """
        Update document metadata

        Args:
            document_id: Document ID
            data: Update data

        Returns:
            Updated document
        """
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError("Document not found")

        # Validate category if provided
        if data.category and data.category not in KnowledgeDocument.VALID_CATEGORIES:
            raise ValueError(f"Invalid category. Must be one of: {KnowledgeDocument.VALID_CATEGORIES}")

        # Update fields
        if data.title is not None:
            document.title = data.title
        if data.category is not None:
            document.category = data.category
        if data.source is not None:
            document.source = data.source

        await self.db.commit()
        await self.db.refresh(document)

        return KnowledgeDocumentResponse.model_validate(document)

    async def delete_document(self, document_id: str) -> None:
        """
        Delete a document and its chunks from ChromaDB

        Args:
            document_id: Document ID
        """
        # Get document
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError("Document not found")

        # Delete from ChromaDB
        try:
            await self.document_service.delete_document(document_id)
        except Exception as e:
            logger.error(f"Error deleting from ChromaDB: {e}")

        # Delete from database
        await self.db.execute(
            delete(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        await self.db.commit()

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics

        Returns:
            Dict with total_documents, total_chunks, categories, etc.
        """
        # Get document count
        doc_count_result = await self.db.execute(
            select(func.count()).select_from(KnowledgeDocument)
        )
        total_documents = doc_count_result.scalar() or 0

        # Get total chunks
        chunks_result = await self.db.execute(
            select(func.sum(KnowledgeDocument.chunk_count)).select_from(KnowledgeDocument)
        )
        total_chunks = chunks_result.scalar() or 0

        # Get category distribution
        category_result = await self.db.execute(
            select(
                KnowledgeDocument.category,
                func.count(KnowledgeDocument.id)
            ).group_by(KnowledgeDocument.category)
        )
        categories = {cat or "uncategorized": count for cat, count in category_result.all()}

        # Get ChromaDB stats
        chroma_stats = await self.chroma_service.get_collection_stats()

        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "categories": categories,
            "chroma_collection_count": chroma_stats.get("count", 0),
            "valid_categories": list(KnowledgeDocument.VALID_CATEGORIES)
        }
