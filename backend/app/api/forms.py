"""Forms CRUD API — list, create, update, delete intake forms."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any

from app.api import deps
from app.models.form import Form
from app.models.user import User

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────
class FormFieldSchema(BaseModel):
    name: str
    label: str
    type: str = "text"  # text, textarea, email, phone, select
    required: bool = False
    options: Optional[List[str]] = None  # for select fields


class FormOut(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    is_public: bool
    fields: Any  # JSON list of FormFieldSchema dicts
    google_form_url: Optional[str] = None

    class Config:
        from_attributes = True


class FormCreate(BaseModel):
    name: str
    type: str = "intake"
    fields: List[FormFieldSchema] = []
    google_form_url: Optional[str] = None


class FormUpdate(BaseModel):
    name: Optional[str] = None
    fields: Optional[List[FormFieldSchema]] = None
    google_form_url: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────
@router.get("/", response_model=List[FormOut])
def list_forms(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all forms for the user's workspace."""
    forms = (
        db.query(Form)
        .filter(Form.workspace_id == current_user.workspace_id)
        .order_by(Form.name)
        .all()
    )
    # Attach google_form_url if the column exists
    result = []
    for f in forms:
        out = FormOut(
            id=f.id,
            name=f.name,
            type=f.type,
            is_public=f.is_public,
            fields=f.fields or [],
            google_form_url=getattr(f, 'google_form_url', None),
        )
        result.append(out)
    return result


@router.post("/", response_model=FormOut, status_code=201)
def create_form(
    form_in: FormCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Create a new form (owner only)."""
    form = Form(
        name=form_in.name,
        type=form_in.type,
        is_public=True,
        fields=[f.model_dump() for f in form_in.fields],
        workspace_id=current_user.workspace_id,
    )
    # Set google_form_url if the column exists
    if form_in.google_form_url and hasattr(form, 'google_form_url'):
        form.google_form_url = form_in.google_form_url

    db.add(form)
    db.commit()
    db.refresh(form)
    return FormOut(
        id=form.id,
        name=form.name,
        type=form.type,
        is_public=form.is_public,
        fields=form.fields or [],
        google_form_url=getattr(form, 'google_form_url', None),
    )


@router.patch("/{form_id}", response_model=FormOut)
def update_form(
    form_id: int,
    form_in: FormUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Update a form (owner only)."""
    form = (
        db.query(Form)
        .filter(
            Form.id == form_id,
            Form.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    if form_in.name is not None:
        form.name = form_in.name
    if form_in.fields is not None:
        form.fields = [f.model_dump() for f in form_in.fields]
    if form_in.google_form_url is not None and hasattr(form, 'google_form_url'):
        form.google_form_url = form_in.google_form_url

    db.commit()
    db.refresh(form)
    return FormOut(
        id=form.id,
        name=form.name,
        type=form.type,
        is_public=form.is_public,
        fields=form.fields or [],
        google_form_url=getattr(form, 'google_form_url', None),
    )


@router.delete("/{form_id}", status_code=204)
def delete_form(
    form_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Delete a form (owner only)."""
    form = (
        db.query(Form)
        .filter(
            Form.id == form_id,
            Form.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    db.delete(form)
    db.commit()
    return None
