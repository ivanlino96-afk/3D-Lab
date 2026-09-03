# Plan de implementación 001: MVP de 3D-Lab

## 1. Arquitectura general

**RF cubiertos:** RF-01 a RF-39.

### Enfoque

La aplicación será un monolito modular desplegable como una sola unidad, con límites internos claros. FastAPI atenderá páginas HTML, operaciones del panel y procesos de carga. HTML semántico, CSS y JavaScript progresivo conformarán la interfaz. PostgreSQL será la única fuente de verdad para datos estructurados, historial, auditoría y trabajo pendiente de notificaciones. Los STL vivirán en almacenamiento privado fuera del área pública y solo sus metadatos se persistirán en PostgreSQL.

La solución seguirá estrictamente estas capas:

```text
Navegador
   │
   ▼
Presentación
   │  traduce solicitudes y respuestas
   ▼
Aplicación / Casos de uso
   │  coordina reglas y transacciones
   ▼
Dominio
   │  define entidades, estados e invariantes
   ▼
Infraestructura
   ├── PostgreSQL
   ├── almacenamiento privado de STL
   └── entrega de correo
```

Las dependencias apuntan hacia el dominio. Presentación no decide reglas comerciales y dominio no conoce FastAPI, HTML, PostgreSQL, archivos físicos ni proveedores de correo.

### Componentes de ejecución

- **Aplicación web:** contenido público, guía de materiales, formulario de cotización y panel administrativo.
- **Proceso de trabajos:** ejecutable Python separado que consulta en PostgreSQL notificaciones pendientes y archivos vencidos. Comparte casos de uso con la aplicación web y no introduce otra plataforma.
- **PostgreSQL:** clientes, solicitudes, catálogo, sesiones administrativas, historial, notificaciones, auditoría y métricas derivables.
- **Almacenamiento privado:** STL identificados mediante claves internas, nunca rutas o nombres públicos.

### Límites y garantías

- Una solicitud se confirma solo después de persistir cliente, solicitud, archivos válidos, estado inicial, auditoría y notificaciones pendientes dentro de una operación consistente.
- El correo se procesa después de confirmar la solicitud; su fallo no revierte datos comerciales.
- Las cargas se transfieren por bloques y no se mantienen completas en memoria.
- El límite de 20 archivos y 500 MB se valida antes y durante la recepción.
- Cada STL tiene una fecha de expiración calculada a 30 días desde su carga.
- Los estados terminales `closed` y `canceled` no admiten transiciones posteriores.

### Cumplimiento de la constitución

- **Stack simple:** un backend Python/FastAPI, una base PostgreSQL y frontend HTML/CSS/JS.
- **Trazabilidad:** cada módulo, flujo y grupo de pruebas referencia RF concretos.
- **Separación:** las reglas viven en dominio y casos de uso; las vistas solo presentan estados y resultados.
- **Pruebas:** cada caso de uso tendrá recorrido exitoso y al menos un error.
- **Persistencia:** cambios de esquema mediante migraciones; STL privados con expiración de 30 días.
- **Idioma:** identificadores internos en inglés; textos, correos, estados visibles y errores en español.

## 2. Estructura de módulos

**RF cubiertos:** RF-01 a RF-08, RF-09 a RF-22, RF-23 a RF-35 y RF-36 a RF-39.

Cada módulo mantiene la misma separación `presentation → application → domain → infrastructure`.

```text
backend/src/
├── catalog/          servicios públicos
├── materials/        exploración, comparación y mantenimiento
├── quotes/           cargas, solicitudes, folios y estados
├── customers/        identidad por correo e historial
├── administration/   autenticación, sesión y panel
├── notifications/    correo, reintentos y fallos permanentes
├── reporting/        métricas comerciales
├── retention/        expiración y eliminación de STL
├── audit/            registro inmutable de acciones
└── shared/           tipos y utilidades sin reglas específicas

frontend/src/
├── views/            páginas y fragmentos HTML
├── styles/           sistema visual responsive
└── scripts/          filtros, comparación, carga y estados de UI
```

### `catalog`

- Publica servicios activos y su llamada a cotización.
- Mantiene el contenido separado de la lógica de solicitudes.
- Cubre RF-01, RF-34 y RF-35.

### `materials`

- Consulta materiales por aplicación, propiedades, disponibilidad y costo relativo.
- Aplica el orden determinista de coincidencias, disponibilidad y costo.
- Compara materiales con unidades consistentes.
- Presenta fichas, fuentes, vigencias y valores no disponibles.
- Permite al administrador crear, editar, publicar, ordenar y archivar el catálogo.
- Cubre RF-02 a RF-08, RF-31, RF-32 y RF-37.

