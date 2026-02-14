from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models.contact import Contact
from app.models.workspace import Workspace
from app.schemas.signup import LeadFormSubmission, LeadResponse, UpdateLeadStatus
from app.services.email import send_welcome_email
from app.core.rate_limit import public_rate_limiter

router = APIRouter()

@router.post("/workspaces/{workspace_slug}/lead-form")
def submit_lead_form(
    request: Request,
    workspace_slug: str,
    lead_data: LeadFormSubmission,
    db: Session = Depends(deps.get_db)
):
    """
    Public endpoint for lead capture form submission
    """
    public_rate_limiter.check(request)
    # 1. Find workspace
    workspace = db.query(Workspace).filter(Workspace.slug == workspace_slug).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # 2. Check if contact already exists
    existing_contact = db.query(Contact).filter(
        Contact.email == lead_data.email,
        Contact.workspace_id == workspace.id
    ).first()
    
    if existing_contact:
        # Update existing contact
        existing_contact.first_name = lead_data.first_name
        existing_contact.last_name = lead_data.last_name
        existing_contact.phone = lead_data.phone
        existing_contact.full_name = f"{lead_data.first_name} {lead_data.last_name}"
        if existing_contact.status == "new":
            existing_contact.status = "contacted"
        db.commit()
        contact = existing_contact
    else:
        # 3. Create new lead
        contact = Contact(
            workspace_id=workspace.id,
            email=lead_data.email,
            first_name=lead_data.first_name,
            last_name=lead_data.last_name,
            full_name=f"{lead_data.first_name} {lead_data.last_name}",
            phone=lead_data.phone,
            status="new",
            source="form"
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
    
    # 4. Send welcome email (async in background)
    try:
        send_welcome_email(
            to_email=contact.email,
            contact_name=contact.full_name,
            workspace_name=workspace.name
        )
    except Exception as e:
        # Don't fail the request if email fails
        print(f"Failed to send welcome email: {e}")
    
    return {
        "message": "Thank you! We'll be in touch soon.",
        "contact_id": contact.id
    }

@router.get("/leads", response_model=List[LeadResponse])
def get_leads(
    status: str = None,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get all leads for the workspace
    """
    query = db.query(Contact).filter(Contact.workspace_id == current_user.workspace_id)
    
    if status:
        query = query.filter(Contact.status == status)
    
    leads = query.order_by(Contact.created_at.desc()).all()
    
    return [
        LeadResponse(
            id=lead.id,
            first_name=lead.first_name or "",
            last_name=lead.last_name or "",
            email=lead.email,
            phone=lead.phone,
            status=lead.status or "new",
            source=lead.source or "manual",
            created_at=lead.created_at.isoformat() if lead.created_at else ""
        )
        for lead in leads
    ]

@router.patch("/leads/{lead_id}/status")
def update_lead_status(
    lead_id: int,
    status_update: UpdateLeadStatus,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Update lead status
    """
    lead = db.query(Contact).filter(
        Contact.id == lead_id,
        Contact.workspace_id == current_user.workspace_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.status = status_update.status
    db.commit()
    
    return {"message": "Status updated successfully"}
