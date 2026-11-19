# EduCampus LMS — Grupo 5

Proyecto final integral de Ingeniería de Software I (PCIA5008).

## Estructura

- `referencias/`: guía oficial del proyecto.
- `gestion/`: acta Scrum, Product Backlog, registro de decisiones, guion y preguntas de defensa.
- `requisitos/`: SRS v0.5 y formulario de aprobación.
- `uml/analisis/`: contexto, casos de uso, actividades, CU-02 y modelo de dominio.
- `uml/diseno/`: secuencia, clases de diseño y máquina de estados de la fase final.
- `entregas/parcial/`: paquete consolidado firmado, presentación y checklist.
- `prototipo/` y `calidad/`: prototipo funcional CU-02 y resultados QA locales.
- `entregas/final/`: dossier, presentación, guion y guía de despliegue de la entrega final.

## Versiones vigentes

- SRS firmado: `requisitos/SRS_EduCampus_LMS_v0.5_firmado.docx` y PDF.
- Acta firmada: `gestion/Acta_Scrum_01_Reunion_2026-11-07_v1.0_firmada.docx` y PDF.
- Product Backlog firmado: `gestion/Product_Backlog_EduCampus_Grupo5_v0.3_firmado.docx` y PDF.
- Consolidado: `entregas/parcial/Entrega_Parcial_EduCampus_Grupo5_2026-11-10.pdf`.
- Presentación: `entregas/parcial/Presentacion_EduCampus_Grupo5_2026-11-10.pptx` y PDF.

## Firmas

Las imágenes de firma proporcionadas por los integrantes se insertaron en los documentos que contienen bloques explícitos de aceptación. Los campos de fecha se dejaron en blanco para completarlos con la fecha efectiva de firma. Son imágenes de firmas manuscritas, no firmas digitales criptográficas.

## Integrantes

- Laura Vargas — Product Owner
- Juan Tibatá — Scrum Master
- Juan Riaño — Developer

## Tablero

https://trello.com/b/KH4FS7cE/educampus-lms-grupo-5-proyecto-final-ingenieria-de-software-i

## Entrega final — 19 de noviembre de 2026

Esta actualización incorpora un **prototipo funcional del flujo CU-02** y los entregables de diseño y calidad de la sesión 6:

- **Prototipo:** `prototipo/` — Python estándar, navegador, SQLite, validación académica, paz y salvo financiero simulado, transacción de matrícula y pruebas.
- **Diseño UML:** `uml/diseno/` — diagrama de secuencia (alt, par, loop), clases de diseño y máquina de estados (PDF, SVG y fuentes).
- **Pruebas e informe QA:** `calidad/Informe_SQA_EduCampus_2026-11-18.pdf`, JSON de resultados y complejidad McCabe.
- **Dossier final:** `entregas/final/Dossier_Tecnico_Final_EduCampus_Grupo5_2026-11-18.pdf`.
- **Presentación:** `entregas/final/Presentacion_Final_EduCampus_Grupo5_2026-11-19.pptx` y PDF.
- **Guía de despliegue:** `entregas/final/GUIA_DESPLIEGUE_Y_ENTREGA.md` y `render.yaml`.

### Iniciar el prototipo

```bash
cd prototipo
python3 -m educampus --reset-demo
python3 -m educampus --host 127.0.0.1 --port 8000
```

Abre http://127.0.0.1:8000. Credenciales exclusivamente ficticias en `prototipo/README.md`.

### Alcance y estado de verificación

RF-01 a RF-03 implementados con pruebas automáticas locales. RF-04 y RF-05 siguen como diseño documental, no como funciones desarrolladas. El despliegue cloud requiere cuenta de Render y **no se ha realizado ni verificado desde esta entrega**. La medición RNF-02 de 30 minutos y el valor DRE están pendientes por falta de evidencia suficiente. Los documentos anteriores incluyen imágenes de firmas: conservar el repositorio privado o proteger esos archivos.
