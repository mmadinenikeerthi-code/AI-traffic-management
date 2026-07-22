# app/routers/profile.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db

router = APIRouter()


@router.get("/", response_model=schemas.UserOut)
def get_profile(
    current_user: models.User = Depends(auth.get_current_user)
):
    return current_user


@router.put("/update", response_model=schemas.UserOut)
def update_profile(
    profile_data: schemas.UpdateProfile,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if profile_data.email != current_user.email:
        existing_email = db.query(models.User).filter(
            models.User.email == profile_data.email,
            models.User.id != current_user.id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already in use by another account"
            )

    if profile_data.phone:
        existing_phone = db.query(models.User).filter(
            models.User.phone == profile_data.phone,
            models.User.id != current_user.id
        ).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is already in use by another account"
            )

    current_user.fullname = profile_data.fullname
    current_user.email = profile_data.email
    current_user.phone = profile_data.phone

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/change-password")
def change_password(
    password_data: schemas.ChangePassword,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.verify_password(password_data.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation password do not match"
        )

    if auth.verify_password(password_data.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password"
        )

    current_user.password = auth.hash_password(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}
