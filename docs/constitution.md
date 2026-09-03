# Constitución de 3D-Lab

1. **Stack simple:** Solo Python, FastAPI, PostgreSQL y HTML/CSS/JS; cero frameworks duplicados.
2. **Especificación trazable:** Toda funcionalidad debe vincularse con un requisito y criterio de aceptación antes de implementarse.
3. **Separación estricta:** La presentación no contiene reglas de negocio y el dominio no importa frameworks ni infraestructura.
4. **Pruebas obligatorias:** Cada caso de uso incluye al menos una prueba exitosa y una de error; el 100 % debe pasar.
5. **Persistencia segura:** Todo cambio de esquema usa migración; PostgreSQL guarda datos y los STL permanecen privados durante 30 días.
6. **Idioma consistente:** Código e identificadores en inglés; interfaz, errores y mensajes para usuarios en español.
