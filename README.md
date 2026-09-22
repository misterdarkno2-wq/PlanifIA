# PlanifIA

Aplicación escolar para organizar tareas y pruebas, recibir recordatorios y generar planes de estudio con OpenAI. Usa FastAPI, PyMySQL y MySQL; el frontend se abre desde el servidor.

## Si ya tienes `.env` configurado

Abre PowerShell en esta carpeta y ejecuta estos comandos en orden:

```powershell
.\.venv\Scripts\python.exe scripts\crear_base.py
.\.venv\Scripts\python.exe scripts\iniciar_local.py
```

El primer comando crea las tablas que faltan en **la base indicada por `DB_NAME`** usando tus credenciales actuales. Puedes repetirlo: conserva las tablas y los datos existentes. Necesitas permisos para crear tablas en esa base. No hace falta activar el entorno virtual ni cambiar la política de ejecución de PowerShell.

Abre [PlanifIA](http://127.0.0.1:8000) y registra tu cuenta. Si el servidor ya estaba iniciado, detenlo con Ctrl+C antes de volver a arrancarlo para cargar los cambios.

## Primera ejecución en Windows

Necesitas Python 3.11 o posterior, acceso a una base MySQL y una clave de la API de OpenAI para generar planes. Puedes usar un servidor remoto con las credenciales que te hayan asignado. Si prefieres instalarlo en tu equipo, usa el [MSI de MySQL Community Server 8.4 para Windows](https://dev.mysql.com/downloads/mysql/8.4.html) y configúralo con MySQL Configurator siguiendo el [manual de MySQL](https://dev.mysql.com/doc/refman/8.4/en/windows-choosing-package.html).

Si todavía no tienes el proyecto, descárgalo con Git:

```powershell
git clone https://github.com/misterdarkno2-wq/PlanifIA.git
cd PlanifIA
```

El repositorio incluye `.env.example` como plantilla. Tu `.env` con las credenciales reales se configura únicamente en tu equipo y queda excluido de Git.

Abre **PowerShell en la carpeta `planifia`**. Ejecuta este bloque; conserva los archivos `.venv` y `.env` si ya existen:

```powershell
if (!(Test-Path .venv\Scripts\python.exe)) { py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

En el Bloc de notas, completa `.env` con los datos reales de tu servidor. Si ya están configurados, consérvalos. Este ejemplo corresponde a una instalación local:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=planifia_app
DB_PASSWORD=contraseña_del_usuario_mysql
DB_NAME=planifia
OPENAI_API_KEY=tu_clave_de_openai
OPENAI_MODEL=gpt-4o-mini
```

Para un servidor remoto, usa su host, puerto, nombre de base, usuario y contraseña. `DB_NAME` puede ser el nombre que te asignaron: no tiene que llamarse `planifia`. Obtén la clave en [OpenAI Platform](https://platform.openai.com/api-keys). La contraseña de MySQL y la clave de OpenAI son credenciales distintas.

Crea las tablas de la aplicación en tu base:

```powershell
.\.venv\Scripts\python.exe scripts\crear_base.py
```

El script usa `.env` directamente. No cambia el usuario ni la contraseña, y no borra datos. Si tienes tablas de otra aplicación, se conservan. Las tablas de PlanifIA que ya existan deben tener la estructura de `database/planifia.sql`.

Si tu base aún no existe y tu usuario tiene permiso para crear bases, ejecuta en su lugar:

```powershell
.\.venv\Scripts\python.exe scripts\crear_base.py --crear-base
```

Arranca la aplicación:

```powershell
.\.venv\Scripts\python.exe scripts\iniciar_local.py
```

Mantén esa ventana abierta y visita **http://127.0.0.1:8000**. Registra una cuenta, crea una tarea o prueba y entra en **Planificador IA** para generar un plan. Ctrl+C detiene el servidor. Los HTML no funcionan abiertos con doble clic.

## Las siguientes veces

Con MySQL iniciado, desde la carpeta del proyecto ejecuta:

```powershell
.\iniciar.cmd
```

La clave de OpenAI se vuelve a leer al generar un plan, así que puedes corregirla en `.env` sin reiniciar FastAPI.

## Generar y comprobar un plan

En **Planificador IA**, guarda tus días, horario y minutos disponibles. Pulsa **Generar plan**, revisa el resultado y después **Guardar este plan**. La llamada a OpenAI puede consumir cuota de tu cuenta. El backend envía actividades y disponibilidad, sin nombre, correo ni contraseña; valida el resultado antes de guardarlo en MySQL. Usa la [API Responses con salida estructurada](https://developers.openai.com/api/docs/guides/structured-outputs).

Para hacer una prueba real con datos ficticios, una vez que MySQL funcione y `OPENAI_API_KEY` esté configurada, ejecuta:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\probar_openai_real.py
```

El script solo crea `docs/PRUEBA_OPENAI_REAL.md` si la generación, el guardado y la recuperación pasan. El usuario temporal se elimina al finalizar.

## Cómo funciona PyMySQL

`backend/database.py` abre una conexión con `DictCursor`. El administrador de contexto `transaction()` abre y cierra el cursor, confirma con `commit()` si todo salió bien, hace `rollback()` ante un error y siempre cierra la conexión con `finally`. `query()` obtiene filas y `execute()` ejecuta escrituras.

Los valores se pasan aparte con `%s`, incluso los IDs y el usuario autenticado:

```python
query('SELECT * FROM tareas WHERE usuario_id=%s', (usuario['id'],))
```

No se concatenan entradas del navegador en SQL. Editar, completar y eliminar verifican tanto el ID del recurso como `usuario_id`. Las operaciones relacionadas usan una transacción. Las claves foráneas eliminan los registros dependientes si se elimina un usuario.

## Sesiones y validación

Las contraseñas se guardan como hash Argon2id. La sesión es un token aleatorio de 32 bytes: el navegador conserva una cookie HttpOnly/SameSite=Strict; MySQL guarda solamente su SHA-256 y vencimiento de 7 días. Cerrar sesión elimina la sesión del servidor. La cuenta nunca se elige mediante un `usuario_id` enviado por el frontend.

La API valida entradas con Pydantic y el navegador aplica campos obligatorios y límites. Las peticiones que modifican datos exigen una cabecera propia y comprueban Origin cuando está presente. El backend limita intentos de registro/login por IP (20 por minuto, por proceso). Las claves quedan en `.env`, excluido de Git. El contenido del usuario y de la IA se escapa antes de renderizarse.

La configuración entregada es para demostración local. Si se publica en Internet se necesita HTTPS, `COOKIE_SECURE=true`, un `APP_ORIGIN` correcto y un despliegue administrado con límites compartidos entre procesos. No se incluye ese despliegue en Sprint 1.

## Recordatorios internos

`notification_service.py` revisa las tareas pendientes, las pruebas próximas y las sesiones del último plan guardado. Crea avisos para hoy, mañana, dentro de 2 días y tareas atrasadas. Usa la zona `America/Santiago`, configurable con `APP_TIMEZONE`. Las tareas son de fecha completa, sin hora exacta de entrega; lo mismo aplica a pruebas en Sprint 1.

El cálculo ocurre al consultar el dashboard o las notificaciones. El navegador consulta cada minuto mientras está visible; al volver a entrar se generan los avisos correspondientes. No hay SMS, correo, push ni un proceso que despierte con la aplicación cerrada. Los avisos quedan en MySQL, con clave única por usuario/evento/día. Leerlos mantiene su estado; editar, completar o eliminar una actividad invalida sus recordatorios anteriores. Los planes guardados no se reescriben cuando cambia una actividad: genera otro plan si cambian tus pendientes.

## Tablas

| Tabla | Contenido |
|---|---|
| usuarios | Nombre, correo único y hash de contraseña |
| sesiones | Hash del token, usuario y vencimiento |
| tareas | Entrega, prioridad, dificultad, minutos y estado |
| evaluaciones | Fecha, asignatura, prioridad, dificultad y preparación |
| disponibilidad | Una configuración JSON por usuario |
| planes_estudio | Respuesta validada, modelo, fecha y estado de guardado |
| notificaciones | Mensaje, tipo, fecha, clave única y estado de lectura |

Todas las tablas dependientes tienen clave foránea al usuario con ON DELETE CASCADE. El SQL completo está en [database/planifia.sql](database/planifia.sql).

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\comprobar_reinicio.py
```

Las pruebas de integración utilizan MySQL real del `.env` y crean usuarios temporales con correos únicos, que eliminan al terminar. No borran la base ni los datos de otros usuarios. `test_openai.py` verifica el contrato y fallos HTTP inducidos de manera aislada; no es evidencia de una respuesta de OpenAI. El script de reinicio levanta un servidor temporal, persiste datos, lo detiene, lo inicia de nuevo y comprueba la sesión y las filas.

La documentación interactiva de los endpoints está disponible en **http://127.0.0.1:8000/docs** mientras el servidor está iniciado.

## Si algo falla

- **MySQL no disponible:** revisa que esté iniciado y que coincidan host, puerto, usuario y contraseña. `/api/health` comprueba una consulta real con PyMySQL.
- **Cada petición tarda varios segundos:** si la dirección IPv6 de tu servidor no responde, añade `DB_IPV4=true` a `.env` y reinicia la aplicación. La conexión resolverá el mismo host mediante IPv4.
- **Faltan tablas / error 1146:** ejecuta `scripts/crear_base.py` con el Python del entorno virtual. La conexión puede funcionar aunque la base todavía no tenga las tablas de PlanifIA.
- **401 en `/api/auth/me`:** es normal antes de iniciar sesión. Registra una cuenta o ingresa con una existente.
- **Correo repetido:** usa otro correo o inicia sesión con la cuenta existente.
- **Sesión vencida:** vuelve a iniciar sesión.
- **Datos inválidos:** completa campos obligatorios, usa una fecha real y horarios coherentes. Se permiten fechas pasadas para registrar tareas atrasadas.
- **OpenAI sin clave o con clave rechazada:** corrige `.env` y revisa permisos del modelo.
- **OpenAI sin cuota, timeout o respuesta inválida:** la disponibilidad permanece guardada y puedes intentar de nuevo. La API no guarda respuestas inválidas como planes.
- **403 al guardar:** abre la URL configurada en APP_ORIGIN; las llamadas manuales requieren `X-Planifia-Request: 1`.

## Alcance

Sprint 1 incluye cuentas, tareas, pruebas, dashboard, disponibilidad, recordatorios internos y planificación OpenAI con historial. No se implementaron Classroom, Moodle, chat, pagos, aplicación móvil ni otras funciones de Sprint 2. La generación real de planes requiere una clave OpenAI válida y una llamada exitosa al servicio.
