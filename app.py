"""MCA Student Records - a small Flask + MongoDB CRUD application.

    python app.py        # http://127.0.0.1:5000

Routes
    GET  /                      list + search students
    GET  /students/new          create form
    POST /students              create
    GET  /students/<id>/edit    edit form (full record)
    POST /students/<id>         update
    GET  /students/<id>/profile student profile page
    POST /students/<id>/profile student updates their own profile
    POST /students/<id>/delete  delete
"""

from __future__ import annotations

import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

from db import StudentRepository, build_database
from seed import ensure_demo_data
from validators import FIELDS, clean, to_document, validate

load_dotenv()

COURSES = ("MCA", "MCA (Data Science)", "MCA (Cyber Security)")
SEMESTERS = tuple(range(1, 7))

# Fields that make up a student's own profile completeness score.
PROFILE_KEYS = (
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
    "about",
)


def form_values(student: dict | None = None, overrides: dict | None = None) -> dict:
    """Prefill a form from a stored student document."""
    values = {key: "" for key in FIELDS}
    if student:
        for key in FIELDS:
            value = student.get(key)
            values[key] = "" if value is None else str(value)
    if overrides:
        values.update(overrides)
    return values


def profile_strength(student: dict) -> int:
    """Percentage of profile fields that have been filled in."""
    filled = sum(1 for key in PROFILE_KEYS if str(student.get(key) or "").strip())
    return round(filled / len(PROFILE_KEYS) * 100)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

    database, backend = build_database()
    repo = StudentRepository(database)
    if backend != "MongoDB" and repo.summary()["total"] == 0:
        # The in-memory fallback cannot be seeded from another process,
        # so give the demo a usable dataset on startup.
        ensure_demo_data(repo)
    app.config["REPO"] = repo
    app.config["BACKEND"] = backend

    @app.context_processor
    def inject_globals():
        return {
            "backend": app.config["BACKEND"],
            "student_count": repo.summary()["total"],
            "courses": COURSES,
            "semesters": SEMESTERS,
            "today": date.today().isoformat(),
        }

    @app.get("/")
    def index():
        query = request.args.get("q", "")
        return render_template(
            "index.html",
            students=repo.list(query),
            summary=repo.summary(),
            query=query,
        )

    @app.get("/students/new")
    def new_student():
        return render_template(
            "form.html",
            data=form_values({"course": "MCA", "semester": "1"}),
            errors={},
            student=None,
        )

    @app.post("/students")
    def create_student():
        data = clean(request.form)
        errors = validate(data, repo=repo)
        if errors:
            return render_template("form.html", data=data, errors=errors, student=None), 400

        student_id = repo.create(to_document(data))
        flash(f"Added {data['name']} ({data['roll_no']}).", "success")
        return redirect(url_for("index", _anchor=f"student-{student_id}"))

    @app.get("/students/<student_id>/edit")
    def edit_student(student_id: str):
        student = repo.get(student_id)
        if student is None:
            abort(404)
        return render_template(
            "form.html", data=form_values(student), errors={}, student=student
        )

    @app.post("/students/<student_id>")
    def update_student(student_id: str):
        student = repo.get(student_id)
        if student is None:
            abort(404)

        data = clean(request.form)
        errors = validate(data, repo=repo, student_id=student_id)
        if errors:
            return render_template("form.html", data=data, errors=errors, student=student), 400

        repo.update(student_id, to_document(data))
        flash(f"Saved changes for {data['name']}.", "success")
        return redirect(url_for("index", _anchor=f"student-{student_id}"))

    @app.get("/students/<student_id>/profile")
    def profile(student_id: str):
        student = repo.get(student_id)
        if student is None:
            abort(404)
        return render_template(
            "profile.html",
            student=student,
            data=form_values(student),
            errors={},
            strength=profile_strength(student),
        )

    @app.post("/students/<student_id>/profile")
    def update_profile(student_id: str):
        student = repo.get(student_id)
        if student is None:
            abort(404)

        data = clean(request.form)
        errors = validate(data, academic=False)
        if errors:
            return (
                render_template(
                    "profile.html",
                    student=student,
                    data=data,
                    errors=errors,
                    strength=profile_strength(student),
                ),
                400,
            )

        repo.update(student_id, to_document(data, academic=False))
        flash(f"Profile updated for {data['name']}.", "success")
        return redirect(url_for("profile", student_id=student_id, _anchor="profile-top"))

    @app.post("/students/<student_id>/delete")
    def delete_student(student_id: str):
        student = repo.get(student_id)
        if student is None:
            abort(404)
        repo.delete(student_id)
        flash(f"Deleted {student['name']} ({student['roll_no']}).", "success")
        return redirect(url_for("index"))

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
