"""CU-02 business logic: parallel checks, serializable confirmation and rollback."""
from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .db import connect


@dataclass
class EnrollmentError(Exception):
    code: str
    message: str
    status: int = 409

    def __str__(self) -> str:
        return self.message


def _academic_rules(conn: sqlite3.Connection, student_id: str, offering_id: str) -> dict:
    offer = conn.execute("""
        SELECT o.*, c.name AS course_name, p.status AS period_status
        FROM offerings o JOIN courses c ON c.id=o.course_id
        JOIN academic_periods p ON p.id=o.period_id WHERE o.id=?
    """, (offering_id,)).fetchone()
    if not offer:
        raise EnrollmentError("OFERTA_INEXISTENTE", "La oferta seleccionada no existe.", 404)
    if offer["period_status"] != "ABIERTO" or offer["status"] != "ABIERTA":
        raise EnrollmentError("OFERTA_CERRADA", "El periodo o la oferta no están abiertos.")
    if offer["remaining"] < 1:
        raise EnrollmentError("SIN_CUPOS", "La asignatura no tiene cupos disponibles.")
    missing = conn.execute("""
        SELECT p.required_course_id FROM prerequisites p
        WHERE p.course_id=? AND NOT EXISTS (
          SELECT 1 FROM approved_courses a WHERE a.student_id=?
          AND a.course_id=p.required_course_id AND a.status='APROBADA'
        )
    """, (offer["course_id"], student_id)).fetchall()
    if missing:
        ids = ", ".join(row["required_course_id"] for row in missing)
        raise EnrollmentError("PRERREQUISITO", f"Faltan prerrequisitos aprobados: {ids}.")
    dup = conn.execute("SELECT 1 FROM enrollments WHERE student_id=? AND offering_id=? AND state='CONFIRMADA'", (student_id, offering_id)).fetchone()
    if dup:
        raise EnrollmentError("DUPLICADA", "Esta asignatura ya está inscrita.")
    clash = conn.execute("""
        SELECT 1 FROM enrollments e JOIN offerings existing ON existing.id=e.offering_id
        WHERE e.student_id=? AND e.state='CONFIRMADA'
          AND existing.period_id=? AND existing.day_of_week=?
          AND existing.starts_at < ? AND ? < existing.ends_at LIMIT 1
    """, (student_id, offer["period_id"], offer["day_of_week"], offer["ends_at"], offer["starts_at"])).fetchone()
    if clash:
        raise EnrollmentError("CRUCE_HORARIO", "El horario coincide con otra asignatura inscrita.")
    return dict(offer)


class AcademicValidator:
    """Encapsulate the academic rules and their transactional recheck."""

    def check(self, path: str | Path, student_id: str, offering_id: str) -> dict:
        with connect(path) as conn:
            return _academic_rules(conn, student_id, offering_id)

    def recheck(self, conn: sqlite3.Connection, student_id: str, offering_id: str) -> dict:
        return _academic_rules(conn, student_id, offering_id)


class FinancialGateway:
    """Port for retrieving an external accounting status."""

    def check(self, path: str | Path, student_id: str, period_id: str) -> str:
        raise NotImplementedError


class SimulatedFinancialGateway(FinancialGateway):
    """Fictitious SystemaContable adapter; no live financial integration."""

    def check(self, path: str | Path, student_id: str, period_id: str) -> str:
        with connect(path) as conn:
            person = conn.execute("SELECT financial_status FROM users WHERE id=? AND role='ESTUDIANTE'", (student_id,)).fetchone()
            period = conn.execute("SELECT id FROM academic_periods WHERE id=?", (period_id,)).fetchone()
            if not person or not period:
                return "SERVICIO_NO_DISPONIBLE"
            return person["financial_status"]


