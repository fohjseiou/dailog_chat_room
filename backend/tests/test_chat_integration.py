import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_with_agent():
    """Test chat through agent system"""
    response = client.post("/api/v1/chat", json={
        "message": "你好"
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data

def test_legal_question_with_rag():
    """Test legal question goes through RAG"""
    response = client.post("/api/v1/chat", json={
        "message": "合同违约需要承担什么责任？"
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
