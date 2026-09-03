# Tareas de implementación 001: MVP de 3D-Lab

Fuentes: `specs/001-3D-Lab/spec.md` y `specs/001-3D-Lab/plan.md`.

Cada tarea respeta las capas `presentation → application → domain → infrastructure`. Los identificadores internos se escriben en inglés y todos los textos visibles en español.

## Fase 1 — Preparación del proyecto

- [X] T001 Crear la configuración del proyecto Python y sus dependencias mínimas en `backend/pyproject.toml`.
  - RF cubiertos: RF-01 a RF-39 (soporte transversal).
  - Hecho cuando: el entorno instala FastAPI, PostgreSQL, migraciones, plantillas y herramientas de prueba sin incorporar un segundo framework.
- [X] T002 Crear el punto de entrada y la configuración por entorno en `backend/src/main.py` y `backend/src/shared/config.py`.
  - RF cubiertos: RF-01 a RF-39 (soporte transversal).
  - Hecho cuando: la aplicación inicia con configuración externa validada y no contiene secretos dentro del repositorio.
- [X] T003 Crear la estructura modular y los archivos de paquete en `backend/src/` conforme al plan.
  - RF cubiertos: RF-01 a RF-39 (soporte transversal).
  - Hecho cuando: existen los módulos `catalog`, `materials`, `quotes`, `customers`, `administration`, `notifications`, `reporting`, `retention`, `audit` y `shared`, cada uno separado por capas.
- [X] T004 [P] Crear la estructura de presentación web en `frontend/src/views/`, `frontend/src/styles/` y `frontend/src/scripts/`.
  - RF cubiertos: RF-01 a RF-39 (soporte transversal).
  - Hecho cuando: las carpetas admiten vistas, estilos y JavaScript progresivo sin reglas de negocio.
- [X] T005 [P] Configurar pytest y los directorios de pruebas en `backend/tests/conftest.py` y `backend/pytest.ini`.
  - RF cubiertos: RF-01 a RF-39 (política de pruebas).
  - Hecho cuando: las suites `unit`, `integration` y `e2e` pueden ejecutarse por separado y comparten fixtures controlados.
- [X] T006 [P] Documentar variables locales sin secretos en `.env.example`.
  - RF cubiertos: RF-17, RF-19 a RF-23 y RF-26.
  - Hecho cuando: están declaradas las variables de PostgreSQL, sesión, correo y almacenamiento privado con nombres en inglés y ejemplos seguros.

## Fase 2 — Fundamentos bloqueantes

Esta fase debe concluir antes de iniciar cualquier historia de usuario.

- [X] T007 Configurar migraciones versionadas en `backend/migrations/env.py` y `backend/migrations/versions/0001_initial.py`.
  - RF cubiertos: RF-01 a RF-33 y RF-36 a RF-39.
  - Hecho cuando: una base PostgreSQL vacía puede avanzar y retroceder la migración inicial de forma reproducible.
- [X] T008 Implementar la unidad de trabajo y conexión PostgreSQL en `backend/src/shared/infrastructure/database.py`.
  - RF cubiertos: RF-14 a RF-16, RF-18 a RF-33 y RF-38 a RF-39.
  - Hecho cuando: los casos de uso pueden confirmar o revertir una transacción sin importar componentes de presentación.
- [X] T009 [P] Definir tipos comunes, reloj y generación segura de identificadores en `backend/src/shared/domain/types.py`.
  - RF cubiertos: RF-14, RF-17, RF-22, RF-28, RF-38 y RF-39.
  - Hecho cuando: tiempo, IDs internos y tokens no predecibles pueden sustituirse de manera determinista en pruebas.
- [X] T010 [P] Definir contratos de repositorios y almacenamiento en `backend/src/shared/application/ports.py`.
  - RF cubiertos: RF-01 a RF-33 y RF-36 a RF-39.
  - Hecho cuando: dominio y aplicación no importan FastAPI, PostgreSQL, sistema de archivos ni proveedor de correo.
