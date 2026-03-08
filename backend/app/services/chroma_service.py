import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from app.config import get_settings
import logging

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

    @property
    def collection(self):
        """Get or create collection"""
        if self._collection is None:
            try:
                self._collection = self.client.get_collection(name=self.collection_name)
            except:
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
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
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
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
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
            results = self.collection.get(
                where={"document_id": document_id}
            )
            if results and results.get("ids"):
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "metadata": self.collection.metadata
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
