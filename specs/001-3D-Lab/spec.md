# Especificación 001: MVP de 3D-Lab

## Contexto y objetivo

3D-Lab necesita una plataforma web que explique sus servicios de manufactura aditiva y convierta visitantes en clientes mediante solicitudes de cotización con archivos STL. La primera funcionalidad abarca el MVP completo: catálogo de servicios, guía de materiales, solicitud de cotización, seguimiento administrativo y administración del catálogo de materiales.

El resultado principal de negocio es aumentar las ventas concretadas. Para esta especificación, una venta se considera concretada cuando el administrador registra que el cliente aprobó la cotización y realizó el pago fuera de la plataforma, momento en que la solicitud pasa a `En proceso`.

## Clarifications

### Session 2026-09-02

- Q: ¿Cómo debe manejarse una cotización rechazada, cancelada o cerrada por error? → A: Añadir `Cancelada` como estado terminal; `Cerrada` no se reabre.
- Q: Si una venta pasa a `Cancelada` después de estar `En proceso`, ¿debe seguir contando como venta concretada? → A: Se conserva en el historial, pero deja de contar como venta concretada.
- Q: ¿Cuánto tiempo deben conservarse los datos personales del cliente después de su última solicitud? → A: Sin vencimiento automático.
- Q: Si un STL expira mientras la solicitud sigue activa, ¿cómo debe entregar el cliente una copia nueva? → A: La reposición se gestiona fuera de la plataforma.

## Usuarios

### Visitante

Persona, emprendedor, empresa o institución que consulta los servicios, explora materiales y solicita una cotización sin crear una cuenta.

### Administrador

Único operador autorizado durante el MVP. Revisa solicitudes, consulta clientes y archivos, actualiza estados, administra el catálogo de materiales y registra las ventas concretadas.

## Historias de usuario

### HU-01 — Conocer los servicios

Como visitante, quiero conocer los servicios y capacidades de 3D-Lab para decidir si pueden atender mi proyecto.

Trazabilidad: RF-01, RF-34 y RF-35; CA-01 y CA-22.

### HU-02 — Elegir un material

Como visitante, quiero explorar materiales por aplicación y propiedades, compararlos y revisar sus detalles para identificar alternativas adecuadas antes de cotizar.

Trazabilidad: RF-02 a RF-08 y RF-37; CA-02 a CA-06, CA-28 y CA-29.

### HU-03 — Solicitar una cotización

Como visitante, quiero proporcionar mis datos y cargar uno o varios STL sin registrarme para recibir una evaluación de mi proyecto con la menor fricción posible.

Trazabilidad: RF-09 a RF-18, RF-36 y RF-38; CA-07 a CA-12, CA-23 a CA-25 y CA-31.

### HU-04 — Recibir confirmaciones

Como visitante, quiero recibir un folio y avisos por correo para saber que mi solicitud fue recibida y conocer sus cambios de estado.

Trazabilidad: RF-19 a RF-22 y RF-39; CA-13, CA-14, CA-30 y CA-32.

### HU-05 — Gestionar solicitudes

Como administrador, quiero consultar y actualizar las solicitudes para dar seguimiento desde su recepción hasta la entrega de la pieza.

Trazabilidad: RF-23 a RF-30; CA-15 a CA-18, CA-26 y CA-27.

### HU-06 — Administrar materiales

Como administrador, quiero crear, editar, publicar y retirar materiales para mantener vigente la guía ofrecida a los visitantes.

Trazabilidad: RF-31 y RF-32; CA-19, CA-20 y CA-28.

### HU-07 — Medir resultados

Como responsable del negocio, quiero conocer solicitudes, tiempos y ventas concretadas para evaluar la efectividad comercial de la plataforma.

Trazabilidad: RF-29 y RF-33; CA-18 y CA-21.

## Requisitos funcionales numerados (RF-x)

