import secrets
import json
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User, UserRole
from app.schemas.onboarding import StaffInvite
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[dict]) # Simple dict response for MVP
def read_staff(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
) -> Any:
    """
    Retrieve all staff members for the current workspace.
    Owner only.
    """
    staff = db.query(User).filter(
        User.workspace_id == current_user.workspace_id,
        User.role == UserRole.STAFF.value,
        User.is_active == True
    ).all()
    
    # Simple serialization
    return [
        {"id": u.id, "email": u.email, "full_name": u.full_name, "is_active": u.is_active, "role": u.role}
        for u in staff
    ]

@router.post("/invite")
def invite_staff(
    staff_in: StaffInvite,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
) -> Any:
    """
    Invite a new staff member.
    Owner only.
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == staff_in.email).first()
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists in the system."
            )
        else:
            # Reactivate user
            temp_password = secrets.token_urlsafe(8)
            from app.core import security
            hashed_pw = security.get_password_hash(temp_password)
            
            existing_user.hashed_password = hashed_pw
            existing_user.permissions = json.dumps(staff_in.permissions)
            existing_user.is_active = True
            
            # Helper to commit and send email for existing user
            db.commit()
            db.refresh(existing_user)
            from app.services.email import send_staff_invite
            background_tasks.add_task(send_staff_invite, existing_user.email, temp_password)
            
            return {
                "status": "invited",
                "email": existing_user.email, 
                "message": "Staff user reactivated and invited successfully."
            }

    # Create dummy password (system generated)
    temp_password = secrets.token_urlsafe(8)
    from app.core import security
    hashed_pw = security.get_password_hash(temp_password)

    user = User(
        email=staff_in.email,
        hashed_password=hashed_pw,
        role=UserRole.STAFF.value,
        workspace_id=current_user.workspace_id,
        permissions=json.dumps(staff_in.permissions),
        is_active=True,
        full_name="Staff Member" # Placeholder or separate field
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"Generated staff invite for {user.email}. Password: {temp_password}")

    # Send email in background
    from app.services.email import send_staff_invite
    background_tasks.add_task(send_staff_invite, user.email, temp_password)

    return {
        "status": "invited",
        "email": user.email, 
        "message": "Staff invited successfully. Credentials sent via email."
    }

@router.post("/{user_id}/resend-invite")
def resend_staff_invite(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
) -> Any:
    """
    Resend invitation email to a staff member.
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.workspace_id == current_user.workspace_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Staff member not found."
        )
        
    # Generate new password if they haven't logged in yet (optional policy)
    # For now, we'll generate a new one to ensure they can get in
    temp_password = secrets.token_urlsafe(8)
    from app.core import security
    hashed_pw = security.get_password_hash(temp_password)
    
    user.hashed_password = hashed_pw
    db.commit()

    # Send email
    from app.services.email import send_staff_invite
    background_tasks.add_task(send_staff_invite, user.email, temp_password)

    return {"message": "Invitation resent successfully."}


@router.delete("/{user_id}")
def remove_staff(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
) -> Any:
    """
    Remove a staff member from the workspace.
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.workspace_id == current_user.workspace_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Staff member not found."
        )

    # Soft delete or hard delete? MVP: Hard delete for simplicity or set inactive
    # Let's set to inactive to preserve history (bookings etc)
    user.is_active = False
    # Optionally remove from workspace to "hide" them from list, or just show as inactive
    # For "Remove", users usually expect them to disappear.
    # Let's rename their email to free it up? No, that's messy.
    # Let's just set inactive and maybe we hide inactive ones in UI or show them in a separate tab.
    # But for MVP, let's actually DELETE them if they have no bookings, else Deactivate?
    # Simpler: Just Deactivate.
    
    db.commit()
    
    return {"message": "Staff member removed (deactivated)."}
