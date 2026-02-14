from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
import jwt
import json
import secrets
# from passlib.context import CryptContext # Not used directly here
from app.core import security
from app.api import deps # Use centralized deps

from app.schemas.onboarding import (
    WorkspaceCreate, EmailConfig, ServiceCreate, FormCreate,
    InventoryCreate, StaffInvite, Token
)
from app.models.workspace import Workspace
from app.models.user import User, UserRole
from app.models.service import Service
from app.models.form import Form
from app.models.inventory import InventoryItem
from app.services.email import send_test_email

router = APIRouter()

# 1. Create Workspace (Public)
@router.post("/workspaces")
def create_workspace(workspace_in: WorkspaceCreate, db: Session = Depends(deps.get_db)):
    # 1. Create Workspace (is_active=False)
    # Generate slug
    slug = workspace_in.name.lower().replace(" ", "-") + "-" + secrets.token_hex(2)
    
    workspace = Workspace(
        name=workspace_in.name,
        slug=slug,
        address=workspace_in.address,
        timezone=workspace_in.timezone,
        contact_email=workspace_in.contact_email,
        is_active=False
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    # 2. Create Owner User
    hashed_password = security.get_password_hash(workspace_in.owner_password)
    user = User(
        email=workspace_in.owner_email,
        hashed_password=hashed_password,
        role=UserRole.OWNER.value,
        workspace_id=workspace.id,
        is_active=True,
        full_name="Owner" # Placeholder
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. Generate JWT
    access_token = security.create_access_token(
        subject=user.id,
        workspace_id=workspace.id
    )
    
    return {"workspace_id": workspace.id, "slug": workspace.slug, "access_token": access_token}

# 2. Configure Email (Owner)
@router.put("/workspaces/{workspace_id}/config/email")
def configure_email(
    workspace_id: int,
    config: EmailConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner)
):
    if current_user.workspace_id != workspace_id:
         raise HTTPException(status_code=403, detail="Not authorized for this workspace")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    background_tasks.add_task(send_test_email, config)

    workspace.email_config = config.dict()
    db.add(workspace)
    db.commit()

    return {"status": "verification_sent"}

# 3. Create Contact Form (Owner)
@router.post("/workspaces/{workspace_id}/forms/contact")
def create_contact_form(
    workspace_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner)
):
    if current_user.workspace_id != workspace_id:
         raise HTTPException(status_code=403, detail="Not authorized")

    form = Form(
        name="Contact Form",
        type="contact",
        is_public=True,
        fields=[
            {"name": "name", "type": "text", "required": True},
            {"name": "email", "type": "email", "required": True},
            {"name": "phone", "type": "tel", "required": False},
            {"name": "message", "type": "textarea", "required": True}
        ],
        workspace_id=workspace_id
    )
    db.add(form)
    db.commit()
    db.refresh(form)
    
    return {"form_id": form.id, "public_url": f"/forms/{form.id}"}

# 4. Create Services (Owner)
@router.post("/workspaces/{workspace_id}/services")
def create_services(
    workspace_id: int,
    services_in: List[ServiceCreate],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner)
):
    if current_user.workspace_id != workspace_id:
         raise HTTPException(status_code=403, detail="Not authorized")

    service_ids = []
    for s in services_in:
        service = Service(
            name=s.name,
            duration_minutes=s.duration_minutes,
            availability=s.availability,
            location=s.location,
            workspace_id=workspace_id,
            inventory_item_id=s.inventory_item_id,
            inventory_quantity_required=s.inventory_quantity_required
        )
        db.add(service)
        db.flush() 
        service_ids.append(service.id)
        
    db.commit()
    return {"count": len(service_ids), "service_ids": service_ids}

# 5. Create Post-Booking Form (Owner)
@router.post("/workspaces/{workspace_id}/forms/post-booking")
def create_post_booking_form(
    workspace_id: int,
    form_in: FormCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner)
):
    if current_user.workspace_id != workspace_id:
         raise HTTPException(status_code=403, detail="Not authorized")

    fields_data = {
        "linked_services": form_in.linked_services,
        "questions": [] 
    }

    form = Form(
        name="Post Booking Form",
        type="post_booking",
        is_public=False,
        fields=fields_data,
        workspace_id=workspace_id
    )
    if form_in.name:
        form.name = form_in.name

    db.add(form)
    db.commit()
    db.refresh(form)
    
    return {"form_id": form.id}

# 6. Create Inventory (Owner)
@router.post("/workspaces/{workspace_id}/inventory")
def create_inventory(
    workspace_id: int,
    inventory_in: List[InventoryCreate],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner)
):
    if current_user.workspace_id != workspace_id:
         raise HTTPException(status_code=403, detail="Not authorized")

    count = 0
    created_items = []
    for i in inventory_in:
        item = InventoryItem(
            name=i.name,
            quantity=i.quantity_available,
            threshold=i.low_threshold,
            workspace_id=workspace_id
        )
        db.add(item)
        db.flush() # Get ID
        created_items.append({"id": item.id, "name": item.name})
        count += 1
    db.commit()
    return {"count": count, "items": created_items}

# 7. Invite Staff (DEPRECATED/Moved to staff.py, but kept for onboarding flow consistency if called from existing frontend)
# We will protect it with Owner check strictly.
@router.post("/workspaces/{workspace_id}/staff")
def invite_staff_onboarding(
    workspace_id: int,
    staff_in: List[StaffInvite],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner)
):
    if current_user.workspace_id != workspace_id:
         raise HTTPException(status_code=403, detail="Not authorized")

    invited_count = 0
    for s in staff_in:
        if db.query(User).filter(User.email == s.email).first():
            continue 
            
        temp_password = secrets.token_urlsafe(8)
        hashed_pw = security.get_password_hash(temp_password)
        
        user = User(
            email=s.email,
            hashed_password=hashed_pw,
            role=UserRole.STAFF.value,
            workspace_id=workspace_id,
            permissions=json.dumps(s.permissions),
            is_active=True 
        )
        db.add(user)
        invited_count += 1
        
    db.commit()
    return {"invited_count": invited_count}

# 8. Activate Workspace (Owner)
@router.post("/workspaces/{workspace_id}/activate")
def activate_workspace(
    workspace_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner)
):
    if current_user.workspace_id != workspace_id:
         raise HTTPException(status_code=403, detail="Not authorized")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    errors = []
    
    if not workspace.email_config:
        errors.append("email")
        
    service_count = db.query(Service).filter(Service.workspace_id == workspace_id).count()
    if service_count < 1:
        errors.append("services")
        
    services = db.query(Service).filter(Service.workspace_id == workspace_id).all()
    has_availability = False
    for s in services:
        if s.availability:
            has_availability = True
            break
    
    if not has_availability:
        errors.append("availability")
        
    if errors:
        raise HTTPException(status_code=400, detail=f"Missing: {', '.join(errors)}")
        
    workspace.is_active = True
    db.add(workspace)
    db.commit()
    
    return {"status": "activated"}
