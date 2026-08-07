# ==========================================================
# app/routers/users.py
# USER MANAGEMENT
# ==========================================================

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db


router = APIRouter()


# ==========================================================
# ADMIN DEPENDENCY
# ==========================================================

def admin_only(
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )

    return current_user


# ==========================================================
# GET ALL USERS
# GET /users/
# ==========================================================

@router.get(
    "/",
    response_model=List[schemas.UserResponse]
)
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_only)
):
    return (
        db.query(models.User)
        .order_by(models.User.id.asc())
        .all()
    )


# ==========================================================
# CREATE USER
# POST /users/
# ==========================================================

@router.post(
    "/",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_only)
):

    # Check username
    username_exists = (
        db.query(models.User)
        .filter(models.User.username == user_data.username)
        .first()
    )

    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists."
        )

    # Check email
    email_exists = (
        db.query(models.User)
        .filter(models.User.email == user_data.email)
        .first()
    )

    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered."
        )

    # Allowed roles
    allowed_roles = [
        "Admin",
        "Supervisor",
        "Traffic Officer"
    ]

    if user_data.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role."
        )

    # Hash password
    hashed_password = auth.hash_password(
        user_data.password
    )

    # Create user
    new_user = models.User(
        fullname=user_data.fullname,
        username=user_data.username,
        email=user_data.email,
        phone=getattr(user_data, "phone", None),
        role=user_data.role,
        password=hashed_password,
        status="Active"
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create user: {str(e)}"
        )


# ==========================================================
# GET ONE USER
# GET /users/{user_id}
# ==========================================================

@router.get(
    "/{user_id}",
    response_model=schemas.UserResponse
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_only)
):

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return user


# ==========================================================
# DELETE USER
# DELETE /users/{user_id}
# ==========================================================

@router.delete(
    "/{user_id}"
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_only)
):

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Don't allow admin to delete themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account."
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully."
    }