"""SQLite schema, deterministic demonstration fixtures and database connections."""
from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('ESTUDIANTE', 'DOCENTE')),
    salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    financial_status TEXT NOT NULL DEFAULT 'PAZ_Y_SALVO'
);
CREATE TABLE IF NOT EXISTS academic_periods (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ABIERTO', 'CERRADO'))
);
CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prerequisites (
    course_id TEXT NOT NULL REFERENCES courses(id),
    required_course_id TEXT NOT NULL REFERENCES courses(id),
    PRIMARY KEY(course_id,required_course_id)
);
CREATE TABLE IF NOT EXISTS approved_courses (
    student_id TEXT NOT NULL REFERENCES users(id),
    course_id TEXT NOT NULL REFERENCES courses(id),
    status TEXT NOT NULL CHECK(status IN ('APROBADA','PENDIENTE')),
    PRIMARY KEY(student_id,course_id)
);
CREATE TABLE IF NOT EXISTS offerings (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES courses(id),
    period_id TEXT NOT NULL REFERENCES academic_periods(id),
    section TEXT NOT NULL,
    day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 1 AND 7),
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK(capacity>=0),
    remaining INTEGER NOT NULL CHECK(remaining>=0 AND remaining<=capacity),
    status TEXT NOT NULL CHECK(status IN ('ABIERTA','CERRADA')),
    UNIQUE(course_id,period_id,section),
    CHECK(starts_at < ends_at)
);
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES users(id),
    offering_id TEXT NOT NULL REFERENCES offerings(id),
    period_id TEXT NOT NULL REFERENCES academic_periods(id),
    state TEXT NOT NULL CHECK(state IN ('CONFIRMADA','CANCELADA')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(student_id,offering_id)
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    csrf_token TEXT NOT NULL,
    expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_enroll_student ON enrollments(student_id);
"""

DEMO_PASSWORD = "EduCampus2026!"
PERIOD = "2026-2"


def database_path() -> Path:
    return Path(os.environ.get("EDUCAMPUS_DB", str(Path(__file__).resolve().parents[1] / "educampus.sqlite3")))


@contextmanager
def connect(path: str | Path | None = None):
    destination = str(path or database_path())
    conn = sqlite3.connect(destination, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    try:
        yield conn
    finally:
        conn.close()


def password_digest(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 210_000).hex()


def initialize(path: str | Path | None = None, *, reset: bool = False) -> None:
    target = Path(path or database_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    if reset and target.exists():
        target.unlink()
    with connect(target) as conn:
        conn.executescript(SCHEMA)
        count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if count:
            return
        fixtures = [
            ("ana", "Ana Morales", "ESTUDIANTE", "PAZ_Y_SALVO"),
            ("bruno", "Bruno Salazar", "ESTUDIANTE", "BLOQUEADO"),
            ("camila", "Camila Torres", "ESTUDIANTE", "SERVICIO_NO_DISPONIBLE"),
            ("diana", "Diana Ríos", "ESTUDIANTE", "PAZ_Y_SALVO"),
            ("elias", "Elías Mora", "ESTUDIANTE", "PAZ_Y_SALVO"),
            ("profesor", "Docente de prueba", "DOCENTE", "PAZ_Y_SALVO"),
        ]
        for user_id, name, role, finance in fixtures:
            salt = os.urandom(16).hex()
            conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (user_id, name, role, salt, password_digest(DEMO_PASSWORD, salt), finance))
        conn.execute("INSERT INTO academic_periods VALUES (?,?,?)", (PERIOD, "Segundo semestre 2026", "ABIERTO"))
        conn.executemany("INSERT INTO courses VALUES (?,?)", [
            ("MAT100", "Fundamentos de matemáticas"),
            ("MAT201", "Cálculo II"),
            ("SIS101", "Introducción a sistemas"),
            ("ING202", "Ingeniería de software"),
            ("EST102", "Estadística aplicada"),
            ("BIO150", "Ciencia y tecnología"),
        ])
        conn.execute("INSERT INTO prerequisites VALUES (?,?)", ("MAT201", "MAT100"))
        for student in ("ana", "bruno", "camila", "elias"):
            conn.execute("INSERT INTO approved_courses VALUES (?,?,?)", (student, "MAT100", "APROBADA"))
        conn.executemany("INSERT INTO offerings VALUES (?,?,?,?,?,?,?,?,?,?)", [
            ("OF-101", "SIS101", PERIOD, "A", 1, "08:00", "10:00", 20, 20, "ABIERTA"),
            ("OF-102", "MAT201", PERIOD, "A", 2, "10:00", "12:00", 10, 10, "ABIERTA"),
            ("OF-103", "ING202", PERIOD, "B", 1, "09:00", "11:00", 12, 12, "ABIERTA"),
            ("OF-104", "EST102", PERIOD, "A", 4, "14:00", "16:00", 1, 1, "ABIERTA"),
            ("OF-105", "BIO150", PERIOD, "A", 5, "08:00", "10:00", 0, 0, "ABIERTA"),
            ("OF-106", "MAT100", PERIOD, "C", 3, "18:00", "20:00", 12, 12, "CERRADA"),
        ])
        # Student Elias has a confirmed enrollment that conflicts with OF-103.
        conn.execute("INSERT INTO enrollments(student_id,offering_id,period_id,state) VALUES (?,?,?,?)", ("elias", "OF-101", PERIOD, "CONFIRMADA"))
        conn.execute("UPDATE offerings SET remaining=remaining-1 WHERE id='OF-101'")
        conn.commit()
