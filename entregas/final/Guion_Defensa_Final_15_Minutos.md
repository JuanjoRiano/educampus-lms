# EduCampus LMS — Guion de sustentación final (15 minutos)

**Objetivo:** explicar decisiones técnicas y demostrar el CU-02 en vivo sin atribuir al sistema funcionalidades que todavía no se han programado. **No inventar una URL de nube.**

| Diapositiva | Tiempo sugerido | Integrante | Idea principal |
|---|---|---|---|
| 1 | 00:00–00:40 | Laura | Introducción del Grupo 5 y EduCampus LMS. |
| 2 | 00:40–01:40 | Laura | Problema, alcance, RF-01/03 y módulos futuros RF-04/05. |
| 3 | 01:40–03:10 | Juan Riaño | Arquitectura, puerto del sistema financiero y transacción atómica. |
| 4 | 03:10–04:40 | Juan Riaño | Secuencia con fragmentos par, loop y alt. |
| 5 | 04:40–05:45 | Juan Riaño | Clases implementadas, persistencia y relaciones. |
| 6 | 05:45–06:40 | Juan Riaño | Estados y temporizador de diseño no implementado. |
| 7 | 06:40–09:40 | Juan Riaño | Demostración funcional (éxito + duplicado). |
| 8 | 09:40–10:45 | Juan Riaño | Casos A1–A6, respuesta del simulador y ausencia de cambios parciales. |
| 9 | 10:45–12:10 | Juan Tibatá | 26 pruebas; RNF-01/03/04/05 y límites de medición. |
| 10 | 12:10–13:20 | Juan Tibatá | McCabe, DRE no calculable, riesgos técnicos. |
| 11 | 13:20–14:30 | Laura | Cumplimientos, pendientes cloud y cierre. |
| Reserva | 14:30–15:00 | Equipo | Margen para cambios de pantalla o una pregunta. |

## Texto base de intervención

**Laura · inicio:** “Presentamos EduCampus LMS, un sistema de gestión académica cuyo flujo principal de demostración es la inscripción de asignaturas. Esta entrega reúne diseño UML, prototipo ejecutable y evidencias de calidad. El alcance implementado cubre la consulta de ofertas, el estado financiero simulado y la confirmación de matrícula; asistencia y exámenes forman parte del SRS, pero no de esta versión del prototipo.”

**Juan Riaño · arquitectura:** “El navegador llama al Handler HTTP, que autentica al estudiante y comprueba el token CSRF. EnrollmentService ejecuta las verificaciones académica y financiera preliminares en paralelo. Si ambas resultan favorables, SQLiteEnrollmentRepository abre una transacción con `BEGIN IMMEDIATE`, revalida cupos, inserta la matrícula y decrementa exactamente un cupo. Si algo falla, aplica rollback.”

**Juan Riaño · secuencia:** “En el diagrama `par` representa la bifurcación de comprobaciones independientes; `loop` expresa la validación de cada prerrequisito; `alt` separa confirmación, errores de negocio y fallo de persistencia. La implementación utiliza ThreadPoolExecutor y espera ambas respuestas antes de continuar.”

**Juan Riaño · clases y estados:** “El servicio contiene un validador, una interfaz para el sistema financiero y un repositorio. La implementación utiliza un adaptador financiero simulado. El estado compuesto VALIDANDO representa las dos comprobaciones. `after(30s)` pertenece al diseño de un manejo futuro de timeout; esta versión ya rechaza respuestas no disponibles, pero no implementa un temporizador asíncrono de 30 segundos.”

**Juan Riaño · demo:** “Ingreso con Ana, consulto el periodo y elijo OF-101. Antes había 19 cupos y después habrá 18, salvo que se haya realizado una matrícula anterior en este entorno. Al confirmar obtengo estado CONFIRMADA. Repito la solicitud para probar que el sistema rechaza la duplicidad sin descontar otro cupo.” Si OF-101 ya está inscrita, reiniciar el entorno demo local o escoger una oferta nueva.

**Juan Riaño · alternativas:** “Las cuentas ficticias permiten reproducir bloqueo de paz y salvo, indisponibilidad financiera, prerrequisitos y cruces de horario. También existe una oferta sin cupos. La prueba E1 fuerza un error de persistencia desde tests para comprobar rollback; no expusimos esa falla como acción para usuarios.”

**Juan Tibatá · QA:** “Las pruebas automatizadas unitarias y HTTP sumaron 26 y pasaron. Medimos 30 solicitudes locales de consulta de oferta: el p95 quedó por debajo de tres segundos, pero esto no valida desempeño cloud. Las 12 solicitudes de acceso indebido fueron rechazadas y 20 casos inválidos no dejaron cambios parciales. La ventana de disponibilidad cloud de 30 minutos está pendiente.”

**Juan Tibatá · métricas:** “Calculamos complejidad ciclomática con una regla AST reproducible y la expresión v(G)=P+1. Reportamos valores para validación académica, servicio y repositorio. No informamos un DRE porcentual porque faltan datos reales de defectos anteriores y posteriores a la liberación.”

**Laura · cierre:** “La principal contribución es la trazabilidad entre requisitos, diagramas, código y pruebas. El entregable contiene la configuración para publicarse en Render; para afirmar que el requisito cloud está cumplido debemos disponer de una URL operativa y su evidencia real.” Si la URL ya está operativa, sustituir esta última frase por el enlace efectivamente verificado.

## Preguntas de defensa

**¿Por qué usar fork/join?** Porque la regla académica y la financiera son independientes y se esperan ambas antes de confirmar. El código hace comprobaciones preliminares concurrentes y revalida academia en la transacción.

**¿Cómo evitan una sobreventa del último cupo?** `BEGIN IMMEDIATE`, revalidación bajo bloqueo de escritura, `UPDATE` condicionado a `remaining > 0`, restricción UNIQUE e inserción/transacción atómica.

**¿Qué pasa si el sistema financiero no responde?** Rechazo con estado de servicio no disponible; no se crea la inscripción ni se descuenta cupo.

**¿Por qué no hay biometría real?** Porque el SRS autoriza simulaciones y exige privacidad, con cero imágenes o plantillas biométricas reales. La implementación de RF-04 no está incluida en el MVP.

**¿Se cumplen todos los RNF?** No. RNF-01, 03 y 04 tienen evidencia local; RNF-05 se sustenta en revisión del código y datos ficticios. RNF-02 necesita medir 30 minutos en la instancia cloud.

**¿Qué patrón de diseño utilizan?** Puerto/estrategia de pasarela financiera (`FinancialGateway` con adaptador `SimulatedFinancialGateway`) y repositorio para aislar persistencia. La arquitectura es deliberadamente mínima.

**¿Por qué DRE no tiene valor?** Una tasa de remoción exige defectos detectados antes y después de liberar el producto; falta la segunda medición.
