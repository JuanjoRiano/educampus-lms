# Actualización de evidencia final — 18 de noviembre de 2026

La entrega final anterior afirmaba que Render y RNF-02 estaban pendientes. Esta actualización corrige esos documentos sobre la base de evidencia nueva aportada por el equipo.

- URL: https://educampus-lms-demo.onrender.com
- RNF-02: **30/30 respuestas HTTP 200**, 1.800 segundos; umbral SRS 29/30. Se verifica una ventana de 30 minutos, no disponibilidad sostenida de producción.
- Evidencia original: `calidad/observacion_cloud_30min.json`
- Evidencia visual: `entregas/final/evidencia_cloud/inscripciónConfirmada.png` y `bloqueoFinanciero.png`.
- SQA actualizado: `calidad/Informe_SQA_EduCampus_2026-11-18.pdf`.
- Dossier actualizado: `entregas/final/Dossier_Tecnico_Final_EduCampus_Grupo5_2026-11-18.pdf` (11 páginas).
- Entrega integral actualizada: `entregas/final/Entrega_Final_Integral_EduCampus_Grupo5_2026-11-19.pdf` (42 páginas).
- Presentación actualizada: `entregas/final/Presentacion_Final_EduCampus_Grupo5_2026-11-19.pptx` y PDF (12 diapositivas, incluida evidencia fotográfica).

**Alcance**: RF-01, RF-02 y RF-03 están implementados en el MVP; RF-04 y RF-05 no están implementados. Las pruebas de rendimiento local no permiten inferir p95 en cloud; DRE continúa no calculable. La comprobación de salud RNF-02 no sustituye pruebas de carga ni seguridad de producción.

**Importante**: el estado de Render puede variar. Antes de la sustentación se debe comprobar que el servicio esté operativo y que haya al menos una asignatura demostrable con cupos. El proyecto utiliza SQLite efímero.

**Versionado**: este paquete reemplaza versiones anteriores con iguales nombres. No elimina la carpeta `.git`, no modifica el código del prototipo ni requiere volver a clonar.
