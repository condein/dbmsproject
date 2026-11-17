# MCA Student Records

A small web application for an MCA department where a student can **create, read,
update and delete (CRUD)** student records stored in **MongoDB**.

Built with Flask, PyMongo and Jinja templates — no JavaScript framework, no build
step, one Python process.

![Student list](screenshots/01-list.png)

## Features

- **Create** a student (academic details plus a full personal profile)
- **Read** the list with a live search across name, roll number, email, city, phone and course
- **Update** any record through the validated admin form
- **Delete** with a confirmation prompt
- **Student profile page** where a student edits their own details: name, email,
  phone, date of birth, gender, street address, city, state, PIN code, guardian
  name and phone, and a short introduction. Roll number, course, semester and
  marks stay read-only there.
- A profile-completeness ring shows how much of the profile has been filled in
- Server-side validation: required fields, email/phone/PIN formats, date of birth
  not in the future, semester 1-6, marks 0-100 and a **unique roll number**
  (also enforced by a MongoDB unique index)
- Summary counters: total students, average marks, number of courses
- Animated UI: aurora background, glass cards, staggered reveals, gradient
  headings and counters; every animation respects `prefers-reduced-motion`
- Flash messages, 404 page, responsive layout

## Stack

| Layer | Choice |
|---|---|
| Web | Flask 3 + Jinja2 |
| Database | MongoDB via PyMongo |
| Styling | Plain CSS (`static/style.css`) |
| Config | `python-dotenv` + `.env` |

## Setup

```bash
cd student-crud
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
copy .env.example .env          # or: cp .env.example .env
```

### Point it at a database

**Option A — MongoDB Atlas (works from any machine, free tier)**

1. Create a free cluster at <https://www.mongodb.com/cloud/atlas>.
2. Add your IP under *Network Access*, and a database user under *Database Access*.
3. Copy the connection string into `.env`:

```
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

**Option B — local MongoDB**

Install MongoDB Community Server, make sure `mongod` is running, then keep the
default `MONGODB_URI=mongodb://localhost:27017`.

**Option C — no database installed (demo only)**

If no server answers, the app falls back to `mongomock`, an in-memory MongoDB,
so you can still click through every screen. Data disappears when the process
stops. The page footer shows which backend is active.

### Sample data

```bash
python seed.py
```

## Run

```bash
python app.py
```

Open <http://127.0.0.1:5000>.

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | list students, optional `?q=` search |
| GET | `/students/new` | create form |
| POST | `/students` | create a student |
| GET | `/students/<id>/edit` | edit form |
| POST | `/students/<id>` | update a student |
| GET | `/students/<id>/profile` | student profile page |
| POST | `/students/<id>/profile` | student updates their own profile |
| POST | `/students/<id>/delete` | delete a student |

## Project structure

```
student-crud/
├── app.py              Flask app + CRUD routes
├── db.py               MongoDB connection, StudentRepository, mongomock fallback
├── validators.py       form cleaning and validation rules
├── seed.py             sample students with full profiles
├── templates/
│   ├── base.html       layout, navigation, flash messages
│   ├── index.html      card grid, search, summary counters
│   ├── form.html       add/edit form (shared)
│   ├── profile.html    student profile + self-service update
│   ├── _profile_fields.html  personal/address fields used by both forms
│   └── 404.html
├── static/style.css    animated glass theme
├── static/app.js       counter, ring and flash animations
├── requirements.txt
├── .env.example
└── README.md
```

## How the CRUD maps to MongoDB

| Operation | Route | PyMongo call |
|---|---|---|
| Create | `POST /students` | `insert_one(...)` |
| Read | `GET /` | `find(criteria).sort(...)` |
| Update | `POST /students/<id>` and `POST /students/<id>/profile` | `update_one({"_id": oid}, {"$set": ...})` |
| Delete | `POST /students/<id>/delete` | `delete_one({"_id": oid})` |

Documents look like:

```json
{
  "_id": "ObjectId(...)",
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
  "created_at": "2026-11-14T05:35:20Z"
}
```

## Notes

- Writes use `POST` only, so a link or refresh cannot delete a record.
- The roll number has a unique index; validation also reports a friendly message
  before MongoDB raises `DuplicateKeyError`.
- This is a teaching project: it has no login, so the profile page is reached by
  clicking a student (or `/students/<id>/profile`). Add authentication and CSRF
  protection before putting it on a public network.
