from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from crud.crud import (
    create_inspection,
    delete_inspection,
    get_inspection,
    get_inspections,
    update_inspection,
)
from database.database import get_db
from jwt_auth import get_current_user, require_roles
from schemas.schemas import InspectionCreate, InspectionResponse, InspectionUpdate

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.post("/", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
def create(
    inspection: InspectionCreate, db: Session = Depends(get_db), _user=Depends(require_roles("writer", "moderator"))
):
    return create_inspection(db, inspection)


@router.get("/", response_model=list[InspectionResponse])
def read_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_inspections(db, skip=skip, limit=limit)


@router.get("/{inspection_id}", response_model=InspectionResponse)
def read_one(inspection_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    inspection = get_inspection(db, inspection_id)

    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    return inspection


@router.put("/{inspection_id}", response_model=InspectionResponse)
def update(
    inspection_id: int,
    inspection: InspectionUpdate,
    db: Session = Depends(get_db),
    _user=Depends(require_roles("writer", "moderator")),
):
    updated = update_inspection(db, inspection_id, inspection)

    if not updated:
        raise HTTPException(status_code=404, detail="Inspection not found")

    return updated


@router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(inspection_id: int, db: Session = Depends(get_db), _user=Depends(require_roles("moderator"))):
    deleted = delete_inspection(db, inspection_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Inspection not found")

    return None
