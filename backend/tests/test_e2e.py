import pytest

def test_chat_flow(test_client):
    """Test complete chat flow"""
    # New session with greeting
    response = test_client.post("/api/v1/chat", json={
        "message": "你好"
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "response" in data

    session_id = data["session_id"]

    # Legal question
    response = test_client.post("/api/v1/chat", json={
        "session_id": session_id,
        "message": "合同法的基本原则是什么？"
    })
    assert response.status_code == 200

    # Get session
    response = test_client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message_count"] >= 2

def test_session_list(test_client):
    """Test session listing"""
    # Create multiple sessions
    for i in range(3):
        test_client.post("/api/v1/chat", json={"message": f"测试{i}"})

    # List sessions
    response = test_client.get("/api/v1/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) >= 3
