# AGENTS.md — 3D-Lab

## Identidad del proyecto

- **Proyecto:** 3D-Lab
- **Spec ID:** 001
- **Idioma del producto:** español
- **Objetivo de negocio:** convertir visitantes en clientes mediante solicitudes de cotización para servicios de manufactura aditiva.
- **Indicador principal:** ventas concretadas.
- **Capacidad inicial objetivo:** aproximadamente 500 solicitudes mensuales, con crecimiento posterior sin rediseñar el dominio.

## Descripción

3D-Lab es una plataforma web informativa y comercial para presentar servicios de impresión 3D, diseño e ingeniería, orientar al cliente en la selección de materiales y recibir solicitudes de cotización con archivos STL.

El MVP no procesa pagos, no gestiona suscripciones, no incorpora inteligencia artificial y no se integra con CRM, WhatsApp ni facturación. El cierre comercial y el pago se realizan fuera de la plataforma.

## Alcance del MVP

### Catálogo de servicios

Mostrar de forma visual:

- Tecnologías y materiales de impresión 3D disponibles.
- Prototipos funcionales y piezas personalizadas.
- Componentes industriales, eléctricos, mecánicos y de automatización.
- Refacciones y piezas de reemplazo.
- Diseño desde cero, ingeniería inversa y optimización para manufactura aditiva.
- Diseño de componentes eléctricos y electrónicos.
- Asesoría técnica y selección de procesos y materiales.

### Roles

Solo existen dos roles en el MVP:

#### Visitante

- Navega por todo el contenido público.
- Usa la guía de selección de materiales.
- Solicita cotizaciones sin crear una cuenta.
- Proporciona nombre, correo electrónico y teléfono.
- Adjunta archivos STL y requerimientos del proyecto.
- Recibe un folio y notificaciones por correo.

#### Administrador

- Existe una sola cuenta administrativa en el MVP.
- Inicia sesión en un panel privado.
- Consulta, busca y filtra clientes y solicitudes.
- Visualiza y descarga los STL de cada solicitud.
- Cambia el estado de una cotización.
- Consulta el historial de solicitudes asociado a un cliente.
- Elimina archivos inválidos u obsoletos.
- Registra manualmente una venta concretada.

No implementar registro, inicio de sesión ni portal privado para visitantes.

### Flujo principal de cotización

1. El visitante consulta servicios o materiales.
2. Inicia una solicitud de cotización.
3. Captura nombre, correo electrónico y teléfono.
4. Adjunta uno o varios archivos STL.
5. Agrega comentarios y requerimientos especiales.
6. El frontend valida el formulario y muestra progreso de carga.
7. El backend vuelve a validar datos, cantidad, tamaño y contenido de los archivos.
8. El sistema normaliza el correo y busca un cliente existente.
9. Si el correo existe, crea una nueva solicitud asociada al mismo cliente; si no existe, crea primero al cliente.
10. El sistema genera un ID interno y un folio público no predecible para la solicitud.
11. El sistema confirma la recepción en pantalla y por correo.
12. El administrador recibe un aviso de nueva solicitud.

Mensaje de confirmación:

> ✅ Hemos recibido correctamente tus archivos y la información de tu proyecto.
>
> Nuestro equipo técnico revisará tu solicitud y un asesor se pondrá en contacto contigo a la brevedad para proporcionar una cotización personalizada y resolver cualquier duda relacionada con tu proyecto.

### Estados de la cotización

Usar exclusivamente estos estados en el MVP:

- `abierta`
- `en_proceso`
- `entregada`
- `cerrada`

Cada transición debe registrar estado anterior, estado nuevo, fecha y actor. No inventar estados adicionales sin actualizar primero la especificación. Mientras el Product Owner no indique otra cosa, mostrar una explicación visible para evitar confundir `entregada` con cotización enviada o pieza entregada.

### Gestión de archivos STL

