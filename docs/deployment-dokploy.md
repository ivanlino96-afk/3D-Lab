# Despliegue de 3D-Lab en Dokploy

## 1. Configuración de compilación

En la aplicación de Dokploy selecciona el proveedor `Dockerfile` y configura:

- Contexto de construcción: `/`
- Ruta del Dockerfile: `/Dockerfile`
- Puerto interno: `8000`
- Réplicas: `1`

La imagen ejecuta las migraciones pendientes antes de iniciar FastAPI. Si una migración falla, la aplicación no inicia y evita operar con un esquema incompleto.

## 2. Variables de entorno

Configura en la aplicación, no en el servicio PostgreSQL:

```env
APP_ENV=production
PORT=8000
DATABASE_URL=postgresql+psycopg://USUARIO:CONTRASEÑA@HOST_INTERNO:5432/BASE
PRIVATE_STORAGE_ROOT=/data/stl
APP_SECRET_KEY=VALOR_ALEATORIO_DE_AL_MENOS_32_CARACTERES
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=HASH_PBKDF2
ADMIN_EMAIL=correo-administrativo@example.com
SMTP_HOST=servidor-smtp
SMTP_PORT=587
SMTP_USERNAME=usuario-smtp
SMTP_PASSWORD=contraseña-smtp
SMTP_FROM=3D-Lab <cotizaciones@example.com>
```

No pegues estas credenciales en el repositorio. Para generar `APP_SECRET_KEY`:

```console
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Para generar `ADMIN_PASSWORD_HASH`, ejecuta desde `backend` en un equipo confiable:

```console
python -c "from getpass import getpass; from src.administration.infrastructure.auth import PasswordHasher; print(PasswordHasher().hash(getpass('Contraseña administrativa: ')))"
```

El comando solicita la contraseña sin guardarla en el historial de la terminal. Copia únicamente el hash resultante a Dokploy.

## 3. Almacenamiento persistente

En `Advanced → Volumes` agrega un volumen persistente:

- Nombre sugerido: `3dlab-stl`
- Ruta de montaje en el contenedor: `/data/stl`

No montes este volumen dentro de `/app/frontend` ni lo expongas como almacenamiento público. Los STL deben sobrevivir un redespliegue y solo pueden descargarse mediante una sesión administrativa válida.

## 4. Dominio y despliegue

Asigna el dominio de la aplicación al puerto `8000`, activa HTTPS y despliega. El contenedor debe aparecer como saludable después de aplicar las migraciones y poder consultar PostgreSQL.

Revisa los logs si el despliegue falla. Los errores más comunes son una `DATABASE_URL` incorrecta, contraseña con caracteres sin codificar o falta de conectividad entre la aplicación y PostgreSQL.

## 5. Trabajos periódicos

El proceso web no envía la cola de correos ni elimina por sí solo los STL vencidos. Configura un trabajo programado en Dokploy cada cinco minutos usando la misma imagen y variables:

```console
python -m src.worker
```

Este comando procesa correos pendientes y elimina archivos cuya retención de 30 días terminó. Configura respaldos de PostgreSQL y del volumen privado antes de recibir solicitudes reales.