### `quotes`

- Gestiona sesiones de carga, validación individual, límites y reintentos.
- Confirma solicitudes, genera folios y evita duplicados.
- Controla el ciclo `open → quote_sent → in_progress → closed` y la salida `canceled`.
- Mantiene metadatos después de eliminar un STL.
- Cubre RF-10 a RF-14, RF-17 a RF-19, RF-25 a RF-29 y RF-36 a RF-39.

### `customers`

- Normaliza el correo y agrupa solicitudes bajo el mismo cliente.
- Conserva la instantánea de contacto utilizada en cada solicitud.
- Atiende registro de solicitudes de consulta, corrección o eliminación.
- Cubre RF-09, RF-15, RF-16 y RF-30.

### `administration`

- Autentica la cuenta administrativa y gestiona su sesión.
- Proporciona búsqueda, filtros, paginación, detalle y descarga autorizada.
- Cubre RF-23 a RF-26, RF-30, RF-31, RF-33 a RF-35.

### `notifications`

- Registra correos de confirmación, aviso administrativo y cambio de estado.
- Ejecuta hasta tres intentos y marca `not_delivered` al agotarlos.
- Cubre RF-19 a RF-22.

### `reporting`, `retention` y `audit`

- Calculan indicadores por periodo sin contabilizar solicitudes canceladas como ventas.
- Eliminan STL vencidos y conservan sus metadatos.
- Registran accesos, cambios de estado, ventas, descargas, eliminaciones y cambios del catálogo.
- Cubren RF-17, RF-18, RF-28, RF-29, RF-32 y RF-33.

## 3. Modelo de datos

**RF cubiertos:** RF-01 a RF-08, RF-09 a RF-22, RF-23 a RF-33 y RF-36 a RF-39.

### Entidades principales

#### `Service`

- `id`, `slug`, `name`, `summary`, `description`, `display_order`, `is_published`.
- El nombre y contenido visible se almacenan en español.
- Cubre RF-01.

#### `Customer`

- `id`, `current_name`, `original_email`, `normalized_email`, `current_phone`, fechas de creación y actualización.
- `normalized_email` es único.
- Dos personas con el mismo correo comparten `Customer`; la solicitud preserva sus datos propios.
- Cubre RF-09, RF-15, RF-16 y RF-30.

#### `QuoteRequest`

- `id`, `public_reference`, `customer_id`, instantánea de nombre, correo y teléfono, comentarios, material seleccionado, `status`, fechas de creación, confirmación, venta y finalización.
- `public_reference` es único.
- Estados internos en inglés: `open`, `quote_sent`, `in_progress`, `closed`, `canceled`.
- Etiquetas visibles en español: `Abierta`, `Cotización enviada`, `En proceso`, `Cerrada`, `Cancelada`.
- Una venta efectiva existe cuando hay fecha de venta y el estado actual no es `canceled`.
- Cubre RF-14 a RF-16, RF-27, RF-29, RF-32, RF-33, RF-38 y RF-39.

#### `UploadSession` y `UploadItem`

- Identifican el intento de carga previo a la confirmación de la solicitud.
- Cada elemento conserva nombre original, clave interna, tamaño, huella, progreso y resultado de validación.
- La sesión conserva un token de envío único para impedir confirmaciones duplicadas.
- Solo elementos válidos y completados pueden incorporarse a una solicitud.
- Cubre RF-10 a RF-14, RF-36 y RF-38.

#### `QuoteFile`

- `id`, `quote_request_id`, nombre original, clave privada, tamaño, huella, fecha de carga, fecha de expiración, fecha de eliminación y estado.
- Nombres iguales se distinguen por su ID y clave privada.
- La fecha de expiración equivale a fecha de carga más 30 días.
- Después de eliminarse conserva metadatos y estado `expired`.
- Cubre RF-10 a RF-13, RF-17, RF-18, RF-25, RF-26 y RF-36.

#### `QuoteStatusEvent`

- `id`, `quote_request_id`, estado anterior, estado nuevo, administrador, fecha y motivo opcional.
- Es de solo adición; no se edita ni elimina.
- Permite reconstruir tiempos por estado y evidencia cancelaciones posteriores a una venta.
- Cubre RF-21, RF-27 a RF-29 y RF-33.

#### `Material`

- `id`, `slug`, nombre, descripción, ventajas, limitaciones, disponibilidad, costo relativo, fuente, fecha de fuente, fecha de actualización, orden y estado de publicación.
- El costo acepta exclusivamente `low`, `medium`, `high`; se presenta como `bajo`, `medio`, `alto`.
- Estados: `draft`, `published`, `archived`.
- Cubre RF-02, RF-03, RF-06 a RF-08, RF-31, RF-32 y RF-37.

