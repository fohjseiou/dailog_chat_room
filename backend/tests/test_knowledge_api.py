import pytest
import tempfile
import os
from io import BytesIO
from fastapi.testclient import TestClient


class TestKnowledgeAPI:
    """Test knowledge base API endpoints"""

    def test_list_documents_empty(self, test_client: TestClient):
        """Test listing documents when database is empty"""
        response = test_client.get("/api/v1/knowledge/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert data["total"] == 0
        assert data["page"] == 1
        assert len(data["documents"]) == 0

    def test_list_documents_pagination(self, test_client: TestClient):
        """Test document list pagination"""
        # Create some documents first
        for i in range(5):
            response = test_client.post(
                "/api/v1/knowledge/documents",
                json={
                    "title": f"Test Document {i}",
                    "category": "law",
                    "source": f"Source {i}"
                }
            )
            assert response.status_code == 200

        # Test first page
        response = test_client.get("/api/v1/knowledge/documents?page=1&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["documents"]) == 3

        # Test second page
        response = test_client.get("/api/v1/knowledge/documents?page=2&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2

    def test_list_documents_with_search(self, test_client: TestClient):
        """Test searching documents"""
        # Create documents with different titles
        test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Contract Law Basics", "category": "law"}
        )
        test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Criminal Procedure", "category": "law"}
        )
        test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Family Law Guide", "category": "law"}
        )

        # Search for "contract"
        response = test_client.get("/api/v1/knowledge/documents?search=contract")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1
        assert "contract" in data["documents"][0]["title"].lower()

    def test_list_documents_with_category_filter(self, test_client: TestClient):
        """Test filtering documents by category"""
        # Create documents with different categories
        test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Law Document", "category": "law"}
        )
        test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Case Document", "category": "case"}
        )

        # Filter by category
        response = test_client.get("/api/v1/knowledge/documents?category=law")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1
        assert data["documents"][0]["category"] == "law"

    def test_create_document_without_file(self, test_client: TestClient):
        """Test creating a document metadata entry without file"""
        response = test_client.post(
            "/api/v1/knowledge/documents",
            json={
                "title": "Test Document",
                "category": "law",
                "source": "Test Source"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Document"
        assert data["category"] == "law"
        assert data["source"] == "Test Source"
        assert "id" in data
        assert data["chunk_count"] == 0

    def test_create_document_invalid_category(self, test_client: TestClient):
        """Test creating document with invalid category"""
        response = test_client.post(
            "/api/v1/knowledge/documents",
            json={
                "title": "Test Document",
                "category": "invalid_category"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_upload_txt_file(self, test_client: TestClient):
        """Test uploading a TXT file"""
        content = b"This is a test document with some legal content."
        files = {"file": ("test.txt", BytesIO(content), "text/plain")}
        data = {
            "title": "Test TXT Document",
            "category": "law",
            "source": "Test Source"
        }

        response = test_client.post(
            "/api/v1/knowledge/documents/upload",
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "Test TXT Document"
        assert result["category"] == "law"
        assert result["chunk_count"] > 0
        assert "id" in result

    def test_upload_unsupported_file_type(self, test_client: TestClient):
        """Test uploading an unsupported file type"""
        content = b"Some content"
        files = {"file": ("test.exe", BytesIO(content), "application/x-msdownload")}
        data = {"title": "Test", "category": "law"}

        response = test_client.post(
            "/api/v1/knowledge/documents/upload",
            files=files,
            data=data
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_get_document(self, test_client: TestClient):
        """Test getting a document by ID"""
        # Create a document first
        create_response = test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Test Document", "category": "law"}
        )
        document_id = create_response.json()["id"]

        # Get the document
        response = test_client.get(f"/api/v1/knowledge/documents/{document_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id
        assert data["title"] == "Test Document"

    def test_get_document_not_found(self, test_client: TestClient):
        """Test getting a non-existent document"""
        response = test_client.get("/api/v1/knowledge/documents/nonexistent-id")
        assert response.status_code == 404

    def test_update_document(self, test_client: TestClient):
        """Test updating document metadata"""
        # Create a document first
        create_response = test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Original Title", "category": "law"}
        )
        document_id = create_response.json()["id"]

        # Update the document
        response = test_client.put(
            f"/api/v1/knowledge/documents/{document_id}",
            json={"title": "Updated Title", "category": "case"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["category"] == "case"

    def test_update_document_not_found(self, test_client: TestClient):
        """Test updating a non-existent document"""
        response = test_client.put(
            "/api/v1/knowledge/documents/nonexistent-id",
            json={"title": "New Title"}
        )
        assert response.status_code == 404

    def test_delete_document(self, test_client: TestClient):
        """Test deleting a document"""
        # Create a document first
        create_response = test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "To Delete", "category": "law"}
        )
        document_id = create_response.json()["id"]

        # Delete the document
        response = test_client.delete(f"/api/v1/knowledge/documents/{document_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

        # Verify it's gone
        get_response = test_client.get(f"/api/v1/knowledge/documents/{document_id}")
        assert get_response.status_code == 404

    def test_delete_document_not_found(self, test_client: TestClient):
        """Test deleting a non-existent document"""
        response = test_client.delete("/api/v1/knowledge/documents/nonexistent-id")
        assert response.status_code == 404

    def test_get_stats(self, test_client: TestClient):
        """Test getting knowledge base statistics"""
        # Create some documents
        test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Doc 1", "category": "law"}
        )
        test_client.post(
            "/api/v1/knowledge/documents",
            json={"title": "Doc 2", "category": "case"}
        )

        # Get stats
        response = test_client.get("/api/v1/knowledge/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "categories" in data
        assert "valid_categories" in data
        assert data["total_documents"] >= 2

    def test_create_document_missing_title(self, test_client: TestClient):
        """Test creating document without required title"""
        response = test_client.post(
            "/api/v1/knowledge/documents",
            json={"category": "law"}
        )
        assert response.status_code == 422  # Validation error

    def test_list_documents_invalid_page(self, test_client: TestClient):
        """Test listing documents with invalid page number"""
        response = test_client.get("/api/v1/knowledge/documents?page=0")
        assert response.status_code == 422  # Validation error

    def test_list_documents_invalid_page_size(self, test_client: TestClient):
        """Test listing documents with invalid page size"""
        response = test_client.get("/api/v1/knowledge/documents?page_size=0")
        assert response.status_code == 422  # Validation error

        response = test_client.get("/api/v1/knowledge/documents?page_size=101")
        assert response.status_code == 422  # Validation error