- [X] T011 Implementar almacenamiento privado basado en claves internas en `backend/src/shared/infrastructure/private_storage.py`.
  - RF cubiertos: RF-10 a RF-13, RF-17, RF-18, RF-25, RF-26 y RF-36.
  - Hecho cuando: guardar, leer y eliminar un objeto exige una clave interna y ningún archivo queda en una ruta pública.
- [X] T012 Implementar el registro de auditoría de solo adición en `backend/src/audit/domain/entities.py` y `backend/src/audit/infrastructure/repository.py`.
  - RF cubiertos: RF-16, RF-18, RF-23, RF-26, RF-28, RF-29 y RF-31.
  - Hecho cuando: una acción conserva actor, entidad, fecha y resultado, y no existe operación para editar o borrar eventos.
- [X] T013 [P] Crear el catálogo central de mensajes en español en `backend/src/shared/presentation/messages.py`.
  - RF cubiertos: RF-34 y RF-35.
  - Hecho cuando: carga, éxito, vacío y error tienen mensajes reutilizables en español con acción de recuperación cuando aplica.
- [X] T014 [P] Crear la plantilla base accesible y responsive en `frontend/src/views/base.html` y `frontend/src/styles/base.css`.
  - RF cubiertos: RF-34 y RF-35.
  - Hecho cuando: la plantilla incluye navegación por teclado, foco visible, regiones de estado y puntos de adaptación para móvil y escritorio.
- [X] T015 Crear el ejecutor de trabajos periódicos en `backend/src/worker.py`.
  - RF cubiertos: RF-17, RF-18 y RF-22.
  - Hecho cuando: el proceso puede invocar trabajos de notificaciones y retención de forma independiente a la aplicación web.
- [X] T016 Probar las fronteras arquitectónicas en `backend/tests/architecture/test_dependencies.py`.
  - RF cubiertos: RF-01 a RF-39 (cumplimiento transversal).
  - Hecho cuando: la prueba falla si dominio importa presentación o infraestructura, o si presentación contiene una dependencia directa de persistencia.

## Fase 3 — HU-01: Conocer los servicios

Objetivo independiente: un visitante puede conocer todos los servicios publicados y abrir la solicitud de cotización.

- [X] T017 [P] [US1] Escribir pruebas de éxito y error del catálogo en `backend/tests/unit/catalog/test_list_published_services.py`.
  - RF cubiertos: RF-01, RF-34 y RF-35.
  - Hecho cuando: las pruebas verifican catálogo publicado, estado vacío y error recuperable en español antes de implementar el caso de uso.
- [X] T018 [US1] Definir la entidad y repositorio de servicios en `backend/src/catalog/domain/entities.py` y `backend/src/catalog/application/ports.py`.
  - RF cubiertos: RF-01.
  - Hecho cuando: un servicio expresa publicación y orden sin depender de FastAPI ni PostgreSQL.
- [X] T019 [US1] Implementar consulta y persistencia de servicios publicados en `backend/src/catalog/application/list_services.py` y `backend/src/catalog/infrastructure/repository.py`.
  - RF cubiertos: RF-01.
  - Hecho cuando: la consulta devuelve únicamente servicios publicados en orden estable y pasa sus pruebas de éxito y error.
- [X] T020 [US1] Crear la página pública del catálogo en `backend/src/catalog/presentation/routes.py` y `frontend/src/views/catalog/index.html`.
  - RF cubiertos: RF-01, RF-34 y RF-35.
  - Hecho cuando: cada servicio muestra descripción y acción de cotización, y los estados vacío y error aparecen en español.
- [X] T021 [US1] Validar el recorrido completo del catálogo en `backend/tests/e2e/test_service_catalog.py`.
  - RF cubiertos: RF-01, RF-34 y RF-35.
  - Hecho cuando: CA-01 y CA-22 pasan tanto con servicios publicados como sin resultados.

## Fase 4 — HU-02: Elegir un material

Objetivo independiente: el visitante explora, filtra, compara y selecciona materiales publicados con información verificable.

- [X] T022 [P] [US2] Escribir pruebas del ranking y desempate en `backend/tests/unit/materials/test_rank_materials.py`.
  - RF cubiertos: RF-02, RF-03 y RF-04.
  - Hecho cuando: las pruebas demuestran prioridad por criterios cumplidos, disponibilidad y menor costo, además de limpieza de filtros.
