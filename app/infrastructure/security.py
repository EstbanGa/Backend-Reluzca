"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and email verification.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context - Usamos pbkdf2_sha256 (mismo que Django) para todos los usuarios
# Esto evita el límite de 72 bytes de bcrypt y mantiene compatibilidad total con Django
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "django_pbkdf2_sha256"],
    deprecated="auto"
)

# Email verification signer
signer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="email-verify")


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength.
    Must have:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        bool: True if password is strong enough
    """
    import re
    
    if len(password) < 8:
        return False
    
    if not re.search(r"[A-Z]", password):
        return False
    
    if not re.search(r"[a-z]", password):
        return False
    
    if not re.search(r"\d", password):
        return False
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    
    return True


# ============================================================================
# JWT TOKEN UTILITIES
# ============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Data to encode in token
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_REFRESH_TOKEN_LIFETIME)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Dict[str, Any]: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_tokens(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate both access and refresh tokens for a user.
    
    Args:
        user_data: User data to include in token (user_id, email, rol, etc.)
        
    Returns:
        Dict with access_token and refresh_token
    """
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_LIFETIME * 60  # in seconds
    }


# ============================================================================
# EMAIL VERIFICATION
# ============================================================================

def create_email_verification_token(user_id: str) -> str:
    """
    Create token for email verification.
    
    Args:
        user_id: User UUID as string
        
    Returns:
        str: Verification token
    """
    return signer.dumps(user_id)


def verify_email_token(token: str) -> Optional[str]:
    """
    Verify email verification token.
    
    Args:
        token: Verification token
        
    Returns:
        Optional[str]: User ID if valid, None otherwise
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Max age in seconds
        max_age = settings.EMAIL_VERIFICATION_EXPIRY_HOURS * 3600
        user_id = signer.loads(token, max_age=max_age)
        return user_id
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de verificación ha expirado"
        )
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de verificación inválido"
        )


# ============================================================================
# PASSWORD RESET
# ============================================================================

def create_password_reset_token(user_id: str) -> str:
    """
    Create token for password reset.
    
    Args:
        user_id: User UUID as string
        
    Returns:
        str: Reset token
    """
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="password-reset")
    return serializer.dumps(user_id)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token.
    
    Args:
        token: Reset token
        
    Returns:
        Optional[str]: User ID if valid, None otherwise
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="password-reset")
        # Token valid for 1 hour
        user_id = serializer.loads(token, max_age=3600)
        return user_id
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de restablecimiento ha expirado"
        )
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de restablecimiento inválido"
        )