- **RF-01:** El sistema debe mostrar el catálogo de servicios de impresión 3D, diseño, ingeniería inversa, optimización y asesoría.
- **RF-02:** El sistema debe permitir explorar materiales por aplicación, propiedades, disponibilidad y costo relativo. El costo relativo debe usar los niveles `bajo`, `medio` y `alto`; cada propiedad comparable debe mostrar su valor, unidad y fuente, o indicar `No disponible`.
- **RF-03:** La exploración por aplicación debe explicar los factores relevantes y ordenar primero los materiales que cumplan más criterios seleccionados; en caso de empate, debe priorizar disponibilidad y después menor costo relativo. Cada resultado debe indicar los criterios que justifican su posición.
- **RF-04:** El visitante debe poder aplicar varios filtros, ver cuáles están activos y limpiarlos.
- **RF-05:** El visitante debe poder seleccionar materiales y compararlos lado a lado mediante propiedades y unidades consistentes.
- **RF-06:** Cada material publicado debe tener nombre, descripción, aplicaciones, ventajas, limitaciones, disponibilidad, costo relativo, fuente y fecha de actualización. Colores, acabados y propiedades sin información deben mostrarse como `No disponible`.
- **RF-07:** Las afirmaciones sobre certificaciones o usos regulados deben mostrar evidencia y fecha de vigencia. Si no existe evidencia o su vigencia terminó, el material no debe presentarse como certificado.
- **RF-08:** La selección de material debe poder trasladarse a una nueva solicitud de cotización.
- **RF-09:** El visitante debe poder solicitar una cotización sin crear una cuenta. El nombre es obligatorio y admite entre 2 y 100 caracteres; el correo es obligatorio, admite hasta 254 caracteres y debe tener formato válido; el teléfono es obligatorio y admite entre 10 y 15 dígitos, con un signo `+` inicial opcional.
- **RF-10:** Cada solicitud debe contener al menos un STL válido y aceptar como máximo 20 archivos y 500 MB acumulados.
- **RF-11:** El sistema debe validar cada archivo por separado y conservar los archivos válidos cuando otro archivo del mismo envío sea inválido.
- **RF-12:** El visitante debe poder eliminar o reemplazar un archivo antes de enviar la solicitud.
- **RF-13:** El sistema debe mostrar nombre, tamaño, progreso y resultado de validación de cada archivo.
- **RF-14:** Una solicitud se considera aceptada únicamente después de que el visitante confirma el envío, los datos de contacto son válidos y existe al menos un STL válido. Cada solicitud aceptada debe recibir un folio público único y no predecible.
- **RF-15:** Cuando el correo normalizado ya corresponda a un cliente, el sistema debe asociar la nueva solicitud a su historial sin impedir que actualice nombre o teléfono para ese envío. Dos personas que compartan correo se consideran un mismo cliente, pero cada solicitud conserva los datos introducidos en ese envío.
- **RF-16:** El sistema debe conservar sin vencimiento automático los datos de contacto utilizados en cada solicitud como parte de su historial. El cliente puede solicitar su consulta, corrección o eliminación mediante el canal de contacto publicado; antes de ejecutar el cambio, el administrador debe verificar que la solicitud provenga del correo asociado.
- **RF-17:** Los archivos STL deben eliminarse automáticamente 30 días después de su carga, incluso cuando la solicitud permanezca activa. Si todavía se necesita el archivo, su reposición debe gestionarse fuera de la plataforma.
- **RF-18:** Después de eliminar un STL, el historial debe conservar su nombre, tamaño, fecha de carga y fecha de eliminación, indicando que ya no está disponible y sin ofrecer una carga de reemplazo dentro de la plataforma.
- **RF-19:** Al aceptar una solicitud, el sistema debe mostrar la confirmación definida por 3D-Lab y enviar al cliente un correo con el folio.
- **RF-20:** El sistema debe avisar al administrador cuando se reciba una solicitud nueva.
- **RF-21:** El sistema debe enviar al cliente un aviso cuando cambie el estado de su solicitud.
- **RF-22:** Si falla un correo, la solicitud y el cambio de estado deben conservarse. El correo debe reintentarse hasta tres veces sin duplicados; tras el tercer fallo, debe quedar como `No entregado` y mostrarse al administrador.
- **RF-23:** El administrador debe poder iniciar y cerrar una sesión privada.
- **RF-24:** El administrador debe poder buscar por cliente, correo o folio; filtrar por uno o varios estados y por un intervalo de fechas; combinar criterios; limpiar filtros y recorrer resultados divididos en páginas de hasta 50 solicitudes.
- **RF-25:** El administrador debe poder consultar el detalle de una solicitud, sus datos de contacto, comentarios, archivos disponibles e historial de estados.
- **RF-26:** El administrador debe poder descargar individualmente los STL que todavía no hayan expirado.
- **RF-27:** Las solicitudes deben seguir esta secuencia principal de estados: `Abierta` al recibirse, `Cotización enviada` al enviarse la propuesta, `En proceso` cuando el cliente la aprueba y realiza el pago, y `Cerrada` cuando se entrega la pieza. Desde cualquier estado no terminal, el administrador puede pasar la solicitud a `Cancelada`. Los estados `Cerrada` y `Cancelada` son terminales y no pueden reabrirse ni modificarse.
- **RF-28:** Cada cambio de estado debe conservar el estado anterior, el nuevo estado, la fecha y el administrador responsable.
- **RF-29:** El paso a `En proceso` debe registrar una venta concretada. Si posteriormente la solicitud pasa a `Cancelada`, el evento histórico debe conservarse, pero la solicitud debe dejar de contabilizarse como venta concretada y como conversión efectiva.
- **RF-30:** El administrador debe poder consultar todas las solicitudes asociadas a un cliente, ordenadas de la más reciente a la más antigua, con folio, fecha, estado y disponibilidad de archivos.
- **RF-31:** El administrador debe poder crear, editar, publicar, archivar y ordenar materiales, aplicaciones, propiedades, valores comparables, disponibilidad y evidencia documental. No se puede publicar un material sin los campos obligatorios definidos en RF-06.
- **RF-32:** Un material archivado debe permanecer en solicitudes históricas, pero no debe aparecer como disponible para una solicitud nueva.
- **RF-33:** Para un periodo elegido, el administrador debe poder consultar el total de solicitudes aceptadas, solicitudes que alcanzaron `Cotización enviada`, ventas concretadas no canceladas, tasa de conversión efectiva —ventas concretadas no canceladas divididas entre solicitudes aceptadas— y tiempo promedio transcurrido en cada estado.
- **RF-34:** Las operaciones de consulta, filtrado, envío, carga, descarga, cambio de estado y mantenimiento de materiales deben comunicar si están cargando, terminaron correctamente, no tienen resultados o produjeron un error.
- **RF-35:** Los mensajes mostrados a visitantes y administradores deben estar en español y explicar cómo recuperarse del error cuando exista una acción posible.
- **RF-36:** Si una carga se interrumpe, el sistema debe conservar los archivos que ya terminaron y permitir reintentar únicamente los incompletos. La solicitud no puede enviarse mientras existan cargas pendientes.
- **RF-37:** Si ningún material cumple los filtros, el sistema debe mostrar un resultado vacío y permitir limpiar los filtros. Si un material seleccionado deja de estar publicado antes del envío, debe informar que ya no está disponible y retirar su selección.
- **RF-38:** Mientras se procesa el envío de una solicitud, una segunda activación del control de envío no debe crear otra solicitud. Tras recibir el resultado, un nuevo envío debe requerir una confirmación explícita del visitante.
- **RF-39:** Si el folio generado ya existe, la solicitud no debe confirmarse con ese folio y debe recibir otro folio único antes de completar su aceptación.