- [X] T023 [P] [US2] Escribir pruebas de comparación, ficha y certificación en `backend/tests/unit/materials/test_material_details.py`.
  - RF cubiertos: RF-05, RF-06 y RF-07.
  - Hecho cuando: se prueban unidades consistentes, datos `No disponible` y omisión de certificaciones sin evidencia vigente.
- [X] T024 [US2] Crear el esquema de materiales y relaciones en `backend/migrations/versions/0002_material_catalog.py`.
  - RF cubiertos: RF-02 a RF-07, RF-31, RF-32 y RF-37.
  - Hecho cuando: la migración crea materiales, aplicaciones, propiedades, valores y certificaciones con estados y restricciones válidos.
- [X] T025 [US2] Implementar entidades y reglas del catálogo en `backend/src/materials/domain/entities.py` y `backend/src/materials/domain/ranking.py`.
  - RF cubiertos: RF-02 a RF-07 y RF-37.
  - Hecho cuando: el dominio calcula coincidencias y vigencias sin conocer la interfaz ni la base de datos, y las pruebas unitarias pasan.
- [X] T026 [US2] Implementar consultas del catálogo en `backend/src/materials/application/explore_materials.py` y `backend/src/materials/infrastructure/repository.py`.
  - RF cubiertos: RF-02 a RF-07 y RF-37.
  - Hecho cuando: solo aparecen materiales publicados y cada resultado explica su posición, disponibilidad, costo y fuentes.
- [X] T027 [P] [US2] Crear exploración y filtros en `backend/src/materials/presentation/routes.py`, `frontend/src/views/materials/index.html` y `frontend/src/scripts/material-filters.js`.
  - RF cubiertos: RF-02, RF-03, RF-04, RF-34, RF-35 y RF-37.
  - Hecho cuando: se pueden combinar, mostrar y limpiar filtros, con estados de carga, vacío y error en español.
- [X] T028 [P] [US2] Crear comparación y ficha en `frontend/src/views/materials/compare.html` y `frontend/src/views/materials/detail.html`.
  - RF cubiertos: RF-05, RF-06, RF-07, RF-34 y RF-35.
  - Hecho cuando: dos o más materiales se comparan con las mismas unidades y la ficha muestra fuentes, vigencias y ausencias correctamente.
- [X] T029 [US2] Conservar la selección al iniciar una cotización en `backend/src/materials/application/select_for_quote.py` y `frontend/src/scripts/material-selection.js`.
  - RF cubiertos: RF-08 y RF-37.
  - Hecho cuando: un material publicado llega seleccionado al formulario y uno archivado se retira con aviso en español.
- [X] T030 [US2] Validar la guía completa en `backend/tests/e2e/test_material_guide.py`.
  - RF cubiertos: RF-02 a RF-08, RF-34, RF-35 y RF-37.
  - Hecho cuando: CA-02 a CA-06, CA-28 y CA-29 pasan con resultados, sin coincidencias y con una selección archivada.

## Fase 5 — HU-03: Solicitar una cotización

Objetivo independiente: un visitante sin cuenta carga STL válidos y obtiene una única solicitud asociada a su cliente.

- [X] T031 [P] [US3] Escribir pruebas de datos de contacto en `backend/tests/unit/customers/test_contact_validation.py`.
  - RF cubiertos: RF-09, RF-15 y RF-16.
  - Hecho cuando: se cubren límites válidos, formatos inválidos, normalización de correo y conservación de la instantánea por solicitud.
- [X] T032 [P] [US3] Escribir pruebas de carga y validación STL en `backend/tests/unit/quotes/test_upload_session.py`.
  - RF cubiertos: RF-10, RF-11, RF-12, RF-13 y RF-36.
  - Hecho cuando: se cubren éxito, archivo 21, más de 500 MB, STL vacío o dañado, reemplazo y carga interrumpida.
