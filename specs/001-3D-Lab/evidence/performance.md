# Evidencia de capacidad y rendimiento

Fecha: 2026-09-03. Entorno: Windows local, Python 3.14, SQLite aislado y navegador integrado.

| Objetivo | Evidencia automatizada | Resultado |
|---|---|---|
| RNF-02, contenido público en menos de 2 s | 40 solicitudes HTTP; percentil 95 calculado y limitado a 2 s | Aprobado |
| RNF-03, respuesta inicial de carga en menos de 1 s | Primer bloque de un STL de más de 3 MB; límite de 1 MiB por bloque | Aprobado |
| RNF-04, 500 solicitudes mensuales | 500 registros consultados; 10 páginas de 50 y consulta limitada a 2 s | Aprobado |
| RF-24, máximo 50 por página | Se solicita tamaño 500 y el caso de uso devuelve 50 | Aprobado |

Comando reproducible: `python -m pytest backend/tests/performance/test_capacity.py -q`.

Esta evidencia valida capacidad funcional y presupuesto de tiempo en un equipo local. La telemetría del percentil 95 durante periodos reales de 30 días debe habilitarse al desplegar; no se presenta este ensayo local como medición de producción.