## Criterios de aceptación usando EARS

- **CA-01 (RF-01):** Cuando un visitante acceda al catálogo, el sistema deberá mostrar todos los servicios publicados con su descripción y una acción para solicitar cotización.
- **CA-02 (RF-02 a RF-04):** Cuando el visitante seleccione una aplicación o propiedad, el sistema deberá actualizar los materiales recomendados, mostrar disponibilidad, costo relativo y filtros activos, y permitir retirarlos individualmente o en conjunto.
- **CA-03 (RF-03):** Cuando se muestren materiales recomendados, el sistema deberá ordenarlos por cantidad de criterios cumplidos, disponibilidad y costo relativo, e indicar los criterios que justifican la posición de cada uno.
- **CA-04 (RF-05):** Cuando el visitante seleccione dos o más materiales, el sistema deberá presentar sus propiedades comparables con la misma unidad y marcar claramente los datos no disponibles.
- **CA-05 (RF-06 y RF-07):** Cuando el visitante abra una ficha, el sistema deberá mostrar todos los campos obligatorios, marcar como `No disponible` cada dato opcional ausente y omitir cualquier declaración de certificación que no tenga evidencia vigente.
- **CA-06 (RF-08):** Cuando el visitante elija solicitar cotización desde una recomendación o ficha, el sistema deberá abrir la solicitud conservando el material seleccionado.
- **CA-07 (RF-09):** Cuando un visitante capture un nombre de 2 a 100 caracteres, un correo válido de hasta 254 caracteres y un teléfono de 10 a 15 dígitos, el sistema deberá permitir continuar sin solicitar contraseña o registro.
- **CA-08 (RF-10):** Si el visitante intenta agregar un archivo número 21 o superar 500 MB acumulados, el sistema deberá rechazar únicamente la nueva incorporación y explicar el límite aplicable.
- **CA-09 (RF-10 y RF-11):** Si un archivo no es un STL válido, está vacío o está dañado, el sistema deberá marcarlo como inválido y conservar los demás archivos válidos.
- **CA-10 (RF-12 y RF-13):** Mientras la solicitud no haya sido enviada, el visitante deberá poder quitar o reemplazar archivos y ver el estado individual de cada carga.
- **CA-11 (RF-14 a RF-16):** Cuando el visitante confirme el envío con datos válidos y al menos un STL válido, el sistema deberá aceptar la solicitud, generar un folio único, asociarla al historial del correo normalizado y conservar sin vencimiento automático los datos de contacto usados en ese envío. Cuando el cliente solicite consultar, corregir o eliminar sus datos desde el correo asociado, el administrador deberá poder registrar y completar la solicitud.
- **CA-12 (RF-17 y RF-18):** Cuando un STL cumpla 30 días desde su carga, el sistema deberá eliminarlo aunque la solicitud siga activa, conservar sus metadatos con la indicación `Archivo expirado` y no ofrecer una reposición dentro de la plataforma.
- **CA-13 (RF-19 y RF-20):** Cuando una solicitud sea aceptada, el sistema deberá mostrar la confirmación, enviar el folio al cliente y avisar al administrador.
- **CA-14 (RF-21 y RF-22):** Si falla cualquier correo de confirmación, aviso administrativo o cambio de estado, el sistema deberá conservar la operación y reintentar el correo hasta tres veces sin crear duplicados.
- **CA-15 (RF-23):** Si una persona no ha iniciado una sesión administrativa válida, el sistema deberá impedirle consultar solicitudes, clientes, ventas, archivos y materiales no públicos.
- **CA-16 (RF-24, RF-25 y RF-26):** Cuando el administrador consulte una solicitud, el sistema deberá mostrar su información e historial y permitir descargar solamente archivos vigentes.
- **CA-17 (RF-27):** Cuando se reciba una solicitud válida, su estado deberá ser `Abierta`; cuando el administrador registre el envío de la propuesta deberá ser `Cotización enviada`; cuando registre aprobación y pago deberá ser `En proceso`; y cuando registre la entrega de la pieza deberá ser `Cerrada`. Cuando el administrador cancele una solicitud no terminal, deberá pasar a `Cancelada`; si intenta modificar una solicitud `Cerrada` o `Cancelada`, el sistema deberá rechazar el cambio y conservar su estado.
- **CA-18 (RF-28 y RF-29):** Cuando una solicitud pase a `En proceso`, el sistema deberá registrar simultáneamente la venta concretada y el evento de cambio de estado. Si después pasa a `Cancelada`, deberá conservar ambos eventos históricos y excluir la solicitud del total de ventas concretadas y de la conversión efectiva.
- **CA-19 (RF-31):** Cuando el administrador cree, edite, ordene o publique un material con todos los campos obligatorios, el cambio deberá reflejarse en la guía pública y conservar la fecha de modificación. Si falta un campo obligatorio, la publicación deberá rechazarse e indicar cuáles faltan.
- **CA-20 (RF-32):** Cuando un material sea archivado, el sistema deberá retirarlo de nuevas selecciones y conservar su nombre en solicitudes anteriores.
- **CA-21 (RF-33):** Cuando el administrador seleccione un periodo, el sistema deberá calcular las solicitudes aceptadas, las que alcanzaron `Cotización enviada`, las ventas no canceladas, la conversión efectiva y el tiempo promedio por estado, excluyendo solicitudes canceladas de ventas y conversión.
- **CA-22 (RF-34 y RF-35):** Si una consulta, filtro, envío, carga, descarga, cambio de estado o edición de material falla o no devuelve resultados, el sistema deberá mostrar en español el estado correspondiente, un icono, una explicación y una acción de recuperación cuando sea posible.
- **CA-23 (RF-09 y RF-10):** Si falta un dato obligatorio, su formato es inválido o no existe al menos un STL válido, el sistema deberá impedir el envío e identificar cada dato o archivo que requiere atención.
- **CA-24 (RF-36):** Si se interrumpe una carga, el sistema deberá conservar los archivos completados, marcar los incompletos y permitir reintentar solo estos últimos; mientras haya cargas pendientes, deberá impedir el envío.
- **CA-25 (RF-38):** Mientras una solicitud se esté enviando, si el visitante activa nuevamente el control de envío, el sistema deberá conservar una sola solicitud y un solo folio.
- **CA-26 (RF-23):** Cuando el administrador introduzca credenciales válidas, el sistema deberá iniciar la sesión y permitir cerrarla; si son inválidas, deberá rechazar el acceso sin revelar cuál dato falló.
- **CA-27 (RF-24 y RF-30):** Cuando el administrador combine búsqueda, estados e intervalo de fechas, el sistema deberá mostrar únicamente coincidencias en páginas de hasta 50 resultados; al abrir un cliente, deberá ordenar todas sus solicitudes de la más reciente a la más antigua.
- **CA-28 (RF-07 y RF-31):** Cuando venza la evidencia de una certificación o el administrador la retire, el sistema deberá dejar de presentar el material como certificado, conservando el resto de su ficha si continúa publicado.
- **CA-29 (RF-32 y RF-37):** Si no existen coincidencias, el sistema deberá mostrar un estado vacío y permitir limpiar filtros. Si un material seleccionado se archiva antes de enviar la solicitud, deberá retirarlo de la selección e informar al visitante.
- **CA-30 (RF-22):** Si un correo falla tres veces, el sistema deberá marcarlo como `No entregado`, mostrar el fallo al administrador y no realizar un cuarto intento automático.
- **CA-31 (RF-15 y RF-16):** Cuando dos envíos utilicen el mismo correo normalizado, el sistema deberá asociarlos al mismo cliente y conservar por separado los datos de contacto introducidos en cada solicitud.
- **CA-32 (RF-14 y RF-39):** Si un folio generado ya existe, el sistema deberá asignar otro folio antes de confirmar la solicitud y nunca mostrar el folio duplicado al visitante.

