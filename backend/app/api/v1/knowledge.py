from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentResponse,
    DocumentListResponse,
    KnowledgeStatsResponse
)
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List knowledge documents with pagination and filtering

    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (max 100)
    - **search**: Search term for title/source
    - **category**: Filter by category (law, case, contract, interpretation)
    """
    service = KnowledgeService(db)
    return await service.list_documents(page, page_size, search, category)


@router.post("/documents", response_model=KnowledgeDocumentResponse)
async def create_document(
    data: KnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new knowledge document (metadata only, no file)

    - **title**: Document title
    - **category**: Document category (law, case, contract, interpretation)
    - **source**: Optional source information
    """
    service = KnowledgeService(db)

    try:
        result = await service.create_document(data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/upload", response_model=KnowledgeDocumentResponse)
async def upload_document(
    title: str = Form(..., min_length=1, max_length=255),
    category: Optional[str] = Form(None, pattern="^(law|case|contract|interpretation)$"),
    source: Optional[str] = Form(None, max_length=500),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload a document to the knowledge base

    Supported formats: PDF, DOCX, TXT

    - **title**: Document title
    - **category**: Document category (law, case, contract, interpretation)
    - **source**: Optional source information
    - **file**: File to upload
    """
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".txt"}
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Create document data
        document_data = KnowledgeDocumentCreate(
            title=title,
            category=category,
            source=source
        )

        # Process and create document
        service = KnowledgeService(db)
        result = await service.create_document(document_data, temp_path)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process document")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a document by ID

    - **document_id**: Document UUID
    """
    service = KnowledgeService(db)
    document = await service.get_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.put("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
async def update_document(
    document_id: str,
    data: KnowledgeDocumentUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update document metadata

    - **document_id**: Document UUID
    - **data**: Update data (title, category, source)
    """
    service = KnowledgeService(db)

    try:
        result = await service.update_document(document_id, data)
        return result
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a document and all its chunks

    - **document_id**: Document UUID
    """
    service = KnowledgeService(db)

    try:
        await service.delete_document(document_id)
        return {"message": "Document deleted successfully"}
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get knowledge base statistics

    Returns document counts, chunk counts, category distribution, etc.
    """
    service = KnowledgeService(db)
    return await service.get_stats()
