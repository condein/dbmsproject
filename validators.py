"""Form cleaning and validation for student records."""

from __future__ import annotations

import re
from datetime import date, datetime

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
ROLL_RE = re.compile(r"^[A-Za-z0-9\-]{2,20}$")
PHONE_RE = re.compile(r"^[0-9+()\-\s]{7,18}$")
PIN_RE = re.compile(r"^[0-9]{4,10}$")

MAX_MARKS = 100.0
MAX_SEMESTER = 6
GENDERS = ("Male", "Female", "Other")

# Every editable form field, in the order the templates render them.
FIELDS = (
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
    "semester",
    "marks",
    "about",
)


def clean(form) -> dict:
    """Read the form into the shape stored in MongoDB."""
    return {
        "roll_no": (form.get("roll_no") or "").strip().upper(),
        "name": " ".join((form.get("name") or "").split()),
        "email": (form.get("email") or "").strip().lower(),
        "phone": (form.get("phone") or "").strip(),
        "dob": (form.get("dob") or "").strip(),
        "gender": (form.get("gender") or "").strip().title(),
        "address": " ".join((form.get("address") or "").split()),
        "city": " ".join((form.get("city") or "").split()).title(),
        "state": " ".join((form.get("state") or "").split()).title(),
        "pincode": (form.get("pincode") or "").strip(),
        "guardian_name": " ".join((form.get("guardian_name") or "").split()),
        "guardian_phone": (form.get("guardian_phone") or "").strip(),
        "course": (form.get("course") or "").strip(),
        "semester": (form.get("semester") or "").strip(),
        "marks": (form.get("marks") or "").strip(),
        "about": " ".join((form.get("about") or "").split()),
    }


def _phone_error(value: str, label: str = "phone number") -> str | None:
    if value and not PHONE_RE.match(value):
        return f"Enter a valid {label} (7-18 digits, +, - and spaces allowed)."
    return None


def validate(
    data: dict,
    *,
    repo=None,
    student_id: str | None = None,
    academic: bool = True,
) -> dict[str, str]:
    """Return ``{field: message}``; empty means the record is valid.

    ``academic=False`` validates only the personal profile fields, so a student
    editing their own profile never needs to resend roll number, course or marks.
    """
    errors: dict[str, str] = {}

    if academic:
        roll_no = data.get("roll_no", "")
        if not roll_no:
            errors["roll_no"] = "Roll number is required."
        elif not ROLL_RE.match(roll_no):
            errors["roll_no"] = "Use 2-20 letters, digits or dashes."
        elif repo is not None and repo.roll_no_taken(roll_no, exclude_id=student_id):
            errors["roll_no"] = "That roll number is already registered."

    name = data.get("name", "")
    if len(name) < 2:
        errors["name"] = "Enter the student's full name."
    elif len(name) > 60:
        errors["name"] = "Name is too long (max 60 characters)."

    email = data.get("email", "")
    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."

    message = _phone_error(data.get("phone", ""))
    if message:
        errors["phone"] = message

    message = _phone_error(data.get("guardian_phone", ""), "guardian phone number")
    if message:
        errors["guardian_phone"] = message

    dob = data.get("dob", "")
    if dob:
        try:
            born = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            errors["dob"] = "Use the date picker (YYYY-MM-DD)."
        else:
            if born > date.today():
                errors["dob"] = "Date of birth cannot be in the future."
            elif born.year < 1950:
                errors["dob"] = "That date of birth looks too old."

    gender = data.get("gender", "")
    if gender and gender not in GENDERS:
        errors["gender"] = "Choose Male, Female or Other."

    if len(data.get("address", "")) > 200:
        errors["address"] = "Address is too long (max 200 characters)."
    if len(data.get("city", "")) > 60:
        errors["city"] = "City is too long (max 60 characters)."
    if len(data.get("state", "")) > 60:
        errors["state"] = "State is too long (max 60 characters)."

    pincode = data.get("pincode", "")
    if pincode and not PIN_RE.match(pincode):
        errors["pincode"] = "PIN code must be 4-10 digits."

    if len(data.get("guardian_name", "")) > 60:
        errors["guardian_name"] = "Guardian name is too long (max 60 characters)."
    if len(data.get("about", "")) > 300:
        errors["about"] = "Keep the introduction under 300 characters."

    if academic:
        course = data.get("course", "")
        if not course:
            errors["course"] = "Course is required."
        elif len(course) > 60:
            errors["course"] = "Course name is too long."

        semester = data.get("semester", "")
        if not semester.isdigit() or not 1 <= int(semester) <= MAX_SEMESTER:
            errors["semester"] = f"Semester must be a number from 1 to {MAX_SEMESTER}."

        marks = data.get("marks", "")
        if marks:
            try:
                value = float(marks)
            except ValueError:
                errors["marks"] = "Marks must be a number."
            else:
                if not 0 <= value <= MAX_MARKS:
                    errors["marks"] = f"Marks must be between 0 and {int(MAX_MARKS)}."

    return errors


def to_document(data: dict, *, academic: bool = True) -> dict:
    """Convert validated form values into MongoDB types.

    Profile fields are always included; the academic block is left untouched
    when a student saves their own profile.
    """
    document = {
        "name": data["name"],
        "email": data["email"],
        "phone": data.get("phone") or "",
        "dob": data.get("dob") or "",
        "gender": data.get("gender") or "",
        "address": data.get("address") or "",
        "city": data.get("city") or "",
        "state": data.get("state") or "",
        "pincode": data.get("pincode") or "",
        "guardian_name": data.get("guardian_name") or "",
        "guardian_phone": data.get("guardian_phone") or "",
        "about": data.get("about") or "",
    }
    if academic:
        document.update(
            {
                "roll_no": data["roll_no"],
                "course": data["course"],
                "semester": int(data["semester"]),
                "marks": float(data["marks"]) if data.get("marks") else None,
            }
        )
    return document
