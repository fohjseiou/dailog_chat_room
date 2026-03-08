import chromadb
from chromadb.config import Settings
from chromadb import errors
from typing import List, Dict, Any, Optional
from app.config import get_settings
import logging
import asyncio

logger = logging.getLogger(__name__)


class ChromaService:
    """Service for ChromaDB vector operations"""

    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = settings.chroma_collection_name
        self._collection = None

    def _get_or_create_collection(self):
        """Helper method to get or create collection (synchronous)"""
        if self._collection is None:
            try:
                self._collection = self.client.get_collection(name=self.collection_name)
            except errors.NotFoundError:
                self._collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Legal knowledge base with DashScope embeddings"}
                )
        return self._collection

    async def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents with embeddings to collection"""
        try:
            loop = asyncio.get_event_loop()
            coll = await loop.run_in_executor(None, self._get_or_create_collection)
            await loop.run_in_executor(
                None,
                lambda: coll.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
            )
            logger.info(f"Added {len(documents)} documents to ChromaDB")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    async def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents by embedding"""
        try:
            loop = asyncio.get_event_loop()
            coll = await loop.run_in_executor(None, self._get_or_create_collection)
            results = await loop.run_in_executor(
                None,
                lambda: coll.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where,
                    include=["documents", "metadatas", "distances"]
                )
            )
            return {
                "documents": results.get("documents", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "distances": results.get("distances", [[]])[0]
            }
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    async def delete_by_document_id(self, document_id: str) -> None:
        """Delete all chunks for a document"""
        try:
            loop = asyncio.get_event_loop()
            coll = await loop.run_in_executor(None, self._get_or_create_collection)
            results = await loop.run_in_executor(
                None,
                lambda: coll.get(where={"document_id": document_id})
            )
            if results and results.get("ids"):
                await loop.run_in_executor(
                    None,
                    lambda: coll.delete(ids=results["ids"])
                )
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            loop = asyncio.get_event_loop()
            coll = await loop.run_in_executor(None, self._get_or_create_collection)
            count = await loop.run_in_executor(None, lambda: coll.count())
            return {
                "name": self.collection_name,
                "count": count,
                "metadata": coll.metadata
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"name": self.collection_name, "count": 0, "metadata": {}}


# Singleton
_chroma_service = None


def get_chroma_service() -> ChromaService:
    """Get or create the ChromaDB service singleton"""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
