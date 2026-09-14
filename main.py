from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Local Restaurant Inspections")


class Inspection(BaseModel):
    restaurantName: str
    location: str
    email: str
    description: str
    category: str


inspections = [
    {
        "id": 1,
        "restaurantName": "Spice House",
        "location": "San Jose",
        "email": "spice@example.com",
        "description": "Kitchen inspection completed successfully.",
        "category": "Passed"
    },
    {
        "id": 2,
        "restaurantName": "Burger Palace",
        "location": "Santa Clara",
        "email": "burger@example.com",
        "description": "Inspection found some items that need attention.",
        "category": "Conditional Pass"
    },
    {
        "id": 3,
        "restaurantName": "Pizza Corner",
        "location": "San Jose",
        "email": "pizza@example.com",
        "description": "Several violations were found during inspection.",
        "category": "Violation or Failed"
    }
]


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/script.js")
def script():
    return FileResponse("script.js")


@app.get("/api/inspections")
def get_inspections(search: str | None = None):
    if search is None or search.strip() == "":
        return inspections

    search_text = search.strip().lower()

    matching_inspections = [
        inspection
        for inspection in inspections
        if search_text in inspection["restaurantName"].lower()
        or search_text in inspection["location"].lower()
    ]

    return matching_inspections


@app.post("/api/inspections")
def create_inspection(inspection: Inspection):
    new_id = max(
        [item["id"] for item in inspections],
        default=0
    ) + 1

    new_inspection = {
        "id": new_id,
        **inspection.model_dump()
    }

    inspections.append(new_inspection)

    return new_inspection


@app.put("/api/inspections/{inspection_id}")
def update_inspection(
    inspection_id: int,
    inspection: Inspection
):
    for index, existing_inspection in enumerate(inspections):
        if existing_inspection["id"] == inspection_id:
            updated_inspection = {
                "id": inspection_id,
                **inspection.model_dump()
            }

            inspections[index] = updated_inspection

            return updated_inspection

    raise HTTPException(
        status_code=404,
        detail="Inspection not found"
    )


@app.delete("/api/inspections/{inspection_id}")
def delete_inspection(inspection_id: int):
    for index, inspection in enumerate(inspections):
        if inspection["id"] == inspection_id:
            deleted_inspection = inspections.pop(index)

            return {
                "message": "Inspection deleted successfully",
                "deleted": deleted_inspection
            }

    raise HTTPException(
        status_code=404,
        detail="Inspection not found"
    )