- [X] T033 [P] [US3] Escribir pruebas de confirmación idempotente en `backend/tests/unit/quotes/test_confirm_quote.py`.
  - RF cubiertos: RF-14, RF-15, RF-38 y RF-39.
  - Hecho cuando: se prueban confirmación exitosa, doble activación y colisión de folio sin crear solicitudes duplicadas.
- [X] T034 [US3] Crear el esquema de clientes, solicitudes, cargas y archivos en `backend/migrations/versions/0003_quotes.py`.
  - RF cubiertos: RF-09 a RF-18, RF-36, RF-38 y RF-39.
  - Hecho cuando: correo normalizado y folio son únicos, una solicitud conserva su contacto y cada archivo tiene expiración y metadatos.
- [X] T035 [US3] Implementar entidades e invariantes de carga en `backend/src/quotes/domain/uploads.py`.
  - RF cubiertos: RF-10 a RF-13 y RF-36.
  - Hecho cuando: el dominio impide superar 20 archivos o 500 MB, conserva válidos y bloquea el envío con cargas pendientes.
- [X] T036 [US3] Implementar validación individual de STL en `backend/src/quotes/infrastructure/stl_validator.py`.
  - RF cubiertos: RF-10 y RF-11.
  - Hecho cuando: distingue un STL legible de uno vacío, dañado o con contenido incompatible sin invalidar otros archivos.
- [X] T037 [US3] Implementar recepción por bloques y reintento en `backend/src/quotes/application/manage_uploads.py`.
  - RF cubiertos: RF-10 a RF-13 y RF-36.
  - Hecho cuando: una interrupción conserva archivos terminados y permite reintentar solo los incompletos sin mantener 500 MB en memoria.
- [X] T038 [US3] Implementar identidad por correo e instantáneas en `backend/src/customers/application/resolve_customer.py` y `backend/src/customers/infrastructure/repository.py`.
  - RF cubiertos: RF-09, RF-15 y RF-16.
  - Hecho cuando: el mismo correo normalizado reutiliza cliente y cada solicitud conserva el nombre y teléfono capturados en ese envío.
- [X] T039 [US3] Implementar confirmación transaccional y folio seguro en `backend/src/quotes/application/confirm_quote.py`.
  - RF cubiertos: RF-14, RF-15, RF-19, RF-20, RF-38 y RF-39.
  - Hecho cuando: se guardan solicitud, archivos, estado inicial, auditoría y notificaciones pendientes en una transacción, reutilizando el resultado ante doble envío y regenerando folios duplicados.
- [X] T040 [US3] Crear operaciones HTTP de carga y confirmación en `backend/src/quotes/presentation/routes.py`.
  - RF cubiertos: RF-09 a RF-15, RF-34 a RF-36, RF-38 y RF-39.
  - Hecho cuando: cada operación traduce resultados del caso de uso a respuestas en español sin contener reglas comerciales.
- [X] T041 [US3] Crear formulario y lista de archivos en `frontend/src/views/quotes/new.html` y `frontend/src/scripts/quote-upload.js`.
  - RF cubiertos: RF-09 a RF-14, RF-34 a RF-36 y RF-38.
  - Hecho cuando: se muestran nombre, tamaño, progreso y validación por archivo; se puede quitar o reemplazar; y el envío se bloquea mientras está pendiente.
- [X] T042 [US3] Implementar solicitudes de acceso, corrección y eliminación en `backend/src/customers/application/manage_data_request.py`.
  - RF cubiertos: RF-16.
  - Hecho cuando: el administrador solo puede completar una solicitud de datos tras registrar verificación desde el correo asociado.
- [X] T043 [US3] Implementar expiración automática de STL en `backend/src/retention/application/expire_quote_files.py`.
  - RF cubiertos: RF-17 y RF-18.
  - Hecho cuando: al cumplir 30 días se elimina el objeto privado, permanecen sus metadatos y se registra `Archivo expirado` sin opción de reposición.
- [ ] T044 [US3] Integrar y probar solicitud, retención e identidad en `backend/tests/integration/test_quote_lifecycle.py`.
  - RF cubiertos: RF-09 a RF-18, RF-36, RF-38 y RF-39.
  - Hecho cuando: CA-07 a CA-12, CA-23 a CA-25, CA-31 y CA-32 pasan contra PostgreSQL y almacenamiento privado de prueba.

