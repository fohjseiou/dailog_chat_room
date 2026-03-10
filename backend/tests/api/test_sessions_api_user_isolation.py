"""Test session API endpoints for user isolation."""

import pytest
from fastapi.testclient import TestClient


class TestSessionAPIUserIsolation:
    """Test session API endpoints with user authentication and isolation"""

    def test_create_session_as_authenticated_user(self, test_client: TestClient):
        """Test creating a session as an authenticated user includes user_id"""
        # Register and login a user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "sessionuser",
                "password": "password123"
            }
        )
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "sessionuser",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # Create a session with authentication
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "My Session"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "My Session"
        assert data["user_id"] is not None

    def test_create_session_as_anonymous_user(self, test_client: TestClient):
        """Test creating a session without authentication has user_id as None"""
        # Create a session without authentication
        response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Anonymous Session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "Anonymous Session"
        assert data.get("user_id") is None

    def test_list_sessions_returns_only_own_sessions(self, test_client: TestClient):
        """Test that listing sessions only returns sessions for the authenticated user"""
        # Register and login first user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "password": "password123"
            }
        )
        user1_login = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "password123"
            }
        )
        user1_token = user1_login.json()["access_token"]

        # Register and login second user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "password": "password123"
            }
        )
        user2_login = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "user2",
                "password": "password123"
            }
        )
        user2_token = user2_login.json()["access_token"]

        # User1 creates a session
        test_client.post(
            "/api/v1/sessions",
            json={"title": "User1 Session"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )

        # User2 creates a session
        test_client.post(
            "/api/v1/sessions",
            json={"title": "User2 Session"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        # Create an anonymous session
        test_client.post(
            "/api/v1/sessions",
            json={"title": "Anonymous Session"}
        )

        # User1 lists sessions - should only see their own
        user1_sessions = test_client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert user1_sessions.status_code == 200
        user1_session_list = user1_sessions.json()
        assert len(user1_session_list) == 1
        assert user1_session_list[0]["title"] == "User1 Session"
        assert user1_session_list[0]["user_id"] is not None

        # User2 lists sessions - should only see their own
        user2_sessions = test_client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert user2_sessions.status_code == 200
        user2_session_list = user2_sessions.json()
        assert len(user2_session_list) == 1
        assert user2_session_list[0]["title"] == "User2 Session"
        assert user2_session_list[0]["user_id"] is not None

        # Anonymous user lists sessions - should see only anonymous sessions
        anonymous_sessions = test_client.get("/api/v1/sessions")
        assert anonymous_sessions.status_code == 200
        anonymous_session_list = anonymous_sessions.json()
        assert len(anonymous_session_list) == 1
        assert anonymous_session_list[0]["title"] == "Anonymous Session"
        assert anonymous_session_list[0].get("user_id") is None

    def test_get_session_own_session(self, test_client: TestClient):
        """Test getting a session that belongs to the authenticated user"""
        # Register and login a user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "owner",
                "password": "password123"
            }
        )
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "owner",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # Create a session
        create_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "My Session"},
            headers={"Authorization": f"Bearer {token}"}
        )
        session_id = create_response.json()["id"]

        # Get the session
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "My Session"

    def test_get_session_other_user_session_forbidden(self, test_client: TestClient):
        """Test that getting another user's session returns 403"""
        # Register and login first user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "owner2",
                "password": "password123"
            }
        )
        owner_login = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "owner2",
                "password": "password123"
            }
        )
        owner_token = owner_login.json()["access_token"]

        # Create a session as owner
        create_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Owner's Session"},
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        session_id = create_response.json()["id"]

        # Register and login second user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "intruder",
                "password": "password123"
            }
        )
        intruder_login = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "intruder",
                "password": "password123"
            }
        )
        intruder_token = intruder_login.json()["access_token"]

        # Try to get owner's session as intruder
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": f"Bearer {intruder_token}"}
        )

        assert response.status_code == 403
        assert "forbidden" in response.json()["detail"].lower()

    def test_get_session_anonymous_session_by_anyone(self, test_client: TestClient):
        """Test that anonymous sessions can be accessed by anyone"""
        # Create an anonymous session
        create_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Anonymous Session"}
        )
        session_id = create_response.json()["id"]

        # Register and login a user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "authuser",
                "password": "password123"
            }
        )
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "authuser",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # Get the anonymous session as authenticated user
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "Anonymous Session"
