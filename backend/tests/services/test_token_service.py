"""Test TokenService for JWT creation and verification."""

import pytest
from app.services.token_service import TokenService
from datetime import datetime


def test_create_access_token():
    """Test creating an access token returns a valid JWT string."""
    service = TokenService()
    token = service.create_access_token("user123")
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_access_token_valid():
    """Test verifying a valid access token returns correct payload."""
    service = TokenService()
    token = service.create_access_token("user123")
    payload = service.verify_token(token)
    assert payload["sub"] == "user123"


def test_verify_access_token_invalid():
    """Test verifying an invalid token raises an exception."""
    service = TokenService()
    with pytest.raises(ValueError):
        service.verify_token("invalid.token.here")
