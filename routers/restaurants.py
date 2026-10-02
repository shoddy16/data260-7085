from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from crud.crud import (
    create_restaurant,
    delete_restaurant,
    get_inspections_by_restaurant,
    get_restaurant,
    get_restaurants,
    update_restaurant,
)
from database.database import get_db
from schemas.schemas import (
    InspectionResponse,
    RestaurantCreate,
    RestaurantResponse,
    RestaurantUpdate,
)


router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post("/", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create(payload: RestaurantCreate, db: Session = Depends(get_db)):
    return create_restaurant(db, payload)


@router.get("/", response_model=list[RestaurantResponse])
def read_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_restaurants(db, skip=skip, limit=limit)


@router.get("/{restaurant_id}/inspections", response_model=list[InspectionResponse])
def read_inspections(
    restaurant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if not get_restaurant(db, restaurant_id):
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return get_inspections_by_restaurant(db, restaurant_id, skip=skip, limit=limit)


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def read_one(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update(
    restaurant_id: int,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
):
    restaurant = update_restaurant(db, restaurant_id, payload)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = delete_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return None
