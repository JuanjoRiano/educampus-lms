"""Dependency-free threaded HTTP server for the EduCampus academic demonstrator."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .db import connect, database_path, initialize, password_digest
from .service import EnrollmentError, enroll, offerings, student_enrollments

STATIC = Path(__file__).resolve().parents[1] / "static"
SESSION_SECONDS = 7200
STATIC_FILES = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/styles.css": ("styles.css", "text/css; charset=utf-8")}


def create_server(host: str = "127.0.0.1", port: int = 8000, db_path: str | Path | None = None) -> ThreadingHTTPServer:
    db = Path(db_path or database_path())
    initialize(db)
    server = ThreadingHTTPServer((host, port), Handler)
    server.db_path = db
    server.daemon_threads = True
    return server


class Handler(BaseHTTPRequestHandler):
    server_version = "EduCampus/1.0"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        # Avoid logging sensitive request bodies or session credentials.
        print("%s %s" % (self.address_string(), format % args), flush=True)

    @property
    def db_path(self) -> Path:
        return self.server.db_path

    def _headers(self, status: int, content_type: str = "application/json; charset=utf-8", content_length: int = 0, *, cookie: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'self'")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _json(self, status: int, body: dict | list, *, cookie: str | None = None) -> None:
        raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._headers(status, content_length=len(raw), cookie=cookie)
        self.wfile.write(raw)

    def _error(self, status: int, code: str, msg: str) -> None:
        self._json(status, {"ok": False, "code": code, "message": msg})

    def _body(self) -> dict:
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            raise EnrollmentError("TIPO_INVALIDO", "Se requiere application/json.", 415)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 4096:
                raise ValueError("Invalid body size")
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict):
                raise ValueError("Expected object")
            return value
        except (ValueError, json.JSONDecodeError):
            raise EnrollmentError("CUERPO_INVALIDO", "Solicitud JSON inválida o demasiado grande.", 400)

    def _session(self) -> dict | None:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            return None
        token = cookie.get("educampus_session")
        if not token or not re.fullmatch(r"[A-Za-z0-9_\-]{30,150}", token.value):
            return None
        token_hash = hashlib.sha256(token.value.encode()).hexdigest()
        with connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT s.token_hash,s.csrf_token,s.user_id,u.display_name,u.role,u.financial_status
                FROM sessions s JOIN users u ON u.id=s.user_id
                WHERE s.token_hash=? AND s.expires_at>?
            """, (token_hash, int(time.time()))).fetchone()
        return dict(row) if row else None

    def _authorized(self, role: str | None = None, *, csrf: bool = False) -> dict | None:
        user = self._session()
        if not user:
            self._error(401, "NO_AUTENTICADO", "Inicia sesión para continuar.")
            return None
        if role and user["role"] != role:
            self._error(403, "SIN_PERMISO", "No tienes permiso para esta operación.")
            return None
        if csrf and not hmac.compare_digest(user["csrf_token"], self.headers.get("X-CSRF-Token", "")):
            self._error(403, "CSRF_INVALIDO", "Token de seguridad inválido.")
            return None
        return user

    def _cookie(self, token: str, *, remove: bool = False) -> str:
        secure = os.environ.get("EDUCAMPUS_HTTPS") == "1" or self.headers.get("X-Forwarded-Proto", "").split(",")[0].strip() == "https"
        flags = "; HttpOnly; SameSite=Lax; Path=/" + ("; Secure" if secure else "")
        return f"educampus_session={token}{'; Max-Age=0' if remove else f'; Max-Age={SESSION_SECONDS}'}{flags}"

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path in STATIC_FILES:
            filename, mime = STATIC_FILES[path]
            raw = (STATIC / filename).read_bytes()
            self._headers(200, mime, len(raw))
            self.wfile.write(raw)
            return
        if path == "/api/health":
            self._json(200, {"ok": True, "service": "educampus", "version": "1.0"})
            return
        if path == "/api/session":
            user = self._session()
            if not user:
                self._json(200, {"ok": True, "authenticated": False})
            else:
                self._json(200, {"ok": True, "authenticated": True, "user": {"id": user["user_id"], "name": user["display_name"], "role": user["role"], "finance": user["financial_status"]}, "csrf": user["csrf_token"]})
            return
        if path == "/api/offerings":
            if not self._authorized():
                return
            self._json(200, {"ok": True, "offerings": offerings(self.db_path)})
            return
        if path == "/api/enrollments":
            user = self._authorized("ESTUDIANTE")
            if not user:
                return
            self._json(200, {"ok": True, "enrollments": student_enrollments(self.db_path, user["user_id"])})
            return
        self._error(404, "NO_EXISTE", "Ruta no encontrada.")

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        try:
            if path == "/api/login":
                data = self._body()
                user_id, password = data.get("username"), data.get("password")
                if not isinstance(user_id, str) or not isinstance(password, str) or len(user_id) > 80 or len(password) > 100:
                    self._error(400, "DATOS_INVALIDOS", "Credenciales inválidas.")
                    return
                with connect(self.db_path) as conn:
                    user = conn.execute("SELECT id,salt,password_hash FROM users WHERE id=?", (user_id,)).fetchone()
                    valid = bool(user) and hmac.compare_digest(password_digest(password, user["salt"]), user["password_hash"])
                    if not valid:
                        self._error(401, "LOGIN_INVALIDO", "Usuario o contraseña incorrectos.")
                        return
                    token = secrets.token_urlsafe(36)
                    csrf = secrets.token_urlsafe(32)
                    conn.execute("DELETE FROM sessions WHERE expires_at<?", (int(time.time()),))
                    conn.execute("INSERT INTO sessions VALUES (?,?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), user["id"], csrf, int(time.time()) + SESSION_SECONDS))
                    conn.commit()
                self._json(200, {"ok": True, "message": "Sesión iniciada."}, cookie=self._cookie(token))
                return
            if path == "/api/logout":
                user = self._authorized(csrf=True)
                if not user:
                    return
                with connect(self.db_path) as conn:
                    conn.execute("DELETE FROM sessions WHERE token_hash=?", (user["token_hash"],))
                    conn.commit()
                self._json(200, {"ok": True}, cookie=self._cookie("", remove=True))
                return
            if path == "/api/enroll":
                user = self._authorized("ESTUDIANTE", csrf=True)
                if not user:
                    return
                data = self._body()
                result = enroll(user["user_id"], data.get("offering_id"), self.db_path)
                self._json(201, {"ok": True, "message": "Inscripción confirmada.", "enrollment": result})
                return
            self._error(404, "NO_EXISTE", "Ruta no encontrada.")
        except EnrollmentError as exc:
            self._error(exc.status, exc.code, exc.message)
        except BrokenPipeError:
            pass


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="EduCampus LMS — demostración académica CU-02")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--reset-demo", action="store_true", help="Recreate the fictional fixture database and exit")
    args = parser.parse_args()
    if args.reset_demo:
        initialize(reset=True)
        print("Datos ficticios restablecidos.")
        return
    server = create_server(args.host, args.port)
    print(f"EduCampus iniciado en http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
