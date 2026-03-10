"""JWT Token Service for creating and verifying access tokens."""

from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import get_settings


class TokenService:
    """Service for creating and verifying JWT tokens."""

    def __init__(self):
        """Initialize token service with settings."""
        settings = get_settings()
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.expire_days = settings.jwt_expire_days

    def create_access_token(self, user_id: str) -> str:
        """
        Create a JWT access token for a user.

        Args:
            user_id: The user ID to include in the token

        Returns:
            Encoded JWT token string
        """
        expire = datetime.utcnow() + timedelta(days=self.expire_days)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        """
        Verify and decode a JWT token.

        Args:
            token: The JWT token string to verify

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise ValueError("Invalid token")
