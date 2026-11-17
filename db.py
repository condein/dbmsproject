"""MongoDB connection for the student CRUD app.

Real MongoDB is used whenever `MONGODB_URI` answers. If no server is running,
the app falls back to `mongomock` (an in-memory MongoDB) so the project can be
demonstrated on a laptop without installing MongoDB. The active backend is
shown in the page footer.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError

DEFAULT_URI = "mongodb://localhost:27017"
DEFAULT_DB = "mca_students"

# Text fields every document is expected to carry, filled with "" when a
# record predates a profile field.
TEXT_FIELDS = (
    "roll_no",
    "name",
    "email",
    "phone",
    "dob",
    "gender",
    "address",
    "city",
    "state",
    "pincode",
    "guardian_name",
    "guardian_phone",
    "course",
    "about",
)


def build_database(uri: str | None = None, db_name: str | None = None):
    """Return ``(database, backend_label)`` ready for use."""
    uri = uri or os.getenv("MONGODB_URI", DEFAULT_URI)
    db_name = db_name or os.getenv("MONGODB_DB", DEFAULT_DB)

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        return client[db_name], "MongoDB"
    except (PyMongoError, OSError):
        pass

    try:
        import mongomock
    except ImportError as exc:  # pragma: no cover - dependency is in requirements
        raise RuntimeError(
            "No MongoDB server found and mongomock is not installed. "
            "Start MongoDB or run: pip install mongomock"
        ) from exc

    return mongomock.MongoClient()[db_name], "mongomock (no MongoDB server)"


def to_object_id(value: str) -> ObjectId | None:
    """ObjectId for a valid 24-char hex id, else None."""
    return ObjectId(value) if ObjectId.is_valid(value) else None


class StudentRepository:
    """All MongoDB access for students, so routes stay thin."""

    def __init__(self, database):
        self.collection = database["students"]
        self.collection.create_index([("roll_no", ASCENDING)], unique=True)

    # -- reads --------------------------------------------------------- #
    def list(self, query: str = "") -> list[dict]:
        search = (query or "").strip()
        if search:
            pattern = {"$regex": search, "$options": "i"}
            criteria = {
                "$or": [
                    {"roll_no": pattern},
                    {"name": pattern},
                    {"email": pattern},
                    {"course": pattern},
                    {"city": pattern},
                    {"phone": pattern},
                ]
            }
        else:
            criteria = {}
        cursor = self.collection.find(criteria).sort([("name", ASCENDING)])
        return [self._serialise(doc) for doc in cursor]

    def get(self, student_id: str) -> dict | None:
        oid = to_object_id(student_id)
        if oid is None:
            return None
        doc = self.collection.find_one({"_id": oid})
        return self._serialise(doc) if doc else None

    def summary(self) -> dict:
        total = self.collection.count_documents({})
        courses = sorted(
            {doc.get("course", "") for doc in self.collection.find({}, {"course": 1})}
            - {""}
        )
        marks = [
            doc["marks"]
            for doc in self.collection.find({"marks": {"$ne": None}}, {"marks": 1})
            if isinstance(doc.get("marks"), (int, float))
        ]
        average = round(sum(marks) / len(marks), 1) if marks else None
        return {"total": total, "courses": courses, "average": average}

    def roll_no_taken(self, roll_no: str, exclude_id: str | None = None) -> bool:
        criteria = {"roll_no": {"$regex": f"^{roll_no}$", "$options": "i"}}
        if exclude_id:
            oid = to_object_id(exclude_id)
            if oid is not None:
                criteria["_id"] = {"$ne": oid}
        return self.collection.count_documents(criteria, limit=1) > 0

    # -- writes -------------------------------------------------------- #
    def create(self, data: dict) -> str:
        payload = {**data, "created_at": datetime.now(timezone.utc)}
        return str(self.collection.insert_one(payload).inserted_id)

    def update(self, student_id: str, data: dict) -> bool:
        oid = to_object_id(student_id)
        if oid is None:
            return False
        result = self.collection.update_one(
            {"_id": oid},
            {"$set": {**data, "updated_at": datetime.now(timezone.utc)}},
        )
        return result.matched_count == 1

    def delete(self, student_id: str) -> bool:
        oid = to_object_id(student_id)
        if oid is None:
            return False
        return self.collection.delete_one({"_id": oid}).deleted_count == 1

    # -- helpers ------------------------------------------------------- #
    @staticmethod
    def _serialise(doc: dict) -> dict:
        item = dict(doc)
        item["id"] = str(item.pop("_id"))
        for key in TEXT_FIELDS:
            item[key] = item.get(key) or ""
        item.setdefault("semester", "")
        item.setdefault("marks", None)
        item["initials"] = "".join(
            part[0] for part in str(item.get("name", "")).split()[:2]
        ).upper() or "?"
        for key in ("created_at", "updated_at"):
            value = item.get(key)
            if isinstance(value, datetime):
                item[key] = value.strftime("%d %b %Y, %H:%M")
        return item
