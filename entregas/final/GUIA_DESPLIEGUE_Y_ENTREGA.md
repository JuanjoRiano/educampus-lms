# EduCampus LMS — Despliegue y entrega final

**Fecha de preparación:** 18 de noviembre de 2026. **Grupo:** Laura Vargas, Juan Tibatá y Juan Riaño.

## Estado real (no modificar sin nueva evidencia)

- Prototipo CU-02 implementado y probado localmente.
- Diagramas de secuencia, clases y estados disponibles en PDF, SVG y fuentes editables.
- 26/26 pruebas automatizadas satisfactorias; 12/12 accesos indebidos rechazados; 20/20 operaciones inválidas sin cambios parciales. `calidad/resultados_qa.json` registra los resultados medidos.
- Cloud: **NO desplegado ni verificado por el asistente**. La URL, captura y prueba de 30 minutos deben obtenerse desde la cuenta de un integrante.
- RF-04 y RF-05: modelados en la primera entrega, no implementados en el prototipo principal.
- DRE: no calculable con el historial disponible. Temporizador `after(30s)` del modelo de estados: propuesto, no implementado.

## 1. Incorporación al repositorio existente

Desde el equipo Linux, ubícate en la carpeta **padre** del repositorio existente y descomprime el ZIP de actualización:

```bash
cd ~/semestre6/ingenieriaDeSoftware/corte3
unzip -o ~/Descargas/EduCampus_LMS_Actualizacion_Final_2026-11-18.zip
cd educampus-lms
git status
```

Revisa los archivos antes del commit y verifica que no subas la base SQLite ni archivos con secretos. Después:

```bash
git add README.md .gitignore render.yaml prototipo uml/diseno calidad entregas/final
git commit -m "feat: implement CU-02, UML design and QA final delivery"
git push origin main
```

No copies ni sustituyas `.git` con ningún ZIP. El paquete completo **no incluye `.git`**.

## 2. Prueba local antes del despliegue

```bash
cd prototipo
python3 -m educampus --reset-demo
python3 -m educampus --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000. Ingresar con `ana`, contraseña `EduCampus2026!`; confirmar OF-101. Los demás perfiles y casos están documentados en `prototipo/README.md`.

En otra terminal:

```bash
cd prototipo
python3 -m unittest discover -s tests -v
python3 scripts/qa_checks.py
```

## 3. Publicación en Render

1. Iniciar sesión en https://dashboard.render.com. Conectar el repositorio GitHub privado `JuanjoRiano/educampus-lms` (hay que dar a Render permiso para leerlo).
2. Elegir **New > Blueprint** y seleccionar el archivo `render.yaml` que está en la raíz del proyecto. Alternativamente crear Web Service de tipo Python con **Root Directory** `prototipo`, **Build Command** `python -m compileall -q educampus`, y **Start Command** `python -m educampus --host 0.0.0.0 --port $PORT`.
3. Comprobar `EDUCAMPUS_DB=/tmp/educampus-demo.sqlite3` y `EDUCAMPUS_HTTPS=1` en el ambiente de Render.
4. Esperar a estado `Live`. Abrir `<URL_REAL>/api/health`, verificar respuesta `ok: true` y acceder al sitio.
5. Ejecutar una matrícula con Ana y capturar evidencia del resultado real. Si se agotó la oferta en el entorno efímero, reiniciar/deplegar nuevamente el prototipo para repoblar los datos ficticios.
6. Escribir la URL **verificada** y la fecha en el siguiente espacio, y añadir capturas de la demo cloud al directorio `entregas/final/evidencia_cloud/`.

**URL real de Render:** ______________________________________________

**Fecha y persona que verificó:** _____________________________________

**Evidencia GET /api/health:** ________________________________________

**Captura de matrícula confirmada:** __________________________________

Advertencia: en un servicio de plan gratuito Render, el sistema de archivos efímero no garantiza persistencia. Esta versión no está diseñada para usuarios reales ni datos sensibles.

## 4. Observación de disponibilidad RNF-02

Con el servicio desplegado y accesible, ejecutar desde una máquina con internet (30 minutos de observación):

```bash
cd prototipo
python3 scripts/monitor_cloud.py https://URL-REAL.onrender.com --output ../calidad/observacion_cloud_30min.json
```

**Solo después** se podrá afirmar si hubo al menos 29 de 30 respuestas correctas durante la ventana de 30 minutos. El chequeo corto de salud local no basta para esa conclusión.

## 5. Entrega, rúbrica y defensa

- Abrir `entregas/final/Dossier_Tecnico_Final_EduCampus_Grupo5_2026-11-18.pdf` para el diseño UML y QA. El código y las pruebas se entregan vía GitHub.
- Abrir `entregas/final/Presentacion_Final_EduCampus_Grupo5_2026-11-19.pptx` para la sustentación. La demo en vivo requiere enlace público real.
- Leer `entregas/final/Guion_Defensa_Final_15_Minutos.md` y ensayar el recorrido.
- Revisar fecha/hora, formato exacto y método de entrega final en Teams, pues solo la guía institucional de seis sesiones está disponible aquí; **no se confirmó una instrucción específica nueva para esta segunda entrega**.
- Mantener el repositorio privado si conserva firmas manuscritas en los PDF/DOCX originales. No publicar dichas firmas en repositorios públicos.

## 6. Limitaciones que el equipo debe reconocer

El prototipo demuestra CU-02 (RF-01 a RF-03); no afirma tener reconocimiento biométrico real ni exámenes funcionales. El modelo de estados propone `after(30s)` como mecanismo de diseño, todavía no implementado. La arquitectura usa un servidor HTTP de biblioteca estándar y una base SQLite de demostración: no es una arquitectura institucional productiva.
