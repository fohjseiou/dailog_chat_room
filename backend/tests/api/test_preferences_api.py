"""Test preferences API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestPreferencesAPI:
    """Test preferences API endpoints"""

    @pytest.fixture
    def auth_headers(self, test_client: TestClient):
        """Fixture to get authenticated headers"""
        # Register and login a user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "prefuser",
                "password": "password123"
            }
        )
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "prefuser",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_all_preferences_empty(self, test_client: TestClient, auth_headers: dict):
        """Test getting all preferences when none exist"""
        response = test_client.get(
            "/api/v1/preferences",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["preferences"] == {}

    def test_set_preference_success(self, test_client: TestClient, auth_headers: dict):
        """Test setting a single preference"""
        response = test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={
                "key": "language",
                "value": "zh-CN"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "language"
        assert data["value"] == "zh-CN"
        assert "id" in data
        assert "user_id" in data
        assert "updated_at" in data

    def test_set_preference_multiple(self, test_client: TestClient, auth_headers: dict):
        """Test setting multiple preferences"""
        # Set first preference
        test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "language", "value": "en-US"}
        )

        # Set second preference
        test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "theme", "value": "dark"}
        )

        # Get all preferences
        response = test_client.get(
            "/api/v1/preferences",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["preferences"]) == 2
        assert data["preferences"]["language"] == "en-US"
        assert data["preferences"]["theme"] == "dark"

    def test_set_preference_update_existing(self, test_client: TestClient, auth_headers: dict):
        """Test updating an existing preference using POST"""
        # Create preference
        test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "language", "value": "en-US"}
        )

        # Update using POST
        response = test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "language", "value": "zh-CN"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "zh-CN"

    def test_set_preference_validation_error_empty_key(self, test_client: TestClient, auth_headers: dict):
        """Test setting preference with empty key"""
        response = test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "", "value": "some_value"}
        )
        assert response.status_code == 422  # Validation error

    def test_set_preference_validation_error_empty_value(self, test_client: TestClient, auth_headers: dict):
        """Test setting preference with empty value"""
        response = test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "language", "value": ""}
        )
        assert response.status_code == 422  # Validation error

    def test_update_preference_success(self, test_client: TestClient, auth_headers: dict):
        """Test updating an existing preference using PUT"""
        # Create preference first
        test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "theme", "value": "light"}
        )

        # Update using PUT
        response = test_client.put(
            "/api/v1/preferences/theme",
            headers=auth_headers,
            json={"value": "dark"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "dark"
        assert data["key"] == "theme"

    def test_update_preference_not_found(self, test_client: TestClient, auth_headers: dict):
        """Test updating a non-existent preference"""
        response = test_client.put(
            "/api/v1/preferences/nonexistent",
            headers=auth_headers,
            json={"value": "some_value"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_preference_success(self, test_client: TestClient, auth_headers: dict):
        """Test deleting a preference"""
        # Create preference first
        test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "temp_pref", "value": "temp_value"}
        )

        # Delete it
        response = test_client.delete(
            "/api/v1/preferences/temp_pref",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify it's gone
        get_response = test_client.get(
            "/api/v1/preferences",
            headers=auth_headers
        )
        assert get_response.json()["preferences"] == {}

    def test_delete_preference_idempotent(self, test_client: TestClient, auth_headers: dict):
        """Test that deleting non-existent preference is idempotent"""
        # Delete a preference that doesn't exist
        response = test_client.delete(
            "/api/v1/preferences/nonexistent",
            headers=auth_headers
        )
        assert response.status_code == 200  # Still returns success

    def test_list_preference_keys_empty(self, test_client: TestClient, auth_headers: dict):
        """Test listing preference keys when none exist"""
        response = test_client.get(
            "/api/v1/preferences/keys",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_preference_keys(self, test_client: TestClient, auth_headers: dict):
        """Test listing preference keys"""
        # Set multiple preferences
        test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "language", "value": "en-US"}
        )
        test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "theme", "value": "dark"}
        )
        test_client.post(
            "/api/v1/preferences",
            headers=auth_headers,
            json={"key": "notifications", "value": "on"}
        )

        # List keys
        response = test_client.get(
            "/api/v1/preferences/keys",
            headers=auth_headers
        )
        assert response.status_code == 200
        keys = response.json()
        assert len(keys) == 3
        assert "language" in keys
        assert "theme" in keys
        assert "notifications" in keys

    def test_unauthenticated_get_preferences(self, test_client: TestClient):
        """Test getting preferences without authentication"""
        response = test_client.get("/api/v1/preferences")
        assert response.status_code == 401

    def test_unauthenticated_set_preference(self, test_client: TestClient):
        """Test setting preference without authentication"""
        response = test_client.post(
            "/api/v1/preferences",
            json={"key": "language", "value": "en-US"}
        )
        assert response.status_code == 401

    def test_unauthenticated_update_preference(self, test_client: TestClient):
        """Test updating preference without authentication"""
        response = test_client.put(
            "/api/v1/preferences/language",
            json={"value": "zh-CN"}
        )
        assert response.status_code == 401

    def test_unauthenticated_delete_preference(self, test_client: TestClient):
        """Test deleting preference without authentication"""
        response = test_client.delete("/api/v1/preferences/language")
        assert response.status_code == 401

    def test_user_isolation(self, test_client: TestClient):
        """Test that users can only access their own preferences"""
        # Create two users
        test_client.post(
            "/api/v1/auth/register",
            json={"username": "user1", "password": "password123"}
        )
        user1_login = test_client.post(
            "/api/v1/auth/login",
            json={"username": "user1", "password": "password123"}
        )
        user1_headers = {"Authorization": f"Bearer {user1_login.json()['access_token']}"}

        test_client.post(
            "/api/v1/auth/register",
            json={"username": "user2", "password": "password123"}
        )
        user2_login = test_client.post(
            "/api/v1/auth/login",
            json={"username": "user2", "password": "password123"}
        )
        user2_headers = {"Authorization": f"Bearer {user2_login.json()['access_token']}"}

        # User 1 sets a preference
        test_client.post(
            "/api/v1/preferences",
            headers=user1_headers,
            json={"key": "theme", "value": "dark"}
        )

        # User 2 should not see user 1's preference
        response = test_client.get(
            "/api/v1/preferences",
            headers=user2_headers
        )
        assert response.json()["preferences"] == {}

        # User 1 should see their preference
        response = test_client.get(
            "/api/v1/preferences",
            headers=user1_headers
        )
        assert response.json()["preferences"]["theme"] == "dark"

    def test_common_preferences(self, test_client: TestClient, auth_headers: dict):
        """Test setting common preference types"""
        common_prefs = {
            "language": "zh-CN",
            "response_style": "concise",
            "theme": "dark",
            "notifications": "on"
        }

        for key, value in common_prefs.items():
            response = test_client.post(
                "/api/v1/preferences",
                headers=auth_headers,
                json={"key": key, "value": value}
            )
            assert response.status_code == 200
            assert response.json()["value"] == value

        # Verify all are stored
        response = test_client.get(
            "/api/v1/preferences",
            headers=auth_headers
        )
        assert response.status_code == 200
        for key, value in common_prefs.items():
            assert response.json()["preferences"][key] == value
