from sqlalchemy.orm import Session

from models.models import Inspection
from schemas.schemas import InspectionCreate, InspectionUpdate


def create_inspection(db: Session, inspection: InspectionCreate):
    db_inspection = Inspection(**inspection.model_dump())
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection


def get_inspections(db: Session):
    return db.query(Inspection).all()


def get_inspection(db: Session, inspection_id: int):
    return db.query(Inspection).filter(Inspection.id == inspection_id).first()


def update_inspection(
    db: Session,
    inspection_id: int,
    inspection: InspectionUpdate
):
    db_inspection = get_inspection(db, inspection_id)

    if not db_inspection:
        return None

    for key, value in inspection.model_dump().items():
        setattr(db_inspection, key, value)

    db.commit()
    db.refresh(db_inspection)
    return db_inspection


def delete_inspection(db: Session, inspection_id: int):
    db_inspection = get_inspection(db, inspection_id)

    if not db_inspection:
        return None

    db.delete(db_inspection)
    db.commit()
    return db_inspection