# app/auth.py

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, config

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        config.SECRET_KEY,
        algorithm=config.ALGORITHM
    )

    return encoded_jwt


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    if user.status != "Active":
        raise HTTPException(
            status_code=403,
            detail="Account Disabled"
        )

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM]
        )
        username = payload.get("sub")

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


def admin_required(
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin Access Required"
        )
    return current_user


def supervisor_required(
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["Admin", "Supervisor"]:
        raise HTTPException(
            status_code=403,
            detail="Supervisor Access Required"
        )
    return current_user


def officer_required(
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role not in ["Admin", "Supervisor", "Traffic Officer"]:
        raise HTTPException(
            status_code=403,
            detail="Traffic Officer Access Required"
        )
    return current_user


def login_response(user):
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
