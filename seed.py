"""Sample MCA students with complete profiles.

    python seed.py

Running the app without a MongoDB server uses the in-memory fallback, which
cannot share data between processes, so ``ensure_demo_data`` is also called on
startup in that case. Against real MongoDB the data persists as usual.
"""

from __future__ import annotations

from db import StudentRepository, build_database
from validators import clean, to_document, validate

SAMPLE = [
    {
        "roll_no": "MCA2401",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@college.edu",
        "phone": "+91 98210 44551",
        "dob": "2003-02-14",
        "gender": "Male",
        "address": "24, Lake View Road, Andheri East",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400069",
        "guardian_name": "Rohit Sharma",
        "guardian_phone": "+91 98200 11223",
        "course": "MCA",
        "semester": 1,
        "marks": 78.5,
        "about": "Backend enthusiast building small tools with Python and MongoDB.",
    },
    {
        "roll_no": "MCA2402",
        "name": "Meera Iyer",
        "email": "meera.iyer@college.edu",
        "phone": "+91 99401 88230",
        "dob": "2002-11-03",
        "gender": "Female",
        "address": "7A, Besant Nagar 2nd Cross Street",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "pincode": "600090",
        "guardian_name": "Lakshmi Iyer",
        "guardian_phone": "+91 99400 55117",
        "course": "MCA",
        "semester": 1,
        "marks": 85.0,
        "about": "Interested in data structures, teaching assistantships and badminton.",
    },
    {
        "roll_no": "MCA2403",
        "name": "Rahul Verma",
        "email": "rahul.verma@college.edu",
        "phone": "+91 98110 77342",
        "dob": "2002-06-21",
        "gender": "Male",
        "address": "H-14, Sector 12, Dwarka",
        "city": "New Delhi",
        "state": "Delhi",
        "pincode": "110078",
        "guardian_name": "Anil Verma",
        "guardian_phone": "+91 98100 33456",
        "course": "MCA",
        "semester": 2,
        "marks": 66.0,
        "about": "Learning full-stack development, currently exploring Flask APIs.",
    },
    {
        "roll_no": "MCA2404",
        "name": "Sneha Patil",
        "email": "sneha.patil@college.edu",
        "phone": "+91 90280 61194",
        "dob": "2002-01-09",
        "gender": "Female",
        "address": "Flat 302, Sunshine Residency, Kothrud",
        "city": "Pune",
        "state": "Maharashtra",
        "pincode": "411038",
        "guardian_name": "Sunil Patil",
        "guardian_phone": "+91 90280 40071",
        "course": "MCA (Data Science)",
        "semester": 2,
        "marks": 91.5,
        "about": "Data science track. Enjoys dashboards, statistics and Kaggle notebooks.",
    },
    {
        "roll_no": "MCA2405",
        "name": "Karan Singh",
        "email": "karan.singh@college.edu",
        "phone": "+91 98765 12038",
        "dob": "2003-04-27",
        "gender": "Male",
        "address": "18, Model Town Extension",
        "city": "Ludhiana",
        "state": "Punjab",
        "pincode": "141002",
        "guardian_name": "Harpreet Singh",
        "guardian_phone": "+91 98760 22984",
        "course": "MCA",
        "semester": 3,
        "marks": 72.0,
        "about": "Interested in cloud infrastructure and Linux administration.",
    },
    {
        "roll_no": "MCA2406",
        "name": "Priya Nair",
        "email": "priya.nair@college.edu",
        "phone": "+91 98470 55612",
        "dob": "2002-09-18",
        "gender": "Female",
        "address": "TC 12/84, Sasthamangalam",
        "city": "Thiruvananthapuram",
        "state": "Kerala",
        "pincode": "695010",
        "guardian_name": "Suresh Nair",
        "guardian_phone": "+91 98470 11209",
        "course": "MCA (Cyber Security)",
        "semester": 3,
        "marks": 88.0,
        "about": "Cyber security specialisation, CTF player and Linux power user.",
    },
]


def ensure_demo_data(repo: StudentRepository) -> int:
    """Insert the samples that are not already present; return how many."""
    created = 0
    for sample in SAMPLE:
        data = clean({key: str(value) for key, value in sample.items()})
        if validate(data, repo=repo):
            continue
        repo.create(to_document(data))
        created += 1
    return created


def main() -> None:
    database, backend = build_database()
    repo = StudentRepository(database)
    created = ensure_demo_data(repo)
    print(f"{created} sample student(s) added.")
    print(f"Backend: {backend} · total students: {repo.summary()['total']}")


if __name__ == "__main__":
    main()