## Requisitos no funcionales

- **RNF-01 — Usabilidad:** En una prueba con al menos 12 participantes —tres particulares, tres emprendedores, tres representantes de empresas y tres de instituciones—, al menos 11 deben completar una solicitud válida sin asistencia en un máximo de cinco minutos.
- **RNF-02 — Rendimiento percibido:** Durante cada periodo de 30 días, al menos 95 % de las visitas debe ver el contenido principal de las páginas públicas en menos de dos segundos.
- **RNF-03 — Carga:** El progreso o confirmación inicial de una carga debe aparecer en menos de un segundo después de seleccionar los archivos.
- **RNF-04 — Capacidad:** El servicio debe gestionar al menos 500 solicitudes mensuales manteniendo los objetivos de tiempo definidos en RNF-02 y RNF-03.
- **RNF-05 — Accesibilidad:** Consultar servicios, filtrar y comparar materiales, enviar una solicitud y gestionar cotizaciones debe poder completarse con teclado, foco visible, etiquetas comprensibles y contraste de nivel AA.
- **RNF-06 — Adaptabilidad:** Catálogo, guía, formulario y panel deben ser utilizables en teléfono, tableta y computadora sin pérdida de funciones esenciales.
- **RNF-07 — Privacidad:** Después del envío, los archivos y datos personales solo deben ser accesibles para el administrador; el visitante recibe por correo únicamente el folio y los avisos de estado, sin acceso posterior a un portal.
- **RNF-08 — Integridad:** Una solicitud confirmada no debe perder sus datos o cambiar de estado sin dejar evidencia del evento.
- **RNF-09 — Idioma:** El 100 % de los textos de interfaz, validaciones, correos y errores dirigidos al usuario debe estar en español.
- **RNF-10 — Confiabilidad:** Un fallo de correo no debe provocar pérdida ni duplicación de solicitudes, estados o ventas.