#### `Application`, `PropertyDefinition` y `MaterialPropertyValue`

- `Application`: escenario de uso y factores relevantes.
- `PropertyDefinition`: nombre, unidad y reglas de comparación.
- `MaterialPropertyValue`: material, propiedad, valor, fuente y fecha.
- Relaciones muchos-a-muchos conectan materiales con aplicaciones.
- Cubre RF-02 a RF-05 y RF-31.

#### `Certification`

- Material, nombre, evidencia, emisor, fecha inicial y fecha final de vigencia.
- Una certificación vencida no participa en afirmaciones públicas.
- Cubre RF-07 y RF-31.

#### `AdminUser` y `AdminSession`

- Una cuenta habilitada en el MVP, credencial protegida, estado y fechas de acceso.
- Las sesiones pueden invalidarse al cerrar sesión.
- Cubre RF-23.

#### `Notification`

- Evento, solicitud, destinatario, plantilla, estado, número de intentos, próximo intento, último error y fechas.
- Estados: `pending`, `sent`, `not_delivered`.
- Restricción de unicidad por evento, solicitud, destinatario y plantilla para impedir duplicados.
- Cubre RF-19 a RF-22.

#### `DataSubjectRequest` y `AuditEvent`

- `DataSubjectRequest` registra solicitudes de consulta, corrección o eliminación y su resolución.
- `AuditEvent` conserva actor, acción, entidad, identificador, fecha y resultado sin copiar datos sensibles innecesarios.
- Cubren RF-16, RF-18, RF-23, RF-26, RF-28, RF-29 y RF-31.

### Relaciones

```text
Customer 1 ─── N QuoteRequest 1 ─── N QuoteFile
                         │
                         ├──── N QuoteStatusEvent
                         ├──── N Notification
                         └──── 0..1 Material

Material N ─── N Application
Material 1 ─── N MaterialPropertyValue N ─── 1 PropertyDefinition
Material 1 ─── N Certification
AdminUser 1 ─── N AdminSession
AdminUser 1 ─── N AuditEvent
```

### Reglas de integridad

- Correo normalizado y folio público son únicos.
- Una solicitud confirmada posee al menos un archivo válido.
- La suma de archivos de una solicitud no supera 500 MB ni 20 elementos.
- `closed` y `canceled` no tienen transiciones salientes.
- Solo `in_progress` o `closed` pueden contabilizarse como venta, nunca `canceled`.
- Un material archivado permanece referenciable históricamente.
- Una certificación sin evidencia vigente no se publica como válida.
- Los cambios de esquema siempre se realizan mediante migraciones versionadas.

## 4. Diagramas y pseudocódigo

**RF cubiertos:** RF-02 a RF-08, RF-09 a RF-22, RF-23 a RF-33 y RF-36 a RF-39.

### Flujo de solicitud

```text
INICIO
  Crear sesión de carga con token único
  Por cada archivo seleccionado:
    Comprobar cantidad y total acumulado
    Recibir por bloques en almacenamiento privado
    Validar que sea STL legible
    Marcar archivo como válido o inválido
    Conservar los demás archivos válidos
  Si existen cargas pendientes: impedir envío
  Si faltan datos válidos o no existe STL válido: mostrar errores
  Al confirmar:
    Si el token ya fue consumido: devolver la solicitud existente
    Normalizar correo y localizar o crear cliente
    Crear solicitud e instantánea de contacto
    Generar un folio; repetir si ya existe
    Asociar archivos válidos
    Registrar estado Abierta y auditoría
    Registrar correos pendientes
    Confirmar solicitud y mostrar folio
FIN
```

### Ciclo de estados

```text
Abierta ───────► Cotización enviada ───────► En proceso ───────► Cerrada
   │                       │                       │
   └───────────────────────┴───────────────────────┴───────────► Cancelada

Cerrada: terminal
Cancelada: terminal
```

Al entrar en `En proceso`, se registra el evento histórico de venta. Si después se pasa a `Cancelada`, el evento permanece, pero deja de contribuir a ventas efectivas y conversión.

### Selección de materiales

```text
Recibir aplicaciones y propiedades elegidas
Excluir materiales no publicados
Para cada material:
  Contar criterios satisfechos
Ordenar por:
  1. mayor cantidad de criterios satisfechos
  2. disponible antes que no disponible
  3. costo bajo, medio y alto
Mostrar criterios que justifican cada posición
Si no hay resultados: mostrar estado vacío y permitir limpiar filtros
```