## Fase 6 — HU-05: Gestionar solicitudes

Objetivo independiente: el administrador autenticado consulta, descarga y actualiza solicitudes con trazabilidad completa.

- [X] T045 [P] [US5] Escribir pruebas de autenticación administrativa en `backend/tests/unit/administration/test_admin_session.py`.
  - RF cubiertos: RF-23 y RF-35.
  - Hecho cuando: se prueban inicio y cierre válidos, credenciales inválidas y acceso anónimo sin revelar qué dato falló.
- [X] T046 [P] [US5] Escribir pruebas de transiciones y ventas en `backend/tests/unit/quotes/test_status_transitions.py`.
  - RF cubiertos: RF-27, RF-28 y RF-29.
  - Hecho cuando: se cubren la secuencia principal, cancelación, terminales, venta al entrar en proceso y exclusión tras cancelar.
- [X] T047 [P] [US5] Escribir pruebas de filtros e historial en `backend/tests/unit/administration/test_quote_queries.py`.
  - RF cubiertos: RF-24, RF-25, RF-26 y RF-30.
  - Hecho cuando: se prueban filtros combinados, limpieza, páginas de 50, orden descendente e intento de descargar un STL expirado.
- [X] T048 [US5] Crear el esquema de sesiones e historial de estados en `backend/migrations/versions/0004_administration.py`.
  - RF cubiertos: RF-23, RF-27, RF-28 y RF-29.
  - Hecho cuando: las sesiones pueden revocarse y los eventos de estado son de solo adición con administrador y fecha obligatorios.
- [X] T049 [US5] Implementar autenticación y sesión en `backend/src/administration/application/authenticate_admin.py` y `backend/src/administration/infrastructure/auth.py`.
  - RF cubiertos: RF-23.
  - Hecho cuando: una única cuenta habilitada inicia y cierra sesión con credencial protegida, y las rutas privadas rechazan sesiones ausentes o revocadas.
- [X] T050 [US5] Implementar reglas de transición en `backend/src/quotes/domain/status.py`.
  - RF cubiertos: RF-27, RF-28 y RF-29.
  - Hecho cuando: solo se aceptan transiciones definidas, `closed` y `canceled` son terminales y las pruebas de dominio pasan.
- [X] T051 [US5] Implementar el cambio transaccional de estado en `backend/src/quotes/application/change_quote_status.py`.
  - RF cubiertos: RF-21, RF-27, RF-28 y RF-29.
  - Hecho cuando: estado, evento histórico, venta, auditoría y aviso pendiente se guardan juntos o ninguno se guarda.
- [X] T052 [US5] Implementar búsqueda, filtros y paginación en `backend/src/administration/application/list_quotes.py` y `backend/src/administration/infrastructure/quote_queries.py`.
  - RF cubiertos: RF-24 y RF-30.
  - Hecho cuando: cliente, correo, folio, varios estados y fechas pueden combinarse y nunca se devuelven más de 50 filas por página.
- [X] T053 [US5] Implementar detalle y descarga autorizada en `backend/src/administration/application/get_quote_detail.py` y `backend/src/administration/application/download_quote_file.py`.
  - RF cubiertos: RF-25 y RF-26.
  - Hecho cuando: el detalle reúne contacto, comentarios, archivos e historial, y solo entrega objetos privados vigentes registrando auditoría.
- [X] T054 [P] [US5] Crear inicio de sesión y protección de rutas en `backend/src/administration/presentation/auth_routes.py` y `frontend/src/views/admin/login.html`.
  - RF cubiertos: RF-23, RF-34 y RF-35.
  - Hecho cuando: el acceso válido abre el panel, el cierre invalida la sesión y los errores son genéricos y están en español.
- [X] T055 [US5] Crear listado, filtros y detalle administrativo en `backend/src/administration/presentation/quote_routes.py`, `frontend/src/views/admin/quotes.html` y `frontend/src/views/admin/quote_detail.html`.
  - RF cubiertos: RF-24 a RF-30, RF-34 y RF-35.
  - Hecho cuando: el administrador filtra, pagina, abre historial, descarga archivos vigentes y cambia estados con retroalimentación visible.
