"""End-to-end integration test for complete user workflow.

This test verifies the complete user journey from registration to session management
and access control, ensuring proper user isolation and authentication.

Test workflow:
1. Register new user
2. Login (verify JWT token returned)
3. Create session (verify associated with user)
4. List sessions (verify only own sessions returned)
5. Send message
6. Try accessing other user's session (verify 403)
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any


class TestUserWorkflowE2E:
    """Test complete user workflow end-to-end"""

    def test_complete_user_workflow(self, test_client: TestClient):
        """Test the complete user workflow from registration to access control"""

        # ============================================================================
        # Step 1: Register new user
        # ============================================================================
        register_response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "workflow_user",
                "password": "secure_password_123"
            }
        )

        assert register_response.status_code == 200, \
            f"Registration failed: {register_response.json()}"
        register_data = register_response.json()

        # Verify user was created successfully
        assert "id" in register_data, "Response should contain user ID"
        assert register_data["username"] == "workflow_user", "Username should match"
        assert "created_at" in register_data, "Response should contain creation timestamp"
        assert "password" not in register_data, "Password should not be exposed"
        assert "password_hash" not in register_data, "Password hash should not be exposed"

        user_id = register_data["id"]
        print(f"✓ Step 1: User registered successfully with ID: {user_id}")

        # ============================================================================
        # Step 2: Login (verify JWT token returned)
        # ============================================================================
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "workflow_user",
                "password": "secure_password_123"
            }
        )

        assert login_response.status_code == 200, \
            f"Login failed: {login_response.json()}"
        login_data = login_response.json()

        # Verify JWT token structure
        assert "access_token" in login_data, "Response should contain access token"
        assert login_data["token_type"] == "bearer", "Token type should be bearer"
        assert len(login_data["access_token"]) > 0, "Access token should not be empty"

        # Verify user information in response
        assert "user" in login_data, "Response should contain user info"
        assert login_data["user"]["id"] == user_id, "User ID should match"
        assert login_data["user"]["username"] == "workflow_user", "Username should match"
        # JWT token has 3 parts separated by dots (header.payload.signature)
        assert "." in login_data["access_token"], \
            "Token should be a valid JWT format"

        access_token = login_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        print(f"✓ Step 2: User logged in successfully, JWT token received")

        # Verify we can access protected endpoint with token
        me_response = test_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert me_response.status_code == 200, \
            f"Failed to access /me endpoint: {me_response.json()}"
        me_data = me_response.json()
        assert me_data["id"] == user_id, "User ID should match"
        assert me_data["username"] == "workflow_user", "Username should match"
        assert "last_login" in me_data, "Last login should be tracked"
        assert me_data["last_login"] is not None, "Last login should not be null"
        print("✓ Step 2b: JWT token validated successfully via /me endpoint")

        # ============================================================================
        # Step 3: Create session (verify associated with user)
        # ============================================================================
        session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "My Test Session"},
            headers=auth_headers
        )

        assert session_response.status_code == 200, \
            f"Session creation failed: {session_response.json()}"
        session_data = session_response.json()

        # Verify session was created
        assert "id" in session_data, "Session should have ID"
        assert session_data["title"] == "My Test Session", "Session title should match"
        assert session_data["user_id"] == user_id, "Session should be associated with user"
        assert session_data["message_count"] == 0, "New session should have 0 messages"

        session_id = session_data["id"]
        print(f"✓ Step 3: Session created successfully with ID: {session_id}")
        print(f"  Session properly associated with user_id: {user_id}")

        # ============================================================================
        # Step 4: List sessions (verify only own sessions returned)
        # ============================================================================
        list_response = test_client.get(
            "/api/v1/sessions",
            headers=auth_headers
        )

        assert list_response.status_code == 200, \
            f"Session listing failed: {list_response.json()}"
        sessions = list_response.json()

        # Verify we can see our own session
        assert len(sessions) >= 1, "Should see at least our created session"
        assert any(s["id"] == session_id for s in sessions), \
            "Our created session should be in the list"

        # Verify all sessions belong to current user (user isolation)
        for session in sessions:
            assert session["user_id"] == user_id, \
                f"Session {session['id']} should belong to current user"

        print(f"✓ Step 4: Listed {len(sessions)} session(s), all belong to current user")

        # ============================================================================
        # Step 4b: Verify anonymous user cannot see authenticated sessions
        # ============================================================================
        anonymous_list_response = test_client.get("/api/v1/sessions")
        assert anonymous_list_response.status_code == 200
        anonymous_sessions = anonymous_list_response.json()

        # Anonymous users should only see sessions with user_id = None
        for session in anonymous_sessions:
            assert session["user_id"] is None, \
                f"Anonymous user should not see session {session['id']} belonging to {session['user_id']}"

        # Our authenticated session should NOT be visible to anonymous users
        assert not any(s["id"] == session_id for s in anonymous_sessions), \
            "Authenticated session should not be visible to anonymous users"

        print("✓ Step 4b: Verified user isolation - anonymous users cannot see authenticated sessions")

        # ============================================================================
        # Step 5: Send message
        # ============================================================================
        message_response = test_client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Hello, this is a test message"
            },
            headers=auth_headers
        )

        assert message_response.status_code == 200, \
            f"Message sending failed: {message_response.json()}"
        message_data = message_response.json()

        # Verify message response
        assert "response" in message_data, "Should get a response"
        assert "session_id" in message_data, "Should return session ID"
        assert message_data["session_id"] == session_id, "Session ID should match"
        assert len(message_data["response"]) > 0, "Response should not be empty"

        print(f"✓ Step 5: Message sent successfully, response received")

        # Verify session message count was updated
        session_detail_response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers
        )
        assert session_detail_response.status_code == 200
        updated_session = session_detail_response.json()
        assert updated_session["message_count"] == 1, \
            "Session should have 1 message after sending"

        # Verify messages are associated with the session
        messages_response = test_client.get(
            f"/api/v1/sessions/{session_id}/messages",
            headers=auth_headers
        )
        assert messages_response.status_code == 200
        messages = messages_response.json()
        assert len(messages) >= 2, "Should have at least 2 messages (user + assistant)"
        print(f"✓ Step 5b: Verified {len(messages)} messages saved to session")

        # ============================================================================
        # Step 6: Try accessing other user's session (verify 403)
        # ============================================================================

        # First, create another user and a session for them
        other_user_response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "other_user",
                "password": "other_password_123"
            }
        )
        assert other_user_response.status_code == 200
        other_user_id = other_user_response.json()["id"]

        # Login as other user and create a session
        other_login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "other_user",
                "password": "other_password_123"
            }
        )
        other_token = other_login_response.json()["access_token"]

        other_session_response = test_client.post(
            "/api/v1/sessions",
            json={"title": "Other User's Session"},
            headers={"Authorization": f"Bearer {other_token}"}
        )
        assert other_session_response.status_code == 200
        other_session_id = other_session_response.json()["id"]
        print(f"✓ Step 6a: Created other user's session: {other_session_id}")

        # Now try to access other user's session with our token (should fail with 403)
        unauthorized_response = test_client.get(
            f"/api/v1/sessions/{other_session_id}",
            headers=auth_headers  # Using original user's token
        )

        assert unauthorized_response.status_code == 403, \
            f"Should return 403 Forbidden, got {unauthorized_response.status_code}: {unauthorized_response.json()}"
        assert "forbidden" in unauthorized_response.json()["detail"].lower() or \
               "can only access your own sessions" in unauthorized_response.json()["detail"].lower(), \
            "Error message should indicate access forbidden"

        print("✓ Step 6b: Successfully blocked - got 403 when accessing other user's session")

        # Also verify we can't list other user's sessions
        sessions_list_after = test_client.get(
            "/api/v1/sessions",
            headers=auth_headers
        )
        our_sessions = sessions_list_after.json()

        # Should still only see our own sessions, not the other user's session
        assert not any(s["id"] == other_session_id for s in our_sessions), \
            "Other user's session should not appear in our session list"

        print("✓ Step 6c: Verified session list isolation - other users' sessions not visible")

        # ============================================================================
        # Additional verification: Test without authentication
        # ============================================================================

        # Try to access our session without authentication (should work for anonymous viewing)
        # Actually, based on the API, anonymous users can't see authenticated sessions
        unauth_response = test_client.get(f"/api/v1/sessions/{session_id}")
        # This should return 403 because session has user_id
        assert unauth_response.status_code == 403, \
            "Anonymous users should not be able to access authenticated sessions"
        print("✓ Step 7: Verified anonymous users cannot access authenticated sessions")

        print("\n" + "=" * 70)
        print("✅ ALL E2E TESTS PASSED - Complete user workflow verified successfully!")
        print("=" * 70)

    def test_user_workflow_with_multiple_sessions(self, test_client: TestClient):
        """Test user workflow with multiple sessions for better coverage"""

        # Register and login
        test_client.post(
            "/api/v1/auth/register",
            json={"username": "multi_session_user", "password": "password123"}
        )
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "multi_session_user", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = login_response.json()["user"]["id"]

        # Create multiple sessions
        session_ids = []
        for i in range(3):
            response = test_client.post(
                "/api/v1/sessions",
                json={"title": f"Session {i+1}"},
                headers=headers
            )
            assert response.status_code == 200
            session_data = response.json()
            assert session_data["user_id"] == user_id
            session_ids.append(session_data["id"])

        # List sessions
        list_response = test_client.get("/api/v1/sessions", headers=headers)
        sessions = list_response.json()

        # Verify all our sessions are listed
        assert len(sessions) >= 3
        for session_id in session_ids:
            assert any(s["id"] == session_id for s in sessions)

        # Send messages to different sessions
        for i, session_id in enumerate(session_ids):
            response = test_client.post(
                "/api/v1/chat",
                json={
                    "session_id": session_id,
                    "message": f"Message {i+1} for session"
                },
                headers=headers
            )
            assert response.status_code == 200

        # Verify each session has correct message count
        for session_id in session_ids:
            response = test_client.get(f"/api/v1/sessions/{session_id}", headers=headers)
            assert response.status_code == 200
            assert response.json()["message_count"] == 1

        print("✓ Multiple sessions workflow test passed")

    def test_user_cannot_access_anonymous_session_after_login(self, test_client: TestClient):
        """Test that authenticated users have proper boundaries with anonymous sessions"""

        # Create an anonymous session (no auth)
        anonymous_response = test_client.post(
            "/api/v1/chat",
            json={"message": "Anonymous message"}
        )
        assert anonymous_response.status_code == 200
        anonymous_session_id = anonymous_response.json()["session_id"]

        # Register and login
        test_client.post(
            "/api/v1/auth/register",
            json={"username": "boundary_user", "password": "password123"}
        )
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "boundary_user", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Authenticated user should NOT see anonymous sessions in their list
        list_response = test_client.get("/api/v1/sessions", headers=headers)
        sessions = list_response.json()
        assert not any(s["id"] == anonymous_session_id for s in sessions), \
            "Authenticated users should not see anonymous sessions in their list"

        print("✓ User boundary test passed - authenticated users isolated from anonymous sessions")