### Envío de correo

```text
Seleccionar notificación pendiente cuyo momento de intento haya llegado
Intentar entregar
Si se entrega:
  marcar Enviado
Si falla y tiene menos de tres intentos:
  incrementar contador y programar siguiente intento
Si alcanza tres fallos:
  marcar No entregado y hacerlo visible al administrador
```

### Eliminación de STL

```text
Localizar archivos vigentes con fecha de expiración cumplida
Por cada archivo:
  eliminar contenido privado
  conservar metadatos
  marcar Archivo expirado
  registrar auditoría
Si la solicitud sigue activa:
  no ofrecer reposición dentro de la plataforma
```

## 5. Decisiones técnicas justificadas

**RF cubiertos:** RF-01 a RF-39.

1. **Monolito modular:** cubre el MVP y 500 solicitudes mensuales con una operación sencilla, preservando límites que permiten separar componentes después.
2. **Vistas HTML generadas en servidor con JavaScript progresivo:** reduce dependencias, mantiene navegación funcional y reserva JavaScript para filtros, comparación, carga y retroalimentación inmediata.
3. **PostgreSQL como única persistencia estructurada:** satisface unicidad, transacciones, búsquedas, historial, auditoría, métricas y cola de notificaciones sin otro servicio de datos.
4. **Patrón de salida transaccional para correos:** registra la intención de notificar junto con el cambio comercial y permite procesarla después sin perder ni duplicar solicitudes.
5. **Proceso Python para trabajos periódicos:** ejecuta reintentos y expiración con el mismo lenguaje y casos de uso, sin añadir una plataforma de colas.
6. **Almacenamiento privado mediante interfaz:** empieza en disco privado y mantiene la regla de dominio independiente de la ubicación física.
7. **Carga por bloques y sesión previa:** soporta archivos grandes, progreso, interrupciones, archivos parcialmente válidos y confirmación idempotente sin cargar 500 MB en memoria.
8. **Transiciones de estado en dominio:** una sola política valida la secuencia, cancelación y estados terminales para todas las interfaces.
9. **Historial de solo adición:** conserva ventas, cancelaciones, descargas, eliminaciones y cambios de catálogo sin sobrescribir evidencia.
10. **Identificadores internos en inglés y etiquetas visibles en español:** cumple simultáneamente consistencia del código y experiencia en español.
11. **Migraciones versionadas:** todo cambio estructural es reproducible y auditable en cada entorno.
12. **Métricas derivadas de datos operativos:** evita duplicar cifras susceptibles de quedar desactualizadas.

## 6. Alternativas descartadas

**RF cubiertos:** RF-01 a RF-39, al preservar el alcance completo con el menor número de componentes.

| Alternativa | Motivo de descarte |
|-------------|---------------------|
| Microservicios | Añaden despliegues, comunicación y consistencia distribuida sin necesidad para 500 solicitudes mensuales. |
| Framework de frontend o aplicación de página única | Duplica complejidad frente a HTML/CSS/JS y contradice la simplicidad innegociable. |
| Segundo backend o servicio en otro lenguaje | Rompe la regla de un único stack Python. |
| Redis y Celery para trabajos | Añaden persistencia y operación adicionales; PostgreSQL puede coordinar el volumen previsto. |
| Guardar STL dentro de PostgreSQL | Mezcla archivos grandes con datos estructurados y complica respaldo, expiración y descarga. |
| Almacenamiento público con enlaces directos | Contradice privacidad, autorización y expiración de los STL. |
| Almacenamiento externo desde el primer MVP | Añade una dependencia operativa no necesaria para el volumen inicial. |
| Identificar al cliente solo mediante el folio | Impide agrupar el historial solicitado por correo. |
| Cuenta obligatoria para visitantes | Contradice la solicitud sin registro y aumenta fricción comercial. |
| Movimiento libre entre estados | Elimina la semántica de venta, cancelación y cierre terminal. |
| Enviar correo dentro de la solicitud web | Un fallo externo podría retrasar o invalidar una solicitud ya recibida. |
| Borrar solicitudes junto con el STL | Contradice la conservación del historial y las métricas. |
| Recomendaciones mediante IA | Está fuera del MVP y no es necesaria para aplicar reglas deterministas de selección. |

## 7. Estrategia de pruebas

**RF cubiertos:** RF-01 a RF-39.

### Política general