- Aceptar únicamente `.stl` en el MVP.
- Máximo 20 archivos por solicitud.
- Máximo 500 MB sumando todos los archivos de una solicitud.
- No confiar en la extensión: validar firma, estructura y capacidad de lectura del STL.
- Rechazar archivos vacíos, corruptos o cuyo tamaño exceda los límites.
- Sanear el nombre original y generar un nombre interno aleatorio.
- Guardar archivos fuera del directorio público del servidor.
- No almacenar binarios STL dentro de PostgreSQL; guardar metadatos y ruta o clave de almacenamiento.
- Mostrar nombre, tamaño, estado de carga y errores por archivo.
- Implementar carga progresiva y evitar conservar solicitudes parciales abandonadas.
- Conservar los STL durante un mes y eliminarlos mediante una tarea automática. Hasta que el Product Owner precise el evento inicial del plazo, calcularlo desde el cierre de la solicitud, que es la opción más segura para la operación.
- Registrar toda eliminación en la auditoría.
- Conservar el historial y los metadatos de la solicitud aunque el STL haya sido eliminado; la UI debe indicar que el archivo expiró y no mostrar enlaces rotos.

### Clientes y solicitudes

- Un cliente puede tener múltiples solicitudes.
- Cada cliente tiene un ID interno independiente de su correo.
- Normalizar el correo para localizar coincidencias, sin exponerlo como clave técnica.
- El correo normalizado debe tener una restricción única.
- Cada solicitud tiene un ID interno y un folio público propio.
- Conservar los datos del cliente para reutilizarlos si solicita otra cotización en el futuro.
- Preparar mecanismos de corrección y eliminación de datos personales, aunque la retención comercial no tenga una fecha de vencimiento definida.
- Conservar en cada solicitud una instantánea de los datos de contacto utilizados al enviarla, para que cambios posteriores no alteren el historial.

### Correos y notificaciones

Enviar correos transaccionales en estos eventos:

- Confirmación al cliente con folio después de recibir la solicitud completa.
- Aviso al administrador cuando se crea una solicitud.
- Aviso al cliente cuando cambia el estado de su solicitud.

Requisitos:

- Enviar en segundo plano; no bloquear la respuesta HTTP principal.
- Registrar estado, proveedor, intentos y último error.
- Aplicar reintentos con espera incremental e idempotencia para evitar duplicados.
- Usar un dominio remitente autenticado.
- Mantener plantillas en español y separar contenido de la lógica de envío.

### Panel administrativo

- Inicio de sesión seguro para una sola cuenta inicial.
- Dashboard con total de solicitudes y conteo por estado.
- Listado paginado con búsqueda y filtros por estado, fecha, cliente y correo.
- Detalle del cliente con su historial completo.
- Detalle de la solicitud con contacto, comentarios, archivos y línea de tiempo.
- Descarga privada y autorizada de STL.
- Cambio de estado con confirmación y registro histórico.
- Registro manual de venta concretada, fecha e importe opcional.
- Exportación CSV de solicitudes y ventas.
- Indicadores mínimos: solicitudes, cotizaciones entregadas, ventas concretadas, tasa de conversión y tiempo promedio de atención.

## Guía de selección de materiales

