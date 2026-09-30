import random

from database.database import SessionLocal
from models.models import Inspection, InspectionRelated


SEED = 7085
PRIMARY_ROWS = 5000
RELATED_ROWS = 200


def seed_data():
    random.seed(SEED)

    db = SessionLocal()

    try:
        print("Clearing existing N+1 test data...")

        db.query(InspectionRelated).delete()
        db.query(Inspection).delete()
        db.commit()

        print("Creating 5,000 inspections...")

        inspections = []

        for i in range(1, PRIMARY_ROWS + 1):
            inspection = Inspection(
                restaurantName=f"Restaurant {i}",
                location=random.choice([
                    "San Jose, CA",
                    "Mountain View, CA",
                    "Palo Alto, CA"
                ]),
                email=f"restaurant{i}@example.com",
                description=f"Restaurant inspection record {i}",
                category=random.choice([
                    "Food Safety",
                    "Health and Safety",
                    "Sanitation"
                ])
            )

            inspections.append(inspection)

        db.bulk_save_objects(inspections)
        db.commit()

        print("5,000 inspections created.")

       
        inspections = (
            db.query(Inspection)
            .order_by(Inspection.id)
            .limit(PRIMARY_ROWS)
            .all()
        )

        print("Creating 200 related records...")

        related_records = []

        for i in range(RELATED_ROWS):
            inspection = inspections[i]

            related = InspectionRelated(
                inspection_id=inspection.id,
                note=f"Related inspection note {i + 1}"
            )

            related_records.append(related)

        db.bulk_save_objects(related_records)
        db.commit()

        primary_count = db.query(Inspection).count()
        related_count = db.query(InspectionRelated).count()

        print()
        print("========== SEED COMPLETE ==========")
        print(f"Seed: {SEED}")
        print(f"Primary rows: {primary_count}")
        print(f"Related rows: {related_count}")
        print("===================================")

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()