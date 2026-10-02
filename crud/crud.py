from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.models import Inspection, Restaurant
from schemas.schemas import (
    InspectionCreate,
    InspectionUpdate,
    RestaurantCreate,
    RestaurantUpdate,
)


def _new_restaurant_code() -> str:
    return f"s7085-r-{uuid4().hex[:8]}"


def _new_inspection_code() -> str:
    return f"s7085-i-{uuid4().hex[:8]}"


def create_restaurant(db: Session, restaurant: RestaurantCreate):
    values = restaurant.model_dump()
    values["code"] = values.get("code") or _new_restaurant_code()
    db_restaurant = Restaurant(**values)
    db.add(db_restaurant)
    try:
        db.commit()
        db.refresh(db_restaurant)
        return db_restaurant
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Restaurant code must be unique.") from exc


def get_restaurants(db: Session, skip: int = 0, limit: int = 50):
    return (
        db.query(Restaurant)
        .order_by(Restaurant.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_restaurant(db: Session, restaurant_id: int):
    return db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()


def update_restaurant(db: Session, restaurant_id: int, restaurant: RestaurantUpdate):
    db_restaurant = get_restaurant(db, restaurant_id)
    if not db_restaurant:
        return None

    values = restaurant.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(db_restaurant, key, value)
    if "name" in values or "location" in values:
        for inspection in db_restaurant.inspections:
            inspection.restaurantName = db_restaurant.name
            inspection.location = db_restaurant.location
    try:
        db.commit()
        db.refresh(db_restaurant)
        return db_restaurant
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Restaurant code must be unique.") from exc


def delete_restaurant(db: Session, restaurant_id: int):
    db_restaurant = get_restaurant(db, restaurant_id)
    if not db_restaurant:
        return None
    if db.query(Inspection.id).filter(Inspection.restaurant_id == restaurant_id).first():
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a restaurant while inspections are associated with it.",
        )
    db.delete(db_restaurant)
    db.commit()
    return db_restaurant


def _get_or_create_restaurant(db: Session, name: str, location: str):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.name == name, Restaurant.location == location)
        .first()
    )
    if restaurant:
        return restaurant
    restaurant = Restaurant(name=name, location=location, code=_new_restaurant_code())
    db.add(restaurant)
    db.flush()
    return restaurant


def create_inspection(db: Session, inspection: InspectionCreate):
    values = inspection.model_dump()
    restaurant_id = values.pop("restaurant_id", None)
    restaurant = (
        get_restaurant(db, restaurant_id)
        if restaurant_id is not None
        else _get_or_create_restaurant(db, values["restaurantName"], values["location"])
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found.")

    values["restaurant_id"] = restaurant.id
    values["restaurantName"] = restaurant.name
    values["location"] = restaurant.location
    values["inspection_code"] = values.get("inspection_code") or _new_inspection_code()
    db_inspection = Inspection(**values)
    db.add(db_inspection)
    try:
        db.commit()
        db.refresh(db_inspection)
        return db_inspection
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Inspection code must be unique.") from exc


def get_inspections(db: Session, skip: int = 0, limit: int = 50):
    return (
        db.query(Inspection)
        .order_by(Inspection.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_inspections_by_restaurant(
    db: Session,
    restaurant_id: int,
    skip: int = 0,
    limit: int = 50,
):
    return (
        db.query(Inspection)
        .filter(Inspection.restaurant_id == restaurant_id)
        .order_by(Inspection.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_inspection(db: Session, inspection_id: int):
    return db.query(Inspection).filter(Inspection.id == inspection_id).first()


def update_inspection(
    db: Session,
    inspection_id: int,
    inspection: InspectionUpdate,
):
    db_inspection = get_inspection(db, inspection_id)
    if not db_inspection:
        return None

    values = inspection.model_dump(exclude_unset=True)
    restaurant_id = values.get("restaurant_id")
    if restaurant_id is not None:
        restaurant = get_restaurant(db, restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found.")
        values["restaurantName"] = restaurant.name
        values["location"] = restaurant.location
    elif "restaurantName" in values or "location" in values:
        restaurant = _get_or_create_restaurant(
            db,
            values.get("restaurantName", db_inspection.restaurantName),
            values.get("location", db_inspection.location),
        )
        values["restaurant_id"] = restaurant.id

    for key, value in values.items():
        setattr(db_inspection, key, value)
    try:
        db.commit()
        db.refresh(db_inspection)
        return db_inspection
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Inspection code must be unique.") from exc


def delete_inspection(db: Session, inspection_id: int):
    db_inspection = get_inspection(db, inspection_id)
    if not db_inspection:
        return None
    db.delete(db_inspection)
    db.commit()
    return db_inspection
