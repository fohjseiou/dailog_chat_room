import pytest
from fastapi.testclient import TestClient


class TestSummaryService:
    """Test summary service functionality"""

    def test_should_generate_summary_new_session(self, test_client: TestClient):
        """Test that new sessions don't need summaries immediately"""
        # Create a session with few messages
        response = test_client.post("/api/v1/chat", json={"message": "你好"})
        session_id = response.json()["session_id"]

        # Get summary - should return None for new session
        summary_response = test_client.get(f"/api/v1/chat/sessions/{session_id}/summary")
        assert summary_response.status_code == 200
        data = summary_response.json()
        assert data["summary"] is None
        assert "No summary available" in data.get("message", "")

    def test_get_summary_creates_summary_if_needed(self, test_client: TestClient):
        """Test that summary is generated when queried if session has enough messages"""
        session_id = None

        # Create enough messages to trigger summary generation
        for i in range(6):
            response = test_client.post(
                "/api/v1/chat",
                json={"message": f"测试消息 {i}", "session_id": session_id}
            )
            session_id = response.json()["session_id"]

        # Get summary - should generate one
        summary_response = test_client.get(f"/api/v1/chat/sessions/{session_id}/summary")
        assert summary_response.status_code == 200
        data = summary_response.json()
        assert data["summary"] is not None
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 0

    def test_regenerate_summary(self, test_client: TestClient):
        """Test regenerating a summary"""
        # Create a session with messages
        session_id = None
        for i in range(3):
            response = test_client.post(
                "/api/v1/chat",
                json={"message": f"合同问题 {i}", "session_id": session_id}
            )
            session_id = response.json()["session_id"]

        # Generate initial summary
        initial_summary = test_client.get(f"/api/v1/chat/sessions/{session_id}/summary")
        initial_text = initial_summary.json()["summary"]

        # Regenerate summary
        regenerate_response = test_client.post(f"/api/v1/chat/sessions/{session_id}/summary/regenerate")
        assert regenerate_response.status_code == 200
        data = regenerate_response.json()
        assert data["summary"] is not None
        assert "regenerated successfully" in data["message"]

    def test_get_summary_nonexistent_session(self, test_client: TestClient):
        """Test getting summary for non-existent session"""
        response = test_client.get("/api/v1/chat/sessions/nonexistent-id/summary")
        assert response.status_code == 404

    def test_regenerate_summary_nonexistent_session(self, test_client: TestClient):
        """Test regenerating summary for non-existent session"""
        response = test_client.post("/api/v1/chat/sessions/nonexistent-id/summary/regenerate")
        assert response.status_code == 404

    def test_summary_contains_conversation_context(self, test_client: TestClient):
        """Test that summary reflects conversation content"""
        session_id = None

        # Create a legal consultation conversation with enough messages
        messages = [
            "我想了解合同法",
            "请问什么是违约责任？",
            "违约金怎么计算？",
            "合同解除有什么条件？",
            "什么是不可抗力？",
            "合同纠纷怎么处理？"
        ]

        for msg in messages:
            response = test_client.post(
                "/api/v1/chat",
                json={"message": msg, "session_id": session_id}
            )
            session_id = response.json()["session_id"]

        # Get summary
        summary_response = test_client.get(f"/api/v1/chat/sessions/{session_id}/summary")
        summary = summary_response.json()["summary"]

        # Summary should be in Chinese and contain relevant keywords
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summary_persists_across_queries(self, test_client: TestClient):
        """Test that summary is persisted and doesn't change on subsequent queries"""
        session_id = None

        # Create messages
        for i in range(6):
            response = test_client.post(
                "/api/v1/chat",
                json={"message": f"消息 {i}", "session_id": session_id}
            )
            session_id = response.json()["session_id"]

        # Get summary first time
        summary1 = test_client.get(f"/api/v1/chat/sessions/{session_id}/summary")
        text1 = summary1.json()["summary"]

        # Get summary second time
        summary2 = test_client.get(f"/api/v1/chat/sessions/{session_id}/summary")
        text2 = summary2.json()["summary"]

        # Should be the same
        assert text1 == text2


class TestSummaryWithSessionList:
    """Test summary integration with session list"""

    def test_session_list_does_not_include_summary_by_default(self, test_client: TestClient):
        """Test that session list doesn't include summaries by default"""
        # Create a session
        response = test_client.post("/api/v1/chat", json={"message": "测试"})
        session_id = response.json()["session_id"]

        # Get session list
        list_response = test_client.get("/api/v1/sessions")
        sessions = list_response.json()

        # Find our session
        session = next((s for s in sessions if s["id"] == session_id), None)
        assert session is not None
        # Summary should not be in the basic list response
        assert "summary" not in session or session.get("summary") is None

    def test_session_detail_includes_summary(self, test_client: TestClient):
        """Test that getting session details includes summary when available"""
        session_id = None

        # Create enough messages for summary
        for i in range(6):
            response = test_client.post(
                "/api/v1/chat",
                json={"message": f"消息 {i}", "session_id": session_id}
            )
            session_id = response.json()["session_id"]

        # Generate summary
        test_client.get(f"/api/v1/chat/sessions/{session_id}/summary")

        # Get session detail
        detail_response = test_client.get(f"/api/v1/sessions/{session_id}")
        session = detail_response.json()

        # Summary should be included
        assert "summary" in session