## Casos límite

- El visitante agrega 20 archivos válidos e intenta agregar uno más.
- Un único archivo hace que el total supere 500 MB.
- Entre varios archivos, uno está vacío, corrupto o no es realmente un STL.
- La conexión se interrumpe después de cargar algunos archivos; los completados se conservan y los incompletos pueden reintentarse.
- El visitante intenta enviar dos veces la misma solicitud mientras el primer envío sigue en curso; solo se crea una solicitud.
- Dos personas utilizan el mismo correo electrónico; se consideran un cliente y cada solicitud conserva su propia información de contacto.
- Un cliente existente proporciona un nombre o teléfono diferente en una nueva solicitud.
- Un cliente solicita consultar, corregir o eliminar sus datos personales.
- Un STL expira mientras la solicitud sigue `Abierta`, `Cotización enviada` o `En proceso`; la plataforma conserva el historial y cualquier reposición se gestiona fuera de ella.
- El administrador intenta descargar un archivo expirado.
- Falla el correo de confirmación, el aviso administrativo o la notificación de estado; después de tres intentos queda como `No entregado` y visible para el administrador.
- Un material carece de una propiedad necesaria para la comparación.
- Un material seleccionado se archiva antes de que el visitante envíe su solicitud; se retira de la selección y se informa al visitante.
- No existen materiales que cumplan todos los filtros elegidos; se muestra el estado vacío y la opción de limpiar filtros.
- El administrador intenta omitir un estado o cambiar una solicitud `Cerrada` o `Cancelada`.
- Una solicitud pasa a `En proceso` y posteriormente se cancela o se devuelve el pago; el historial conserva ambos eventos, pero la solicitud deja de contar como venta concretada.
- El visitante intenta enviar una solicitud sin un STL válido; el envío se bloquea y se identifican los archivos pendientes.
- Dos archivos tienen el mismo nombre; ambos conservan una entrada distinguible dentro de la solicitud.
- Vence la evidencia de una certificación publicada; el material deja de mostrarse como certificado.
- Se genera un folio ya utilizado; la solicitud recibe otro antes de confirmarse.

