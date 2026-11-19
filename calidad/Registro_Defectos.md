# Registro de defectos del desarrollo de EduCampus LMS

El registro documenta dos problemas técnicos detectados durante la revisión local de noviembre de 2026. La lista no constituye un historial exhaustivo de todos los defectos del desarrollo y no permite estimar DRE.

| ID | Hallazgo | Acción aplicada | Estado |
|---|---|---|---|
| DEF-01 | Conexiones SQLite no se cerraban necesariamente al finalizar el contexto de lectura, generando `ResourceWarning` en pruebas de concurrencia. | Se reemplazó el manejo por un gestor de contexto que cierra las conexiones en `finally`. Se repitieron los tests con `-Wd`. | Corregido localmente |
| DEF-02 | La primera versión de la consulta financiera estaba asociada a un periodo fijo, en vez de usar el periodo de la oferta. | Se recupera `period_id` de la oferta antes de consultar el simulador financiero. | Corregido localmente |

**DRE:** no calculable. No hay evidencia de defectos detectados después de la liberación en producción.
