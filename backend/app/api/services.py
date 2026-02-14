from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.service import Service
from app.models.user import User

router = APIRouter()

# --- Schemas ---
class ServiceBase(BaseModel):
    name: str
    duration_minutes: int
    price: Optional[float] = 0.0
    description: Optional[str] = None
    availability: Optional[dict] = {}
    location: Optional[str] = "Business Location"
    inventory_item_id: Optional[int] = None
    inventory_quantity_required: Optional[int] = 0

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    availability: Optional[dict] = None
    location: Optional[str] = None
    inventory_item_id: Optional[int] = None
    inventory_quantity_required: Optional[int] = None

class ServiceOut(ServiceBase):
    id: int
    workspace_id: int

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/", response_model=List[ServiceOut])
def list_services(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all services for the workspace."""
    services = db.query(Service).filter(Service.workspace_id == current_user.workspace_id).all()
    return services

@router.post("/", response_model=ServiceOut)
def create_service(
    service_in: ServiceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Create a new service (Owner only)."""
    avail = service_in.availability
    if not avail:
        avail = {
            "mon": ["09:00-17:00"],
            "tue": ["09:00-17:00"],
            "wed": ["09:00-17:00"],
            "thu": ["09:00-17:00"],
            "fri": ["09:00-17:00"]
        }

    service = Service(
        **service_in.model_dump(exclude={"availability"}),
        availability=avail,
        workspace_id=current_user.workspace_id
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

@router.patch("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    service_in: ServiceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Update a service."""
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.workspace_id == current_user.workspace_id
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    update_data = service_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
        
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

@router.delete("/{service_id}", status_code=204)
def delete_service(
    service_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Delete a service."""
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.workspace_id == current_user.workspace_id
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    db.delete(service)
    db.commit()
    return None