## Fuera de alcance

- Cuentas, inicio de sesión y portal de seguimiento para clientes.
- Pagos, anticipos, reembolsos o suscripciones dentro de la plataforma.
- Integración con CRM, WhatsApp, facturación u otros servicios comerciales.
- Recomendaciones, clasificación o cotizaciones generadas mediante inteligencia artificial.
- Cálculo automático del precio a partir de la geometría del STL.
- Aplicación móvil nativa.
- Idiomas distintos del español.
- Asignación de solicitudes a varios administradores o permisos administrativos diferenciados.
- Garantizar aptitud técnica o regulatoria de un material sin revisión humana.

## Criterios de finalización

- Todos los requisitos funcionales tienen al menos un criterio de aceptación verificable.
- Cada historia de usuario cuenta con una prueba de recorrido exitoso y al menos una prueba de error relevante.
- El 100 % de las pruebas acordadas pasa antes de aceptar la funcionalidad.
- Los límites de 20 archivos, 500 MB y 30 días se verifican tanto en recorridos exitosos como fallidos.
- Se verifica el recorrido completo desde `Abierta` hasta `Cerrada`, la cancelación desde cada estado no terminal y el bloqueo de cambios sobre estados terminales.
- Se verifica el registro de la venta al pasar a `En proceso` y su exclusión de las métricas si después se cancela.
- Se verifica que un fallo de correo no elimine ni duplique la solicitud.
- Se verifica que los STL expirados no puedan descargarse y que su historial permanezca visible.
- La guía permite explorar, filtrar, comparar, abrir fichas y trasladar una selección a la cotización.
- El administrador puede mantener el catálogo sin intervención externa.
- No quedan contradicciones entre historias, requisitos, criterios y casos límite.
- La especificación no contiene dudas abiertas pendientes antes de aprobarse para planificación.

## Dudas abiertas

- Ninguna.
