from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.contact import Contact
from app.models.booking import Booking
from app.models.service import Service

router = APIRouter()

class ConvertLeadRequest(BaseModel):
    service_id: int
    booking_datetime: str
    notes: str = ""

@router.post("/leads/{lead_id}/convert-to-booking")
def convert_lead_to_booking(
    lead_id: int,
    conversion_data: ConvertLeadRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Convert a lead to a booking
    """
    # 1. Get the lead
    lead = db.query(Contact).filter(
        Contact.id == lead_id,
        Contact.workspace_id == current_user.workspace_id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # 2. Verify service exists
    service = db.query(Service).filter(
        Service.id == conversion_data.service_id,
        Service.workspace_id == current_user.workspace_id
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # 3. Create booking
    booking = Booking(
        workspace_id=current_user.workspace_id,
        contact_id=lead.id,
        service_id=service.id,
        booking_datetime=conversion_data.booking_datetime,
        status="pending",
        notes=conversion_data.notes
    )
    db.add(booking)
    
    # 4. Update lead status
    lead.status = "booked"
    
    db.commit()
    db.refresh(booking)
    
    return {
        "message": "Lead converted to booking successfully",
        "booking_id": booking.id,
        "lead_id": lead.id
    }
