import pytest
from app.services.auth_service import AuthService, UserAlreadyExistsError, InvalidCredentialsError
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_register_user_success(db_session):
    service = AuthService(db_session)
    user_data = UserCreate(username="newuser", password="password123")
    user = await service.register(user_data)

    assert user.username == "newuser"
    assert user.id is not None
    assert user.password_hash != "password123"  # Should be hashed

@pytest.mark.asyncio
async def test_register_duplicate_username_fails(db_session, test_user):
    service = AuthService(db_session)
    user_data = UserCreate(username=test_user.username, password="password123")

    with pytest.raises(UserAlreadyExistsError):
        await service.register(user_data)

@pytest.mark.asyncio
async def test_login_valid_credentials(db_session, test_user_with_password):
    service = AuthService(db_session)
    user = await service.login(test_user_with_password.username, "testpassword123")

    assert user.username == test_user_with_password.username

@pytest.mark.asyncio
async def test_login_invalid_credentials(db_session, test_user):
    service = AuthService(db_session)

    with pytest.raises(InvalidCredentialsError):
        await service.login(test_user.username, "wrongpassword")
