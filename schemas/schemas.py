from pydantic import BaseModel, EmailStr


class InspectionBase(BaseModel):
    restaurantName: str
    location: str
    email: EmailStr
    description: str
    category: str


class InspectionCreate(InspectionBase):
    pass


class InspectionUpdate(InspectionBase):
    pass


class InspectionResponse(InspectionBase):
    id: int

    class Config:
        from_attributes = True