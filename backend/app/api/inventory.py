"""Inventory CRUD API — list, create, update, delete inventory items."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.api import deps
from app.models.inventory import InventoryItem
from app.models.user import User

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────
class InventoryItemOut(BaseModel):
    id: int
    name: str
    quantity: int
    threshold: int

    class Config:
        from_attributes = True


class InventoryItemCreate(BaseModel):
    name: str
    quantity: int = 0
    threshold: int = 5


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    threshold: Optional[int] = None


# ── Endpoints ────────────────────────────────────────────
@router.get("/", response_model=List[InventoryItemOut])
def list_inventory(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List all inventory items for the user's workspace."""
    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.workspace_id == current_user.workspace_id)
        .order_by(InventoryItem.name)
        .all()
    )
    return items


@router.post("/", response_model=InventoryItemOut, status_code=201)
def create_inventory_item(
    item_in: InventoryItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Create a new inventory item (owner only)."""
    item = InventoryItem(
        name=item_in.name,
        quantity=item_in.quantity,
        threshold=item_in.threshold,
        workspace_id=current_user.workspace_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(
    item_id: int,
    item_in: InventoryItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Update an inventory item's name, quantity, or threshold (owner only)."""
    item = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.id == item_id,
            InventoryItem.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_in.name is not None:
        item.name = item_in.name
    if item_in.quantity is not None:
        item.quantity = item_in.quantity
    if item_in.threshold is not None:
        item.threshold = item_in.threshold

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner),
):
    """Delete an inventory item (owner only)."""
    item = (
        db.query(InventoryItem)
        .filter(
            InventoryItem.id == item_id,
            InventoryItem.workspace_id == current_user.workspace_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return None
