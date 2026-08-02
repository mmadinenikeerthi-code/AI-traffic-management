# app/auth.py

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import config, models
from app.database import get_db

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def hash_password(password: str) -> str:
    """Hashes a plain text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a hashed password context."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generates a signed JWT access token with an expiration timestamp."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=getattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        config.SECRET_KEY,
        algorithm=config.ALGORITHM
    )

    return encoded_jwt


def authenticate_user(username: str, password: str, db: Session) -> Optional[models.User]:
    """Authenticates user credentials against database record and active status."""
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    user_status = getattr(user, "status", "Active")
    if user_status != "Active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled or inactive."
        )

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """Extracts and verifies JWT bearer token to inject current User object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM]
        )
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if user is None:
        raise credentials_exception

    return user


# ==========================================================
# ROLE-BASED ACCESS CONTROL (RBAC) DEPENDENCIES
# ==========================================================

def admin_required(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )
    return current_user


def supervisor_required(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if current_user.role not in ["Admin", "Supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor access required."
        )
    return current_user


def officer_required(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if current_user.role not in ["Admin", "Supervisor", "Traffic Officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Traffic Officer access required."
        )
    return current_user


def login_response(user: models.User) -> dict:
    """Helper formatting standardized login token payload."""
    token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "fullname": user.fullname,
        "role": user.role
    }