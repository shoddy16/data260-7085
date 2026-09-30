from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from database.database import get_db
from models.models import Inspection, InspectionRelated

router = APIRouter(
    prefix="/n-plus-one",
    tags=["N+1 Measurement"]
)


@router.get("/naive")
def naive_n_plus_one(
    page_size: int = Query(10),
    db: Session = Depends(get_db)
):
    inspections = db.query(Inspection).limit(page_size).all()

    results = []

    for inspection in inspections:
        related = (
            db.query(InspectionRelated)
            .filter(InspectionRelated.inspection_id == inspection.id)
            .all()
        )

        results.append({
            "id": inspection.id,
            "restaurantName": inspection.restaurantName,
            "location": inspection.location,
            "related_records": [
                {
                    "id": record.id,
                    "note": record.note
                }
                for record in related
            ]
        })

    return {
        "pattern": "Naive N+1",
        "page_size": page_size,
        "inspection_count": len(inspections),
        "queries": 1 + len(inspections),
        "results": results
    }


@router.get("/fixed")
def fixed_n_plus_one(
    page_size: int = Query(10),
    db: Session = Depends(get_db)
):
    inspections = (
        db.query(Inspection)
        .options(joinedload(Inspection.related_records))
        .limit(page_size)
        .all()
    )

    results = [
        {
            "id": inspection.id,
            "restaurantName": inspection.restaurantName,
            "location": inspection.location,
            "related_records": [
                {
                    "id": record.id,
                    "note": record.note
                }
                for record in inspection.related_records
            ]
        }
        for inspection in inspections
    ]

    return {
        "pattern": "Fixed",
        "page_size": page_size,
        "inspection_count": len(inspections),
        "queries": 1,
        "results": results
    }