from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from schemas.schemas import InspectionCreate, InspectionResponse, InspectionUpdate
from crud.crud import (
    create_inspection,
    delete_inspection,
    get_inspection,
    get_inspections,
    update_inspection,
)

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.post("/", response_model=InspectionResponse)
def create(inspection: InspectionCreate, db: Session = Depends(get_db)):
    return create_inspection(db, inspection)


@router.get("/", response_model=list[InspectionResponse])
def read_all(db: Session = Depends(get_db)):
    return get_inspections(db)


@router.get("/{inspection_id}", response_model=InspectionResponse)
def read_one(inspection_id: int, db: Session = Depends(get_db)):
    inspection = get_inspection(db, inspection_id)

    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    return inspection


@router.put("/{inspection_id}", response_model=InspectionResponse)
def update(
    inspection_id: int,
    inspection: InspectionUpdate,
    db: Session = Depends(get_db),
):
    updated = update_inspection(db, inspection_id, inspection)

    if not updated:
        raise HTTPException(status_code=404, detail="Inspection not found")

    return updated


@router.delete("/{inspection_id}")
def delete(inspection_id: int, db: Session = Depends(get_db)):
    deleted = delete_inspection(db, inspection_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Inspection not found")

    return {"message": "Inspection deleted successfully"}