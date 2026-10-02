from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


RESTAURANT_CODE_PATTERN = r"^s7085-r-[a-f0-9]{8}$"


class RestaurantBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=500)


class RestaurantCreate(RestaurantBase):
    code: str | None = Field(default=None, pattern=RESTAURANT_CODE_PATTERN)


class RestaurantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, min_length=1, max_length=500)
    code: str | None = Field(default=None, pattern=RESTAURANT_CODE_PATTERN)


class RestaurantResponse(RestaurantBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    created_at: datetime
    updated_at: datetime


class InspectionBase(BaseModel):
    # These legacy fields remain in the public API for HW1-HW4 compatibility.
    restaurantName: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=500)
    email: EmailStr
    description: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=100)


class InspectionCreate(InspectionBase):
    restaurant_id: int | None = Field(default=None, gt=0)
    inspection_code: str | None = Field(default=None, min_length=1, max_length=64)
    score: int = Field(default=100, ge=0, le=100)


class InspectionUpdate(BaseModel):
    restaurantName: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, min_length=1, max_length=500)
    email: EmailStr | None = None
    description: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    restaurant_id: int | None = Field(default=None, gt=0)
    inspection_code: str | None = Field(default=None, min_length=1, max_length=64)
    score: int | None = Field(default=None, ge=0, le=100)


class InspectionResponse(InspectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    inspection_code: str
    score: int
    created_at: datetime
    updated_at: datetime
    restaurant: RestaurantResponse | None = None