- [X] T056 [US5] Crear la vista de historial del cliente y solicitudes de datos en `frontend/src/views/admin/customer_detail.html`.
  - RF cubiertos: RF-16, RF-30, RF-34 y RF-35.
  - Hecho cuando: las solicitudes aparecen de la más reciente a la más antigua y se puede registrar la verificación de una petición de datos.
- [X] T057 [US5] Validar el panel administrativo completo en `backend/tests/e2e/test_admin_quote_management.py`.
  - RF cubiertos: RF-16, RF-21, RF-23 a RF-30, RF-34 y RF-35.
  - Hecho cuando: CA-15 a CA-18, CA-22, CA-26 y CA-27 pasan para acceso autorizado, acceso negado, filtros, descarga y estados terminales.

## Fase 7 — HU-06: Administrar materiales

Objetivo independiente: el administrador mantiene el catálogo y los cambios se reflejan sin romper solicitudes históricas.

- [X] T058 [P] [US6] Escribir pruebas de mantenimiento y publicación en `backend/tests/unit/materials/test_manage_material.py`.
  - RF cubiertos: RF-06, RF-07, RF-31, RF-32 y RF-37.
  - Hecho cuando: se cubren creación, campos faltantes, orden, publicación, evidencia vencida y archivado con referencia histórica.
- [X] T059 [US6] Implementar mantenimiento del catálogo en `backend/src/materials/application/manage_material.py`.
  - RF cubiertos: RF-06, RF-07, RF-31 y RF-32.
  - Hecho cuando: crear, editar, ordenar, publicar y archivar pasan por reglas de dominio y generan auditoría.
- [X] T060 [US6] Implementar validación de publicación y certificaciones en `backend/src/materials/domain/publication.py`.
  - RF cubiertos: RF-06, RF-07 y RF-31.
  - Hecho cuando: faltantes impiden publicar y evidencia ausente o vencida impide afirmar una certificación.
- [X] T061 [US6] Implementar persistencia administrativa del catálogo en `backend/src/materials/infrastructure/admin_repository.py`.
  - RF cubiertos: RF-31 y RF-32.
  - Hecho cuando: las modificaciones conservan fecha, orden y referencias históricas, y un archivado no elimina el registro.
- [X] T062 [US6] Crear operaciones administrativas del catálogo en `backend/src/materials/presentation/admin_routes.py`.
  - RF cubiertos: RF-31, RF-32, RF-34 y RF-35.
  - Hecho cuando: todas las operaciones exigen sesión y traducen validaciones a mensajes en español sin reglas en la ruta.
- [X] T063 [US6] Crear formularios y listado administrativo en `frontend/src/views/admin/materials.html` y `frontend/src/views/admin/material_form.html`.
  - RF cubiertos: RF-31, RF-32, RF-34 y RF-35.
  - Hecho cuando: el administrador gestiona todos los campos, ve faltantes y recibe estados de carga, éxito, vacío y error.
- [X] T064 [US6] Validar publicación, certificación y archivado en `backend/tests/e2e/test_admin_materials.py`.
  - RF cubiertos: RF-06, RF-07, RF-31, RF-32, RF-34, RF-35 y RF-37.
  - Hecho cuando: CA-19, CA-20, CA-22, CA-28 y CA-29 pasan y el catálogo público refleja los cambios permitidos.

## Fase 8 — HU-04: Recibir confirmaciones

Objetivo independiente: cliente y administrador reciben avisos confiables sin afectar la operación comercial cuando el correo falla.

- [X] T065 [P] [US4] Escribir pruebas de creación y deduplicación de avisos en `backend/tests/unit/notifications/test_enqueue_notification.py`.
  - RF cubiertos: RF-19, RF-20, RF-21 y RF-22.
  - Hecho cuando: se prueban confirmación, aviso administrativo, cambio de estado y repetición del mismo evento sin duplicado.
