import pytest
from app.config import get_settings

def test_auth_settings_exists():
    settings = get_settings()
    assert hasattr(settings, 'secret_key')
    assert hasattr(settings, 'password_min_length')
    assert hasattr(settings, 'jwt_expire_days')
    assert hasattr(settings, 'short_term_session_limit')
    assert hasattr(settings, 'long_term_memory_top_k')
    assert hasattr(settings, 'enable_memory_extraction')

def test_auth_default_values():
    settings = get_settings()
    assert settings.password_min_length == 6
    assert settings.jwt_expire_days == 7
    assert settings.short_term_session_limit == 3
    assert settings.long_term_memory_top_k == 5
    assert settings.enable_memory_extraction is True
