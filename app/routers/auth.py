# ==========================================================
# app/routers/auth.py
# Part 1
# User Registration
# ==========================================================

from datetime import timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas, auth, config
from app.database import get_db

router = APIRouter()

# ==========================================================
# REGISTER USER
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
    # Password Match
    # -----------------------------------
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match."
        )

    # -----------------------------------
    # Username Exists
    # -----------------------------------
    username = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists."
        )

    # -----------------------------------
    # Email Exists
    # -----------------------------------
    email = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if email:
        raise HTTPException(
            status_code=409,
            detail="Email already registered."
        )

    # -----------------------------------
    # Phone Exists
    # -----------------------------------
    if user.phone:
        phone = db.query(models.User).filter(
            models.User.phone == user.phone
        ).first()

        if phone:
            raise HTTPException(
                status_code=409,
                detail="Phone number already exists."
            )

    # -----------------------------------
    # Allowed Roles
    # -----------------------------------
    allowed_roles = [
        "Admin",
        "Supervisor",
        "Traffic Officer"
    ]

    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid Role."
        )

    # -----------------------------------
    # Create User
    # -----------------------------------
    new_user = models.User(
        fullname=user.fullname,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role=user.role,
        password=auth.hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ==========================================================
# CHECK USERNAME
# ==========================================================

@router.get("/check-username/{username}")
def check_username(
    username: str,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if user:
        return {"available": False}
    return {"available": True}


# ==========================================================
# CHECK EMAIL
# ==========================================================

@router.get("/check-email/{email}")
def check_email(
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if user:
        return {"available": False}
    return {"available": True}


# ==========================================================
# LOGIN
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
            detail="Invalid username or password."
        )

    access_token = auth.create_access_token(
        data={
            "sub": user.username,
            "role": user.role
        },
        expires_delta=timedelta(
            minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
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
# CURRENT USER
# ==========================================================

@router.get("/me", response_model=schemas.UserResponse)
def get_logged_user(
    current_user: models.User = Depends(auth.get_current_user)
):
    return current_user


# ==========================================================
# LOGOUT
# ==========================================================

@router.post("/logout")
def logout():
    return {
        "message": "Logout Successful. Please remove the JWT token on the client side."
    }


# ==========================================================
# VERIFY TOKEN
# ==========================================================

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


# ==========================================================
# GET USER PROFILE
# ==========================================================

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
    # Check duplicate email
    email_exists = db.query(models.User).filter(
        models.User.email == profile.email,
        models.User.id != current_user.id
    ).first()

    if email_exists:
        raise HTTPException(
            status_code=409,
            detail="Email already exists."
        )

    # Check duplicate phone
    if profile.phone:
        phone_exists = db.query(models.User).filter(
            models.User.phone == profile.phone,
            models.User.id != current_user.id
        ).first()

        if phone_exists:
            raise HTTPException(
                status_code=409,
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
    # Verify old password
    if not auth.verify_password(
        password_data.old_password,
        current_user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="Old password is incorrect."
        )

    # Check new passwords
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New passwords do not match."
        )

    # Prevent same password
    if auth.verify_password(
        password_data.new_password,
        current_user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the old password."
        )

    current_user.password = auth.hash_password(
        password_data.new_password
    )
    db.commit()
    return {"message": "Password changed successfully."}


# ==========================================================
# DEACTIVATE ACCOUNT
# ==========================================================

@router.put("/deactivate")
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    current_user.status = "Inactive"
    db.commit()
    return {"message": "Account has been deactivated."}


# ==========================================================
# ACTIVATE ACCOUNT
# ==========================================================

@router.put("/activate")
def activate_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    current_user.status = "Active"
    db.commit()
    return {"message": "Account has been activated."}


# ==========================================================
# USER DASHBOARD DETAILS
# ==========================================================

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
# ADMIN - GET ALL USERS
# ==========================================================

@router.get("/admin/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    users = db.query(models.User).all()
    return users


# ==========================================================
# ADMIN - GET USER BY ID
# ==========================================================

@router.get("/admin/user/{user_id}")
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
            status_code=404,
            detail="User not found."
        )
    return user


# ==========================================================
# ADMIN - DELETE USER
# ==========================================================

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
            status_code=404,
            detail="User not found."
        )

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully."}


# ==========================================================
# ADMIN - UPDATE ROLE
# ==========================================================

@router.put("/admin/role/{user_id}")
def update_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    allowed_roles = [
        "Admin",
        "Supervisor",
        "Traffic Officer"
    ]

    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role."
        )

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    user.role = role
    db.commit()
    return {"message": "Role updated successfully."}


# ==========================================================
# ADMIN - ACTIVATE USER
# ==========================================================

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
            status_code=404,
            detail="User not found."
        )

    user.status = "Active"
    db.commit()
    return {"message": "User activated successfully."}


# ==========================================================
# ADMIN - DEACTIVATE USER
# ==========================================================

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
            status_code=404,
            detail="User not found."
        )

    user.status = "Inactive"
    db.commit()
    return {"message": "User deactivated successfully."}


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@router.get("/admin/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    total_users = db.query(models.User).count()

    active_users = db.query(models.User).filter(
        models.User.status == "Active"
    ).count()

    inactive_users = db.query(models.User).filter(
        models.User.status == "Inactive"
    ).count()

    admins = db.query(models.User).filter(
        models.User.role == "Admin"
    ).count()

    supervisors = db.query(models.User).filter(
        models.User.role == "Supervisor"
    ).count()

    officers = db.query(models.User).filter(
        models.User.role == "Traffic Officer"
    ).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "admins": admins,
        "supervisors": supervisors,
        "traffic_officers": officers
    }


# ==========================================================
# SEARCH USER
# ==========================================================

@router.get("/admin/search/{username}")
def search_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    users = db.query(models.User).filter(
        models.User.username.contains(username)
    ).all()
    return users