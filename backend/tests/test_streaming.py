"""Tests for streaming chat using LangGraph astream"""
import pytest
import json


class TestStreamingChatAPI:
    """Test streaming chat API endpoints"""

    def test_stream_chat_creates_session(self, test_client):
        """Test that streaming chat creates a new session"""
        response = test_client.post("/api/v1/chat/stream", json={"message": "你好"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE events
        events = _parse_sse_events(response.text)

        # Check session_id event
        session_events = [e for e in events if e.get("event") == "session_id"]
        assert len(session_events) > 0
        assert "session_id" in session_events[0]["data"]

    def test_stream_chat_intent_classification(self, test_client):
        """Test intent classification in streaming chat"""
        response = test_client.post("/api/v1/chat/stream", json={"message": "我想了解合同法相关内容"})

        assert response.status_code == 200

        events = _parse_sse_events(response.text)

        # Check intent event
        intent_events = [e for e in events if e.get("event") == "intent"]
        assert len(intent_events) > 0
        assert intent_events[0]["data"]["intent"] in ["greeting", "legal_consultation", "general_chat"]

    def test_stream_chat_legal_query_retrieves_context(self, test_client):
        """Test that legal queries trigger context retrieval"""
        response = test_client.post(
            "/api/v1/chat/stream",
            json={"message": "什么是侵权责任？"}
        )

        assert response.status_code == 200

        events = _parse_sse_events(response.text)

        # Check for context event (may be empty if no docs in DB)
        context_events = [e for e in events if e.get("event") == "context"]
        assert len(context_events) > 0
        assert "sources" in context_events[0]["data"]

    def test_stream_chat_sends_tokens(self, test_client):
        """Test that response is streamed in tokens"""
        response = test_client.post("/api/v1/chat/stream", json={"message": "你好"})

        assert response.status_code == 200

        events = _parse_sse_events(response.text)

        # Check for token events
        token_events = [e for e in events if e.get("event") == "token"]
        assert len(token_events) > 0

        # Verify token structure
        assert "chunk" in token_events[0]["data"]
        assert "full_response" in token_events[0]["data"]

    def test_stream_chat_sends_end_event(self, test_client):
        """Test that streaming ends properly"""
        response = test_client.post("/api/v1/chat/stream", json={"message": "你好"})

        assert response.status_code == 200

        events = _parse_sse_events(response.text)

        # Check for end event
        end_events = [e for e in events if e.get("event") == "end"]
        assert len(end_events) > 0
        assert "response" in end_events[0]["data"]

    def test_stream_chat_with_existing_session(self, test_client):
        """Test streaming chat with existing session"""
        # Create a session first using streaming endpoint
        create_response = test_client.post(
            "/api/v1/chat/stream",
            json={"message": "第一次对话"}
        )

        assert create_response.status_code == 200
        events = _parse_sse_events(create_response.text)

        # Extract session_id from first session_id event
        session_events = [e for e in events if e.get("event") == "session_id"]
        assert len(session_events) > 0
        session_id = session_events[0]["data"]["session_id"]

        # Use the session in streaming
        response = test_client.post(
            "/api/v1/chat/stream",
            json={"message": "继续对话", "session_id": session_id}
        )

        assert response.status_code == 200

        events = _parse_sse_events(response.text)

        # Should still get session_id
        session_events = [e for e in events if e.get("event") == "session_id"]
        assert len(session_events) > 0
        assert session_events[0]["data"]["session_id"] == session_id

    def test_stream_chat_greeting_intent(self, test_client):
        """Test greeting classification"""
        response = test_client.post("/api/v1/chat/stream", json={"message": "你好"})

        assert response.status_code == 200

        events = _parse_sse_events(response.text)
        intent_events = [e for e in events if e.get("event") == "intent"]

        assert len(intent_events) > 0
        assert intent_events[0]["data"]["intent"] == "greeting"

    def test_stream_chat_legal_intent(self, test_client):
        """Test legal consultation intent classification"""
        response = test_client.post(
            "/api/v1/chat/stream",
            json={"message": "请问关于合同违约有什么法律规定？"}
        )

        assert response.status_code == 200

        events = _parse_sse_events(response.text)
        intent_events = [e for e in events if e.get("event") == "intent"]

        assert len(intent_events) > 0
        assert intent_events[0]["data"]["intent"] == "legal_consultation"

    def test_stream_chat_general_intent(self, test_client):
        """Test general chat intent classification"""
        response = test_client.post(
            "/api/v1/chat/stream",
            json={"message": "今天天气怎么样"}
        )

        assert response.status_code == 200

        events = _parse_sse_events(response.text)
        intent_events = [e for e in events if e.get("event") == "intent"]

        assert len(intent_events) > 0
        # Should be either general_chat or legal depending on content
        assert intent_events[0]["data"]["intent"] in ["general_chat", "legal_consultation", "greeting"]

    def test_stream_chat_invalid_session(self, test_client):
        """Test streaming chat with invalid session ID"""
        response = test_client.post(
            "/api/v1/chat/stream",
            json={"message": "测试", "session_id": "nonexistent-id"}
        )

        assert response.status_code == 200

        events = _parse_sse_events(response.text)

        # Should get error event
        error_events = [e for e in events if e.get("event") == "error"]
        assert len(error_events) > 0


def _parse_sse_events(text: str) -> list:
    """Parse SSE events from response text"""
    events = []
    lines = text.strip().split("\n")

    current_event = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("event:"):
            current_event["event"] = line[6:].strip()
        elif line.startswith("data:"):
            try:
                current_event["data"] = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                current_event["data"] = line[5:].strip()

            # If we have both event and data, add to events
            if "event" in current_event and "data" in current_event:
                events.append(current_event.copy())
                current_event = {}

    return events
