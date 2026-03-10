"""Test authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestAuthAPI:
    """Test authentication API endpoints"""

    def test_register_success(self, test_client: TestClient):
        """Test successful user registration"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["username"] == "newuser"
        assert "created_at" in data
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_username(self, test_client: TestClient):
        """Test registration with duplicate username"""
        # Register first user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "password": "password123"
            }
        )

        # Try to register with same username
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "password": "different456"
            }
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_invalid_username_too_short(self, test_client: TestClient):
        """Test registration with username too short"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",
                "password": "password123"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_register_invalid_password_too_short(self, test_client: TestClient):
        """Test registration with password too short"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "validuser",
                "password": "12345"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_login_success(self, test_client: TestClient):
        """Test successful login"""
        # Register a user first
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "loginuser",
                "password": "password123"
            }
        )

        # Login
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "loginuser",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "loginuser"
        assert "id" in data["user"]

    def test_login_invalid_username(self, test_client: TestClient):
        """Test login with non-existent username"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_invalid_password(self, test_client: TestClient):
        """Test login with wrong password"""
        # Register a user first
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "passwordtest",
                "password": "correctpassword"
            }
        )

        # Login with wrong password
        response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "passwordtest",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_me_authenticated(self, test_client: TestClient):
        """Test getting current user when authenticated"""
        # Register and login
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "metest",
                "password": "password123"
            }
        )
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "metest",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "metest"
        assert "id" in data
        assert "created_at" in data

    def test_me_unauthenticated(self, test_client: TestClient):
        """Test getting current user without authentication"""
        response = test_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self, test_client: TestClient):
        """Test getting current user with invalid token"""
        response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"}
        )
        assert response.status_code == 401

    def test_me_updates_last_login(self, test_client: TestClient):
        """Test that login updates last_login timestamp"""
        # Register a user
        test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "lastlogintest",
                "password": "password123"
            }
        )

        # Login
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "username": "lastlogintest",
                "password": "password123"
            }
        )

        # Get current user to check last_login was updated
        token = login_response.json()["access_token"]
        me_response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert me_response.status_code == 200
        user_data = me_response.json()
        assert "last_login" in user_data
        assert user_data["last_login"] is not None

    def test_login_missing_fields(self, test_client: TestClient):
        """Test login with missing fields"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "test"}
        )
        assert response.status_code == 422  # Validation error

    def test_register_missing_fields(self, test_client: TestClient):
        """Test registration with missing fields"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={"username": "test"}
        )
        assert response.status_code == 422  # Validation error