- [X] T066 [P] [US4] Escribir pruebas de reintentos en `backend/tests/unit/notifications/test_deliver_notification.py`.
  - RF cubiertos: RF-22.
  - Hecho cuando: se cubren entrega inicial, recuperación posterior y tercer fallo marcado `not_delivered` sin cuarto intento.
- [X] T067 [US4] Crear el esquema de salida transaccional en `backend/migrations/versions/0005_notifications.py`.
  - RF cubiertos: RF-19 a RF-22.
  - Hecho cuando: evento, solicitud, destinatario y plantilla tienen unicidad y se conservan intentos, próximo intento y último error.
- [X] T068 [US4] Implementar plantillas de correo en español en `backend/src/notifications/presentation/templates/`.
  - RF cubiertos: RF-19, RF-20, RF-21 y RF-35.
  - Hecho cuando: existen plantillas verificables para solicitud aceptada, aviso administrativo y cada cambio de estado, todas con folio y contenido en español.
- [X] T069 [US4] Implementar cola y entrega de correos en `backend/src/notifications/application/deliver_notifications.py` y `backend/src/notifications/infrastructure/email_gateway.py`.
  - RF cubiertos: RF-19 a RF-22.
  - Hecho cuando: el trabajador entrega pendientes, reprograma fallos hasta tres intentos y nunca revierte una solicitud o cambio de estado.
- [X] T070 [US4] Mostrar avisos no entregados en `frontend/src/views/admin/notifications.html` y `backend/src/notifications/presentation/admin_routes.py`.
  - RF cubiertos: RF-22, RF-34 y RF-35.
  - Hecho cuando: el administrador identifica folio, destinatario, tipo y último error de todo correo agotado.
- [X] T071 [US4] Validar confirmaciones y fallos en `backend/tests/integration/test_notification_delivery.py`.
  - RF cubiertos: RF-19 a RF-22, RF-34, RF-35 y RF-39.
  - Hecho cuando: CA-13, CA-14, CA-22, CA-30 y CA-32 pasan con entrega exitosa, colisión de folio y proveedor indisponible.

## Fase 9 — HU-07: Medir resultados

Objetivo independiente: el administrador consulta indicadores comerciales exactos para un periodo.

- [X] T072 [P] [US7] Escribir pruebas de métricas en `backend/tests/unit/reporting/test_calculate_metrics.py`.
  - RF cubiertos: RF-29 y RF-33.
  - Hecho cuando: se prueban periodo vacío, cotizaciones enviadas, ventas vigentes, venta cancelada, conversión y tiempo por estado.
- [X] T073 [US7] Implementar consultas agregadas en `backend/src/reporting/infrastructure/metrics_queries.py`.
  - RF cubiertos: RF-28, RF-29 y RF-33.
  - Hecho cuando: los cálculos usan solicitudes y eventos históricos sin mantener contadores duplicados.
- [X] T074 [US7] Implementar el caso de uso de indicadores en `backend/src/reporting/application/get_commercial_metrics.py`.
  - RF cubiertos: RF-29 y RF-33.
  - Hecho cuando: devuelve aceptadas, cotizadas, ventas no canceladas, conversión y promedio por estado para el periodo solicitado.
- [X] T075 [US7] Crear el panel de indicadores en `backend/src/reporting/presentation/routes.py` y `frontend/src/views/admin/metrics.html`.
  - RF cubiertos: RF-33, RF-34 y RF-35.
  - Hecho cuando: el administrador elige un periodo y ve cifras, estado vacío o error recuperable en español.
- [X] T076 [US7] Validar indicadores contra historial real en `backend/tests/integration/test_commercial_metrics.py`.
  - RF cubiertos: RF-28, RF-29, RF-33, RF-34 y RF-35.
  - Hecho cuando: CA-18, CA-21 y CA-22 pasan incluyendo una solicitud que fue venta y después fue cancelada.

## Fase 10 — Calidad transversal y cierre

- [X] T077 [P] Unificar estados visuales e iconos en `frontend/src/views/components/status.html` y `frontend/src/styles/status.css`.
  - RF cubiertos: RF-34 y RF-35.
  - Hecho cuando: consulta, filtro, envío, carga, descarga, cambio de estado y materiales muestran carga, éxito, vacío o error en español.