- Cada caso de uso tendrá al menos una prueba exitosa y una prueba de error.
- Ninguna entrega se acepta si una prueba requerida falla.
- Cada prueba identifica los RF y criterios de aceptación que demuestra.
- Los datos y nombres internos de prueba se escriben en inglés; los mensajes verificados se esperan en español.
- Las pruebas de persistencia se ejecutan contra PostgreSQL y aplican migraciones desde un estado vacío.

### Niveles

#### Pruebas de dominio

- Ranking, filtros, limpieza y desempate de materiales: RF-02, RF-03, RF-04 y RF-05.
- Vigencia de certificaciones y publicación: RF-06, RF-07, RF-31 y RF-37.
- Validación de contacto, reemplazo y límites de archivos: RF-09, RF-10, RF-11, RF-12, RF-13 y RF-14.
- Transiciones, estados terminales, venta y cancelación: RF-27 a RF-29.
- Cálculos de métricas: RF-33.

#### Pruebas de casos de uso

- Crear solicitud nueva y asociarla a cliente existente: RF-14 a RF-16.
- Conservar archivos válidos y reintentar interrumpidos: RF-11 a RF-13 y RF-36.
- Evitar doble envío y resolver colisión de folio: RF-38 y RF-39.
- Publicar y archivar material: RF-31, RF-32 y RF-37.
- Cambiar estado, cancelar y bloquear terminales: RF-27 a RF-29.
- Expirar archivo conservando historial: RF-17 y RF-18.
- Crear, reintentar y agotar notificaciones: RF-19 a RF-22.

#### Pruebas de integración

- Restricciones de unicidad para correo, folio y notificación: RF-14, RF-15, RF-22 y RF-39.
- Consistencia de solicitud, archivos, estado, auditoría y notificaciones: RF-14, RF-19, RF-20 y RF-28.
- Búsqueda, combinación de filtros, paginación e historial: RF-24, RF-25 y RF-30.
- Eliminación física y preservación de metadatos al día 30: RF-17, RF-18 y RF-26.
- Sesión administrativa y bloqueo de acceso no autenticado: RF-23, RF-25, RF-26 y RF-31.

#### Pruebas de interfaz y recorrido completo

- Catálogo y llamada a cotización: RF-01.
- Explorar, filtrar, comparar y abrir ficha: RF-02 a RF-07.
- Trasladar un material a la solicitud: RF-08.
- Formulario, progreso, archivos inválidos y confirmación: RF-09 a RF-14 y RF-34 a RF-36.
- Folio y correos visibles en español: RF-19 a RF-22 y RF-35.
- Panel, filtros, detalle, descarga y estados: RF-23 a RF-30 y RF-34.
- Administración del catálogo: RF-31, RF-32, RF-34 y RF-37.
- Indicadores por periodo: RF-29 y RF-33.

#### Pruebas no funcionales

- Usabilidad con 12 participantes y finalización en cinco minutos.
- Contenido principal visible dentro del objetivo para 95 % de visitas.
- Retroalimentación de carga antes de un segundo.
- Capacidad de 500 solicitudes mensuales manteniendo tiempos objetivo.
- Navegación por teclado, foco, etiquetas, contraste y diseño responsive.
- Privacidad: ningún visitante accede a datos o archivos tras el envío.
- Integridad: fallo de correo, carga o eliminación no duplica ni pierde la solicitud.
- Idioma: 100 % de mensajes públicos, administrativos y correos en español.

### Matriz de cobertura completa

| Grupo de RF | Criterios EARS vinculados | Evidencia principal |
|-------------|---------------------------|---------------------|
| RF-01 | CA-01 | Catálogo público y recorrido a cotización. |
| RF-02 a RF-08 | CA-02 a CA-06, CA-28 y CA-29 | Consultas, ranking, filtros, comparación, fichas, certificaciones y selección. |
| RF-09 a RF-16 | CA-07 a CA-11, CA-23, CA-31 y CA-32 | Contacto, carga, validación, folio, cliente e instantánea. |
| RF-17 a RF-22 | CA-12 a CA-14 y CA-30 | Expiración, confirmación, notificaciones y reintentos. |
| RF-23 a RF-30 | CA-15 a CA-18, CA-26 y CA-27 | Sesión, panel, archivos, estados, venta e historial. |
| RF-31 a RF-35 | CA-19 a CA-22, CA-28 y CA-29 | Catálogo administrable, métricas y estados de interfaz en español. |
| RF-36 a RF-39 | CA-24, CA-25, CA-29 y CA-32 | Interrupción, selección obsoleta, doble envío y colisión de folio. |

La cobertura se considera completa únicamente cuando todos los grupos anteriores tienen pruebas exitosas y de error aprobadas al 100 %.