class SQLiteEnrollmentRepository:
    """Atomic enrollment persistence with a conditional seat update."""

    def confirm(self, path: str | Path, student_id: str, offering_id: str, validator: AcademicValidator, *, fail_after_insert: bool = False) -> dict:
        with connect(path) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                # Recheck under a write lock to prevent stale-seat races.
                offer = validator.recheck(conn, student_id, offering_id)
                updated = conn.execute("UPDATE offerings SET remaining=remaining-1 WHERE id=? AND remaining>0", (offering_id,)).rowcount
                if updated != 1:
                    raise EnrollmentError("SIN_CUPOS", "La asignatura no tiene cupos disponibles.")
                conn.execute("INSERT INTO enrollments(student_id,offering_id,period_id,state) VALUES (?,?,?,'CONFIRMADA')", (student_id, offering_id, offer["period_id"]))
                if fail_after_insert:
                    raise sqlite3.OperationalError("Simulated storage failure")
                enrollment_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
                conn.commit()
                return {"id": enrollment_id, "offering_id": offering_id, "course": offer["course_name"], "period": offer["period_id"], "status": "CONFIRMADA"}
            except EnrollmentError:
                conn.rollback()
                raise
            except (sqlite3.Error, ValueError) as exc:
                conn.rollback()
                raise EnrollmentError("ERROR_PERSISTENCIA", "La inscripción no pudo guardarse. No se aplicaron cambios.", 500) from exc


class EnrollmentService:
    """Orchestrate CU-02 with a pluggable financial gateway."""

    def __init__(self, path: str | Path, gateway: FinancialGateway | None = None):
        self.path = path
        self.validator = AcademicValidator()
        self.gateway = gateway or SimulatedFinancialGateway()
        self.repository = SQLiteEnrollmentRepository()

    def execute(self, student_id: str, offering_id: str, *, fail_after_insert: bool = False) -> dict:
        if not isinstance(offering_id, str) or len(offering_id) > 32 or not offering_id:
            raise EnrollmentError("OFERTA_INVALIDA", "Identificador de oferta inválido.", 400)
        with connect(self.path) as conn:
            user = conn.execute("SELECT role FROM users WHERE id=?", (student_id,)).fetchone()
            if not user or user["role"] != "ESTUDIANTE":
                raise EnrollmentError("NO_AUTORIZADO", "Solo el estudiante puede solicitar una inscripción.", 403)
            offer = conn.execute("SELECT period_id FROM offerings WHERE id=?", (offering_id,)).fetchone()
            period_id = offer["period_id"] if offer else "PERIODO_NO_ENCONTRADO"
        # Fork / join: independent preliminary checks run concurrently.
        with ThreadPoolExecutor(max_workers=2) as pool:
            academic = pool.submit(self.validator.check, self.path, student_id, offering_id)
            finance = pool.submit(self.gateway.check, self.path, student_id, period_id)
            academic_error = None
            try:
                academic.result()
            except EnrollmentError as exc:
                academic_error = exc
            financial_status = finance.result()
        if academic_error is not None:
            raise academic_error
        if financial_status != "PAZ_Y_SALVO":
            code = "BLOQUEO_FINANCIERO" if financial_status == "BLOQUEADO" else "FINANCIERO_NO_DISPONIBLE"
            msg = "El estudiante no está a paz y salvo." if code == "BLOQUEO_FINANCIERO" else "No fue posible validar el estado financiero."
            raise EnrollmentError(code, msg, 409 if code == "BLOQUEO_FINANCIERO" else 503)
        return self.repository.confirm(self.path, student_id, offering_id, self.validator, fail_after_insert=fail_after_insert)


def enroll(student_id: str, offering_id: str, path: str | Path, *, fail_after_insert: bool = False) -> dict:
    """Public enrollment entrypoint compatible with the HTTP adapter."""
    return EnrollmentService(path).execute(student_id, offering_id, fail_after_insert=fail_after_insert)


def offerings(path: str | Path) -> list[dict]:
    with connect(path) as conn:
        return [dict(row) for row in conn.execute("""
            SELECT o.id,o.course_id,c.name,o.section,o.period_id,o.day_of_week,o.starts_at,o.ends_at,
                   o.capacity,o.remaining,o.status FROM offerings o
            JOIN courses c ON c.id=o.course_id ORDER BY o.course_id, o.section
        """).fetchall()]


def student_enrollments(path: str | Path, student_id: str) -> list[dict]:
    with connect(path) as conn:
        return [dict(row) for row in conn.execute("""
            SELECT e.id,e.state,e.created_at,o.id AS offering_id,o.course_id,c.name,o.day_of_week,
                   o.starts_at,o.ends_at,e.period_id FROM enrollments e
            JOIN offerings o ON o.id=e.offering_id JOIN courses c ON c.id=o.course_id
            WHERE e.student_id=? AND e.state='CONFIRMADA' ORDER BY e.id DESC
        """, (student_id,)).fetchall()]
