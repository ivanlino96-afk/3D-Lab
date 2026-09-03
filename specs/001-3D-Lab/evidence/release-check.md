# Puerta de calidad del MVP

Fecha: 2026-09-03. Estado: **NO LISTO PARA LIBERAR**.

| Control | Resultado | Evidencia |
|---|---|---|
| Pruebas automatizadas | Aprobado | 118/118 con `python -m pytest backend/tests -q` |
| Lint | Aprobado | `ruff check backend`: sin hallazgos |
| Formato | Aprobado | `ruff format --check backend`: 153 archivos formateados |
| Dependencias del dominio | Aprobado | Pruebas de arquitectura incluidas en el conjunto |
| Secretos conocidos | Aprobado | Sin coincidencias para claves privadas, tokens OpenAI/GitHub o claves AWS; `.env.example` solo contiene marcadores |
| Migraciones PostgreSQL | Parcial | La cadena 0001→0005 compila completa en modo SQL; falta ejecutarla desde cero sobre PostgreSQL real |
| Privacidad | Aprobado | Acceso anónimo, sesión falsa/vencida/revocada, STL expirado e identificador desconocido rechazados |
| Capacidad local | Aprobado | Página pública, bloques de carga y 500 solicitudes dentro de los presupuestos; ver `performance.md` |
| Responsive y teclado | Aprobado | Navegador real a 390, 768 y 1440 px, sin desbordamiento ni navegación oculta; controles visibles alcanzables por teclado |
| Usabilidad RNF-01 | Pendiente | Faltan 12 participantes reales; ver `usability.md` |
| Extensiones Spec Kit | No aplica | `.specify/extensions.yml` no existe |

## Bloqueos de liberación

1. T044: ejecutar la integración de ciclo de cotización sobre PostgreSQL y almacenamiento privado de prueba.
2. T081: obtener doce pruebas auténticas y comprobar que al menos once finalizan sin ayuda en cinco minutos.

T083 permanecerá abierta hasta que ambos bloqueos estén resueltos y se repita esta puerta con resultado completamente aprobado.
