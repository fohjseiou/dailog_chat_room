"""Test passlib installation and basic functionality."""
import pytest


def test_passlib_import():
    """Test that passlib can be imported."""
    try:
        import passlib
        assert passlib.__version__ is not None
    except ImportError as e:
        pytest.fail(f"passlib import failed: {e}")


def test_bcrypt_import():
    """Test that bcrypt can be imported."""
    try:
        import bcrypt
        assert bcrypt.__version__ is not None
    except ImportError as e:
        pytest.fail(f"bcrypt import failed: {e}")


def test_bcrypt_direct_hashing():
    """Test that bcrypt hashing works directly."""
    import bcrypt

    # Test hashing a password
    password = b"test_password_123"
    salt = bcrypt.gensalt()
    hash_result = bcrypt.hashpw(password, salt)

    # Verify hash was created
    assert hash_result is not None
    assert len(hash_result) > 0
    assert hash_result.startswith(b"$2b$")

    # Test verification
    assert bcrypt.checkpw(password, hash_result) is True
    assert bcrypt.checkpw(b"wrong_password", hash_result) is False


def test_bcrypt_roundtrip():
    """Test password hashing and verification roundtrip."""
    import bcrypt

    passwords = [
        b"simple",
        b"complex_with_numbers_123",
        b"with_special_!@#$%",
    ]

    for password in passwords:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        assert bcrypt.checkpw(password, hashed), f"Failed to verify password: {password}"
        assert not bcrypt.checkpw(password + b"wrong", hashed), f"Incorrectly verified wrong password for: {password}"


def test_bcrypt_password_rehashing():
    """Test that password rehashing works correctly."""
    import bcrypt

    password = b"test_password_123"

    # Create initial hash
    hash1 = bcrypt.hashpw(password, bcrypt.gensalt())

    # Create another hash with different salt
    hash2 = bcrypt.hashpw(password, bcrypt.gensalt())

    # Hashes should be different due to different salts
    assert hash1 != hash2

    # But both should verify correctly
    assert bcrypt.checkpw(password, hash1)
    assert bcrypt.checkpw(password, hash2)