Implementar una experiencia funcional inspirada en [Bambu Lab Filament Collections](https://bambulab.com/en/filament/collections), pero con diseño, textos, datos, imágenes y código originales de 3D-Lab. No copiar marca, recursos visuales, fichas técnicas, fotografías ni contenido propietario. Los datos técnicos publicados deben provenir de proveedores autorizados o mediciones propias y registrar su fuente.

### Navegación principal

La guía debe tener tres vistas públicas conectadas:

1. **Explorar:** descubrir materiales por aplicación, propiedad o compatibilidad.
2. **Comparar:** seleccionar materiales y compararlos lado a lado.
3. **Detalle del material:** consultar descripción, rendimiento, usos, ventajas, limitaciones y datos técnicos.

Todas las vistas deben conservar la selección del usuario al navegar hacia la cotización. El CTA principal será `Solicitar cotización` y deberá preseleccionar el material o criterios elegidos.

### Explorar por aplicación

Presentar tarjetas visuales con descripción breve para, como mínimo:

- Uso exterior.
- Piezas decorativas, juguetes y modelismo.
- Piezas funcionales.
- Piezas mecánicas.
- Automotriz.
- Componentes estructurales.
- Modelos arquitectónicos.
- Aplicaciones eléctricas y electrónicas.
- Prototipos y validación de producto.

Al abrir una aplicación:

- Explicar los factores relevantes para esa aplicación.
- Mostrar materiales recomendados y disponibles en 3D-Lab.
- Permitir ordenar o ponderar resultados por costo, facilidad de impresión, rigidez, resistencia térmica y resistencia al impacto.
- Explicar por qué se recomienda cada material; no mostrar recomendaciones opacas.
- No recomendar materiales no disponibles sin marcarlos claramente como `bajo pedido` o `no disponible`.

### Explorar por propiedades

Permitir seleccionar una o varias propiedades:

- Costo accesible.
- Facilidad de impresión.
- Resistencia al impacto.
- Resistencia al agua.
- Resistencia térmica.
- Resistencia UV.
- Flexibilidad.
- Resistencia al desgaste.
- Resistencia a aceites y grasas.
- Estabilidad dimensional.
- Resistencia mecánica.
- Rigidez.
- Retardancia a la flama.
- Calidad de acabado.
- Transparencia o translucidez.

Los resultados deben actualizarse sin recargar toda la página, mostrar filtros activos, permitir limpiarlos y presentar estados `loading`, `success`, `empty` y `error`.

### Seguridad y certificaciones

Permitir filtrar materiales por certificaciones o pruebas cuando existan datos verificables:

- Seguridad química del material.
- Emisiones y calidad del aire interior.
- Contacto con alimentos.
- Seguridad para juguetes.
- Retardancia a la flama.

No afirmar que un material es seguro, certificado o apto para una aplicación regulada sin registrar el estándar, emisor, documento y vigencia. Mostrar una advertencia de que la guía orienta, pero la selección final requiere validación técnica de 3D-Lab.

### Comparador de materiales

- Permitir elegir materiales por familia y buscador.
- Mostrar los materiales seleccionados como columnas y las propiedades como filas.
- En móvil, usar tarjetas o desplazamiento horizontal accesible.
- Permitir agregar, quitar y limpiar materiales sin recargar la página.
- Resaltar diferencias y valores no disponibles.
- Mantener encabezados y nombres de propiedades visibles durante el desplazamiento.
- Ofrecer comparación por categorías plegables.

Categorías mínimas:

- Resistencia y tenacidad.
- Rigidez y adhesión entre capas.
- Resistencia térmica.
- Absorción de humedad y estabilidad dimensional.
- Densidad y acabado.
- Facilidad de impresión y costo relativo.
- Resistencia ambiental y química.
- Parámetros de impresión.
- Compatibilidad con equipos disponibles en 3D-Lab.
- Posprocesado y recomendaciones de almacenamiento.

Usar unidades consistentes y mostrar `No disponible` cuando no exista un dato; nunca inventar valores.

### Ficha de material

Cada material debe incluir:

- Nombre comercial y familia genérica.
- Resumen y propuesta de valor.
- Disponibilidad y costo relativo.
- Indicadores visuales de propiedades principales.
- Aplicaciones recomendadas.
- Ventajas y limitaciones.
- Colores y acabados disponibles.
- Compatibilidad con impresoras, boquillas y procesos de 3D-Lab.
- Temperatura de boquilla y cama, velocidad, ventilación y necesidad de cámara cerrada cuando correspondan.
- Requisitos de secado, almacenamiento, adhesión y posprocesado.
- Galería de casos o piezas de ejemplo propios.
- Fuente y fecha de actualización de los datos técnicos.
- Ficha técnica descargable solo cuando 3D-Lab tenga derecho a publicarla.
- CTA para solicitar cotización con el material preseleccionado.

### Administración de materiales

El administrador debe poder mantener sin modificar código:

- Materiales y familias.
- Aplicaciones y propiedades.
- Valores, unidades y escalas de comparación.
- Ventajas, limitaciones, colores y acabados.
- Disponibilidad, costo relativo y orden de aparición.
- Compatibilidad con equipos y parámetros técnicos.
- Certificaciones, fuente, documento y vigencia.
- Estado `publicado`, `borrador` o `archivado`.

Los cambios deben quedar registrados en auditoría. Un material archivado debe permanecer visible en solicitudes históricas, pero no ofrecerse en nuevas cotizaciones.

## Funcionalidades fuera del MVP

- IA o recomendaciones generadas por modelos.
- Pagos o anticipos en línea.
- Suscripciones.
- Portal y cuentas de cliente.
- CRM, WhatsApp, facturación u otras integraciones comerciales.
- Cotización automática basada en geometría.
- Aplicación móvil nativa.

## Arquitectura

Aplicar Clean Architecture sin saltar capas:

```text
Presentation → Application / UseCases → Domain → Infrastructure / Data
```

- `domain` no depende de frameworks, FastAPI, SQLAlchemy ni detalles de infraestructura.
- `application` coordina casos de uso y depende de abstracciones del dominio.
- `infrastructure` implementa persistencia, archivos, correo y tareas programadas.
- `presentation` contiene endpoints, schemas HTTP y vistas web.
- La validación de reglas de negocio vive en dominio o casos de uso; no duplicarla en controladores.
- Inyectar repositorios, almacenamiento y correo mediante interfaces.

## Stack tecnológico

- **Frontend:** HTML semántico, CSS y JavaScript; Jinja2 cuando las vistas se sirvan desde FastAPI.
- **Backend:** Python y FastAPI.
- **Validación:** Pydantic.
- **Persistencia:** PostgreSQL con SQLAlchemy y Alembic.
- **Archivos:** almacenamiento privado en VPS mediante una interfaz reemplazable por almacenamiento compatible con S3.
- **Servidor:** Nginx con HTTPS delante de FastAPI.
- **Despliegue:** Docker y Docker Compose en VPS.
- **Pruebas:** Pytest.
- **Calidad:** Ruff.

## Modelo de datos mínimo

- `Customer`: ID, nombre, correo original, correo normalizado, teléfono y fechas.
- `QuoteRequest`: ID, folio, cliente, instantánea de contacto, comentarios, estado y fechas.
- `QuoteFile`: ID, solicitud, nombre original saneado, clave interna, tamaño, hash, estado y fechas de carga, expiración y eliminación.
- `QuoteStatusHistory`: solicitud, estado anterior, estado nuevo, actor y fecha.
- `Sale`: solicitud, fecha de concreción, importe opcional y referencia opcional.
- `Notification`: evento, destinatario, plantilla, estado, intentos y último error.
- `AuditEvent`: actor, acción, entidad, identificador, fecha y metadatos no sensibles.
- `Material`: familia, nombre, descripción, disponibilidad, costo relativo, estado y fuente.
- `MaterialProperty`: propiedad, valor, unidad, escala y fuente.
- `Application`: nombre, descripción y factores relevantes.
- Relaciones muchos-a-muchos entre materiales, aplicaciones, propiedades, certificaciones y equipos compatibles.

## Diseño y experiencia de usuario

Consultar `UI_STYLE_GUIDE.md` antes de implementar cualquier vista.

- Dirección visual premium y minimalista inspirada en Apple.com, sin copiar su identidad.
- Jerarquía tipográfica fuerte, amplio espacio en blanco, imágenes o renders propios y animaciones discretas.
- El contenido y los modelos 3D son protagonistas; evitar decoración innecesaria.
- Diseño responsive para computadora, tableta y teléfono.
- Todo el producto se presenta en español.
- Objetivo mínimo de accesibilidad: WCAG 2.1 AA.
- Respetar `prefers-reduced-motion`.
- Navegación completa por teclado, foco visible, etiquetas accesibles y contraste suficiente.
- Evitar animaciones o recursos que perjudiquen el rendimiento móvil.
- Cada operación asíncrona debe representar explícitamente `loading`, `success`, `empty` cuando aplique y `error`.
- Los errores deben notificarse con icono y texto comprensible; nunca depender únicamente del color.

## Seguridad y privacidad

- Todo tráfico debe usar HTTPS.
- La cuenta administrativa debe usar contraseña robusta almacenada con un hash seguro; preparar soporte para doble factor.
- Usar sesiones seguras, cookies `HttpOnly`, `Secure` y `SameSite`, protección CSRF y cierre de sesión.
- Aplicar autorización en backend para cada acción administrativa y cada descarga.
- No exponer rutas físicas, IDs secuenciales ni nombres internos de archivos.
- Aplicar límites de carga tanto en Nginx como en FastAPI, manteniendo 500 MB por solicitud.
- Prevenir path traversal, archivos comprimidos engañosos y nombres maliciosos.
- No registrar contraseñas, contenido de archivos ni datos personales innecesarios en logs.
- Mantener copias de seguridad cifradas de PostgreSQL y probar restauraciones.
- Preparar mecanismos para consultar, corregir y eliminar datos personales.
- No declarar cumplimiento normativo sin validación legal específica.

## Auditoría y analíticas

Registrar al menos:

- Inicio y cierre de sesión administrativo, intentos fallidos y recuperación de acceso.
- Creación y edición de clientes y solicitudes.
- Cambios de estado.
- Descargas y eliminaciones de STL.
- Registro de ventas.
- Cambios en el catálogo de materiales.

Medir sin incluir datos sensibles en herramientas analíticas:

- Solicitudes creadas.
- Solicitudes por estado.
- Cotizaciones entregadas.
- Ventas concretadas.
- Conversión de solicitud a venta.
- Tiempo promedio entre apertura, proceso, entrega y cierre.
- Materiales, aplicaciones y filtros más consultados.

## Rendimiento y escalabilidad

- Diseñar para 500 solicitudes mensuales y picos razonables de carga concurrente.
- Paginar listados administrativos y consultas de materiales.
- Crear índices para correo normalizado, folio, estado y fechas.
- Procesar correos, expiración y limpieza fuera del ciclo de la petición HTTP.
- Vigilar uso de disco y alertar antes de alcanzar umbrales críticos.
- Mantener el almacenamiento detrás de una interfaz para migrar a S3 sin cambiar los casos de uso.
- No cargar archivos completos en memoria cuando puedan transmitirse por bloques.

## Estructura esperada

```text
3D-Lab/
├── backend/
│   ├── src/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/
│   └── tests/
├── frontend/
│   └── src/
│       ├── models/
│       ├── viewmodels/
│       ├── views/
│       └── services/
├── docs/
├── specs/
│   └── 001-3d-lab-mvp/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── UI_STYLE_GUIDE.md
└── AGENTS.md
```

## Comandos

Ejecutar instalaciones y creación de entornos solo cuando sean necesarias durante la configuración inicial o cuando cambien las dependencias.

```powershell
python -m venv .venv
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest
ruff check .
ruff format --check .
```

Si el frontend incorpora un gestor de paquetes y existe `package.json`:

```powershell
pnpm install
pnpm dev
pnpm test
```

No ejecutar comandos inexistentes ni inventar rutas: verificar primero la estructura real del repositorio.

## Convenciones de código

- Código simple, mantenible y con nombres descriptivos.
- Funciones pequeñas con una sola responsabilidad.
- Evitar duplicación, lógica muerta y código comentado.
- Separar reglas de dominio de presentación e infraestructura.
- Usar tipos y contratos explícitos.
- Aplicar migraciones para todo cambio de esquema.
- No insertar datos técnicos de materiales sin fuente verificable.
- No copiar código, textos ni recursos de Bambu Lab o Apple.

## Pruebas y criterios de calidad

Cada funcionalidad debe incluir pruebas proporcionales al riesgo.

- Unitarias para dominio y casos de uso.
- Integración para PostgreSQL, almacenamiento, correo y tareas.
- API para autenticación, solicitudes, límites y transiciones de estado.
- Seguridad para autorización, traversal, archivos inválidos y límites de carga.
- UI para estados `loading`, `success`, `empty` y `error`.
- Responsive y accesibilidad para las vistas principales.
- Guía de materiales: filtros, ranking, comparación, detalle, unidades y ausencia de datos.
- Retención: expiración, eliminación física e historial posterior.
- Correos: idempotencia, fallo y reintentos.

Antes de entregar cambios ejecutar, cuando existan las dependencias:

```powershell
pytest
ruff check .
ruff format --check .
```

## Restricciones operativas

- No hacer `commit`, `push`, despliegues ni acciones destructivas sin aprobación explícita.
- No borrar archivos de usuario para resolver conflictos de implementación.
- Preservar cambios existentes que no pertenezcan a la tarea actual.
- No incorporar pagos, suscripciones, IA o integraciones externas al MVP sin actualizar primero la especificación.
