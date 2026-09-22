# PlanifIA

Organizador de tareas, pruebas y horarios de estudio. Backend en FastAPI, base de datos MySQL con PyMySQL y frontend en HTML, CSS y JavaScript. La generación de planes usa OpenAI.

## Instalación

Necesitas Python 3.11 o posterior y acceso a una base MySQL.

```powershell
git clone https://github.com/misterdarkno2-wq/PlanifIA.git
cd PlanifIA
```

Desde la carpeta del proyecto:

```powershell
if (!(Test-Path .venv\Scripts\python.exe)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Completa `.env` con tus credenciales. Ejemplo para MySQL local:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=planifia_app
DB_PASSWORD=tu_contraseña
DB_NAME=planifia
OPENAI_API_KEY=tu_clave
OPENAI_MODEL=gpt-4o-mini
```

Si usas MySQL remoto, conserva el host, puerto, usuario y nombre de base que te asignaron. La clave de OpenAI solo es necesaria para generar planes. `.env` está excluido de Git; no publiques tus credenciales.

Crea las tablas:

```powershell
.\.venv\Scripts\python.exe scripts\crear_base.py
```

El script usa la base indicada por `DB_NAME` y crea las tablas que faltan sin borrar las existentes. El usuario necesita permisos para crear tablas. Si la base todavía no existe y tienes permiso para crearla, añade `--crear-base`.

## Ejecutar

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Abre [PlanifIA](http://127.0.0.1:8000). Mantén la terminal abierta; Ctrl+C detiene el servidor. No necesitas activar el entorno virtual. Reinicia el servidor después de cambiar `.env`.

Registra una cuenta, añade tareas o pruebas y guarda tu disponibilidad en el planificador. Al generar un plan se envían a OpenAI las actividades y los horarios, sin correo ni contraseña. El servidor valida el resultado antes de guardarlo. La llamada puede consumir cuota de tu cuenta.

Los recordatorios se actualizan al abrir el dashboard o las notificaciones. No se envían correos ni avisos con la aplicación cerrada.

## Desarrollo

- `backend/`: API, sesiones, consultas y planificación.
- `frontend/`: páginas, estilos y JavaScript.
- `database/planifia.sql`: estructura de las tablas.
- `scripts/`: preparación de la base y comprobaciones de integración.
- `tests/`: pruebas automatizadas.

Documentación de la API: [localhost:8000/docs](http://127.0.0.1:8000/docs).

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas de integración usan el MySQL del `.env` y eliminan sus propios usuarios temporales al finalizar. Las pruebas de OpenAI simulan respuestas. Para comprobar la generación real con actividades ficticias y consumir cuota de la API:

```powershell
.\.venv\Scripts\python.exe scripts\probar_openai_real.py
```

Para comprobar que los datos y la sesión persisten después de reiniciar:

```powershell
.\.venv\Scripts\python.exe scripts\comprobar_reinicio.py
```

## Problemas frecuentes

- **MySQL no conecta:** revisa las credenciales, el puerto y los permisos. `/api/health` comprueba la conexión y las tablas.
- **Faltan tablas / error 1146:** ejecuta `scripts/crear_base.py` con el Python de `.venv`.
- **Conexión lenta por IPv6:** añade `DB_IPV4=true` a `.env` si el servidor solo responde correctamente por IPv4.
- **401 en `/api/auth/me`:** es normal antes de iniciar sesión.
- **403 al guardar:** abre la dirección definida en `APP_ORIGIN`. Las llamadas manuales requieren la cabecera `X-Planifia-Request: 1`.
- **Error al generar:** revisa `OPENAI_API_KEY`, el acceso a `OPENAI_MODEL` y la cuota. Un plan inválido no se guarda.

El servidor está configurado para uso local. Para desplegarlo necesitas HTTPS, `COOKIE_SECURE=true`, un `APP_ORIGIN` correcto y límites de solicitudes compartidos entre procesos.
