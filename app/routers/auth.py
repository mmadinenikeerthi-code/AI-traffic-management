# app/routers/auth.py

from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth, config, models, schemas
from app.database import get_db

router = APIRouter()


# ==========================================================
# USER REGISTRATION
# ==========================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserResponse
)
def register_user(
    user: schemas.UserRegister,
    db: Session = Depends(get_db)
):
    # -----------------------------------
    # Password Match Validation
    # -----------------------------------
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    # -----------------------------------
    # Check Duplicate Username
    # -----------------------------------
    existing_username = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists."
        )

    # -----------------------------------
    # Check Duplicate Email
    # -----------------------------------
    existing_email = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered."
        )

    # -----------------------------------
    # Check Duplicate Phone
    # -----------------------------------
    if user.phone:
        existing_phone = db.query(models.User).filter(
            models.User.phone == user.phone
        ).first()

        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already registered."
            )

    # -----------------------------------
    # Allowed Role Validation
    # -----------------------------------
    allowed_roles = ["Admin", "Supervisor", "Traffic Officer"]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Role selected."
        )

    # -----------------------------------
    # Hash Password & Persist Record
    # -----------------------------------
    hashed_pwd = auth.hash_password(user.password)

    new_user = models.User(
        fullname=user.fullname,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role=user.role,
        password=hashed_pwd,
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
            detail=f"Database error during registration: {str(e)}"
        )


# ==========================================================
# AVAILABILITY VERIFICATION ENDPOINTS
# ==========================================================

@router.get("/check-username/{username}")
def check_username(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()
    return {"available": user is None}


@router.get("/check-email/{email}")
def check_email(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == email
    ).first()
    return {"available": user is None}


# ==========================================================
# LOGIN & TOKEN AUTHENTICATION
# ==========================================================

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(
        form_data.username,
        form_data.password,
        db
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(
        data={
            "sub": user.username,
            "role": user.role
        },
        expires_delta=timedelta(
            minutes=getattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
        )
    )

    return {
        "message": "Login Successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "fullname": user.fullname,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }
    }


# ==========================================================
# LOGOUT
# ==========================================================

@router.post("/logout")
def logout():
    return {
        "message": "Logout Successful. Please remove the JWT token on the client side."
    }


# ==========================================================
# TOKEN VERIFICATION & CURRENT USER PROFILE
# ==========================================================

@router.get("/me", response_model=schemas.UserResponse)
def get_logged_user(
    current_user: models.User = Depends(auth.get_current_user)
):
    return current_user


@router.get("/verify-token")
def verify_token(
    current_user: models.User = Depends(auth.get_current_user)
):
    return {
        "valid": True,
        "username": current_user.username,
        "role": current_user.role,
        "status": current_user.status
    }


@router.get("/profile", response_model=schemas.UserResponse)
def get_profile(
    current_user: models.User = Depends(auth.get_current_user)
):
    return current_user


# ==========================================================
# UPDATE PROFILE
# ==========================================================

@router.put("/profile", response_model=schemas.UserResponse)
def update_profile(
    profile: schemas.UpdateProfile,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify Email Uniqueness
    email_exists = db.query(models.User).filter(
        models.User.email == profile.email,
        models.User.id != current_user.id
    ).first()

    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists."
        )

    # Verify Phone Uniqueness
    if profile.phone:
        phone_exists = db.query(models.User).filter(
            models.User.phone == profile.phone,
            models.User.id != current_user.id
        ).first()

        if phone_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already exists."
            )

    current_user.fullname = profile.fullname
    current_user.email = profile.email
    current_user.phone = profile.phone

    db.commit()
    db.refresh(current_user)
    return current_user


# ==========================================================
# CHANGE PASSWORD
# ==========================================================

@router.put("/change-password")
def change_password(
    password_data: schemas.ChangePassword,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.verify_password(
        password_data.old_password,
        current_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect."
        )

    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match."
        )

    if auth.verify_password(
        password_data.new_password,
        current_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password."
        )

    current_user.password = auth.hash_password(
        password_data.new_password
    )
    db.commit()
    return {"message": "Password changed successfully."}


# ==========================================================
# ACCOUNT ACTIVATION / DEACTIVATION
# ==========================================================

@router.put("/deactivate")
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    current_user.status = "Inactive"
    db.commit()
    return {"message": "Account has been deactivated."}


@router.put("/activate")
def activate_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    current_user.status = "Active"
    db.commit()
    return {"message": "Account has been activated."}


@router.get("/dashboard-info")
def dashboard_info(
    current_user: models.User = Depends(auth.get_current_user)
):
    return {
        "username": current_user.username,
        "fullname": current_user.fullname,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status
    }


# ==========================================================
# ADMIN - USER MANAGEMENT ENDPOINTS
# ==========================================================

@router.get("/admin/users", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    return db.query(models.User).all()


@router.get("/admin/user/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user


@router.delete("/admin/delete/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own administrative account."
        )

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully."}


@router.put("/admin/role/{user_id}")
def update_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    allowed_roles = ["Admin", "Supervisor", "Traffic Officer"]

    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role."
        )

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.role = role
    db.commit()
    return {"message": "Role updated successfully."}


@router.put("/admin/activate/{user_id}")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.status = "Active"
    db.commit()
    return {"message": "User activated successfully."}


@router.put("/admin/deactivate/{user_id}")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.status = "Inactive"
    db.commit()
    return {"message": "User deactivated successfully."}


@router.get("/admin/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    total_users = db.query(models.User).count()
    active_users = db.query(models.User).filter(models.User.status == "Active").count()
    inactive_users = db.query(models.User).filter(models.User.status == "Inactive").count()
    admins = db.query(models.User).filter(models.User.role == "Admin").count()
    supervisors = db.query(models.User).filter(models.User.role == "Supervisor").count()
    officers = db.query(models.User).filter(models.User.role == "Traffic Officer").count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "admins": admins,
        "supervisors": supervisors,
        "traffic_officers": officers
    }


@router.get("/admin/search/{username}", response_model=List[schemas.UserResponse])
def search_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    users = db.query(models.User).filter(
        models.User.username.contains(username)
    ).all()
    return users