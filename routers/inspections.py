from fastapi import APIRouter, Depends, HTTPException, Query, status
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


@router.post("/", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
def create(inspection: InspectionCreate, db: Session = Depends(get_db)):
    return create_inspection(db, inspection)


@router.get("/", response_model=list[InspectionResponse])
def read_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_inspections(db, skip=skip, limit=limit)


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


@router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(inspection_id: int, db: Session = Depends(get_db)):
    deleted = delete_inspection(db, inspection_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Inspection not found")

    return None