- [X] T078 [P] Completar estilos responsive y accesibles en `frontend/src/styles/responsive.css`.
  - RF cubiertos: RF-01 a RF-08, RF-09 a RF-14, RF-23 a RF-35 y RF-37.
  - Hecho cuando: los recorridos públicos y administrativos funcionan con teclado y en móvil, tableta y escritorio sin pérdida de contenido.
- [X] T079 Probar privacidad y autorización de archivos en `backend/tests/security/test_private_access.py`.
  - RF cubiertos: RF-16 a RF-18, RF-23, RF-25 y RF-26.
  - Hecho cuando: visitantes, sesiones vencidas y referencias manipuladas no acceden a clientes, solicitudes ni STL.
- [X] T080 Probar capacidad de cargas y consultas en `backend/tests/performance/test_capacity.py`.
  - RF cubiertos: RF-10, RF-13, RF-24, RF-33 y RF-36.
  - Hecho cuando: se documenta que 500 solicitudes mensuales, cargas por bloques y páginas de 50 mantienen los objetivos definidos en la especificación.
- [ ] T081 Ejecutar pruebas de usabilidad y registrar evidencia en `specs/0013D-Lab/evidence/usability.md`.
  - RF cubiertos: RF-01 a RF-16, RF-34 a RF-38.
  - Hecho cuando: al menos 11 de 12 participantes de los perfiles definidos completan una solicitud válida sin ayuda en cinco minutos.
- [X] T082 Crear la matriz final de trazabilidad en `specs/0013D-Lab/evidence/traceability.md`.
  - RF cubiertos: RF-01 a RF-39.
  - Hecho cuando: cada RF y CA apunta al menos a una tarea, una prueba de éxito y una prueba de error ejecutada.
- [ ] T083 Ejecutar la puerta de calidad y registrar resultados en `specs/0013D-Lab/evidence/release-check.md`.
  - RF cubiertos: RF-01 a RF-39.
  - Hecho cuando: migraciones desde cero, pruebas, lint y formato aprueban al 100 %, no hay secretos y la revisión confirma que dominio no importa frameworks.

## Dependencias

- Fase 1 → Fase 2.
- Fase 2 → HU-01, HU-02 y HU-03.
- HU-02 → T029 y la validación de selección en HU-03.
- HU-03 → HU-05, porque el panel necesita solicitudes persistidas.
- HU-05 → HU-04, porque los avisos de estado dependen del flujo administrativo.
- HU-02 y HU-05 → HU-06, porque el mantenimiento reutiliza el catálogo público y la sesión administrativa.
- HU-05 → HU-07, porque las métricas dependen del historial de estados y ventas.
- Todas las historias → Fase 10.

## Oportunidades de ejecución paralela

- T004, T005 y T006 pueden realizarse en paralelo después de T001.
- T009, T010, T013 y T014 pueden realizarse en paralelo después de crear la estructura.
- Las pruebas marcadas `[P]` de cada historia pueden escribirse en paralelo antes de su implementación.
- HU-01 y el núcleo de HU-02 pueden avanzar en paralelo tras la Fase 2.
- HU-06 y HU-07 pueden avanzar en paralelo una vez disponibles sus dependencias administrativas.
- T077 y T078 pueden avanzar en paralelo antes de las validaciones finales.

## Estrategia incremental

1. Entregar primero Fases 1 y 2 como base verificable.
2. Completar HU-01 para publicar la propuesta de servicios.
3. Completar HU-02 y HU-03 para formar el primer incremento comercial capaz de recibir cotizaciones.
4. Completar HU-05 y HU-04 para operar solicitudes y comunicaciones.
5. Completar HU-06 y HU-07 para mantener información y medir ventas.
6. Cerrar con la Fase 10 y aceptar el MVP únicamente con todas las pruebas en verde.

## Criterio global de finalización

El MVP está hecho cuando T001–T083 están marcadas como completadas, RF-01–RF-39 y CA-01–CA-32 tienen evidencia trazable, cada caso de uso posee al menos una prueba exitosa y una de error, y el conjunto completo aprueba al 100 %.
