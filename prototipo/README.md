# EduCampus LMS — Prototipo CU-02

Este prototipo académico implementa consulta de oferta (RF-01), simulación de verificación financiera (RF-02) y matrícula (RF-03). No implementa reconocimiento biométrico real, examen virtual ni el resto de módulos RF-04/RF-05. **Solo datos ficticios.**

## Ejecutar localmente

Requisito: Python 3.10+; no depende de paquetes de terceros.

```bash
cd prototipo
python3 -m educampus --reset-demo
python3 -m educampus --host 127.0.0.1 --port 8000
```

Visita http://127.0.0.1:8000. Clave para todas las cuentas ficticias: `EduCampus2026!`.

| Usuario | Resultado principal esperado |
|---|---|
| `ana` | Puede confirmar OF-101 y OF-102; segundo intento duplicado rechazado. |
| `bruno` | Bloqueo financiero. |
| `camila` | SistemaContable no disponible. |
| `diana` | Prerrequisito MAT100 pendiente para OF-102. |
| `elias` | Tiene OF-101; OF-103 tiene cruce de horario. |
| `profesor` | Docente no puede inscribir ni ver matrículas ajenas. |

OF-105 no tiene cupos y OF-106 está cerrada. Si se agotaron los datos de la demostración, ejecuta `python3 -m educampus --reset-demo` con el servidor detenido.

## Pruebas

```bash
cd prototipo
python3 -m unittest discover -s tests -v
python3 scripts/qa_checks.py
```

Las pruebas verifican casos de éxito y de rechazo, concurrencia, atomicidad, control de acceso y varias comprobaciones de rendimiento. El ensayo corto no sustituye a la vigilancia continua de 30 minutos que exige RNF-02.

## Diseño

* HTTP estándar de Python (ThreadingHTTPServer), sin dependencias externas.
* Sesión de demostración almacenada en SQLite, cookies HttpOnly, CSRF en operaciones de escritura y contraseñas de muestra con PBKDF2-HMAC.
* Validaciones académica y financiera preliminares concurrentes mediante dos tareas; el `join` espera ambas respuestas.
* Confirmación de inscripción bajo `BEGIN IMMEDIATE`, revalidación de cupos y restricciones, decremento condicionado, inserción única y rollback.
* `SistemaContable` es un simulador que devuelve PAZ_Y_SALVO, BLOQUEADO o SERVICIO_NO_DISPONIBLE según el usuario ficticio.

## Despliegue en Render

1. Sube el repositorio a GitHub y mantén fuera de él las firmas manuscritas si es público.
2. En Render > New > Blueprint, conecta el repositorio y selecciona `render.yaml` en la raíz. O crea un Web Service con `Root Directory=prototipo`, `Build Command=python -m compileall -q educampus` y `Start Command=python -m educampus --host 0.0.0.0 --port $PORT`.
3. Configura `EDUCAMPUS_DB=/tmp/educampus-demo.sqlite3` y `EDUCAMPUS_HTTPS=1`.
4. Comprueba la URL `/api/health` y ensaya una inscripción con `ana`. Copia la URL real al documento de entrega y guarda capturas propias de la ejecución.

**Advertencia:** en el plan gratuito el sistema de archivos es efímero. Los datos de prueba y las sesiones se reinicializan tras reinicios o despliegues; es una limitación deliberada del demostrador. Si necesitas almacenamiento persistente, sustituye SQLite efímero por un almacén persistente y valida sus garantías transaccionales. No utilizar credenciales demo ni contraseñas compartidas en producción.

## API

- `GET /api/health`: estado de servicio.
- `POST /api/login`: `{"username":"ana","password":"EduCampus2026!"}`.
- `GET /api/session`: usuario actual y token CSRF.
- `GET /api/offerings`: oferta del periodo, autenticado.
- `GET /api/enrollments`: matrículas propias del estudiante.
- `POST /api/enroll`: `{"offering_id":"OF-101"}` con cabecera `X-CSRF-Token`.
- `POST /api/logout`: cierre de sesión con token CSRF.

La documentación UML y los resultados de pruebas se encuentran en `../uml/diseno/` y `../calidad/`.
