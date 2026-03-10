import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from datetime import datetime

def test_user_create_valid():
    data = UserCreate(username="testuser", password="password123")
    assert data.username == "testuser"
    assert data.password == "password123"

def test_user_create_username_too_short():
    with pytest.raises(ValidationError):
        UserCreate(username="ab", password="password123")

def test_user_create_password_too_short():
    with pytest.raises(ValidationError):
        UserCreate(username="testuser", password="12345")

def test_user_response_from_model():
    from app.models.user import User
    user = User(
        id="123",
        username="testuser",
        password_hash="hash",
        created_at=datetime.now()
    )
    response = UserResponse.model_validate(user)
    assert response.id == "123"
    assert response.username == "testuser"
