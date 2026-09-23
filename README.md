# PlanifIA

Organizador de tareas, pruebas y horarios de estudio. Backend en FastAPI, base de datos MySQL con PyMySQL y frontend en HTML, CSS y JavaScript. La generación de planes usa Qwen3 en tu equipo mediante Ollama.

## Instalación

Necesitas Python 3.11 o posterior, acceso a una base MySQL y [Ollama para Windows](https://ollama.com/download/windows). Abre Ollama y descarga el modelo una vez:

```powershell
ollama pull qwen3:8b
```

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
OLLAMA_MODEL=qwen3:8b
```

Si usas MySQL remoto, conserva el host, puerto, usuario y nombre de base que te asignaron. La IA local no necesita ninguna API key. `.env` está excluido de Git; no publiques tus credenciales.

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

Registra una cuenta, añade tareas o pruebas y guarda tu disponibilidad en el planificador. Mantén Ollama abierto. FastAPI envía las actividades y horarios a `http://127.0.0.1:11434/api/chat`; Python distribuye las sesiones según vencimientos, prioridad y tiempo disponible. Qwen3 redacta el resumen y los objetivos de estudio en tu equipo. El servidor valida el plan antes de guardarlo en MySQL. La base puede estar en un servidor remoto según tu `.env`.

La integración usa [JSON estructurado](https://docs.ollama.com/capabilities/structured-outputs), un contexto de 16 384 tokens y un límite de 3 minutos por solicitud. Ejecuta `ollama ps` para comprobar el uso de GPU. El modelo se mantiene cargado durante 10 minutos tras usarlo. Consulta la [compatibilidad de GPU](https://docs.ollama.com/gpu) si se carga en CPU.

Los recordatorios se actualizan al abrir el dashboard o las notificaciones. No se envían correos ni avisos con la aplicación cerrada.

## Desarrollo

### Mascota y experiencia

Lumi acompaña al usuario en el dashboard y reacciona al completar tareas. Su progreso se guarda en MySQL. Para actualizar una instalación existente, ejecuta de nuevo `scripts/crear_base.py` y reinicia FastAPI; la migración añade los campos de XP y la tabla `mascotas` sin borrar datos. Requiere permiso `ALTER` sobre `tareas`.

- Prioridad baja: 10 XP; media: 20 XP; alta: 35 XP.
- Completar antes del día de entrega suma 5 XP. El mismo día o después entrega la XP base.
- Reabrir o eliminar una tarea retira su recompensa. Volver a completarla recupera exactamente el primer importe; editar la prioridad después no lo aumenta.
- Las tareas antiguas o creadas directamente como completadas no reciben XP retroactiva.
- Cada nivel requiere `50 + 15 × (nivel actual − 1)` XP. Hay 20 niveles y evoluciones en los niveles 1, 5, 10, 15 y 20. Al retirar XP, el nivel y la etapa se ajustan al saldo.

Los valores están en `backend/pet_config.py`. La actualización de tarea, recompensa y mascota comparte una transacción y bloqueos de filas. El nivel y la etapa se calculan desde el saldo persistido para evitar datos contradictorios.

### Archivos y pruebas

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

Las pruebas de integración usan el MySQL del `.env` y eliminan sus propios usuarios temporales al finalizar. Las pruebas de Ollama simulan respuestas. Con PlanifIA y Ollama iniciados, comprueba la generación real, el guardado y el historial con actividades ficticias:

```powershell
.\.venv\Scripts\python.exe scripts\probar_ollama_real.py
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
- **Ollama no conecta:** abre Ollama en el mismo equipo donde ejecutas FastAPI.
- **Modelo no instalado:** ejecuta `ollama pull qwen3:8b` o descarga el modelo que hayas definido en `OLLAMA_MODEL`.
- **Generación lenta:** comprueba `ollama ps` y cierra programas que ocupen la GPU. Una respuesta incompleta o un plan inválido no se guardan.

El servidor está configurado para uso local. Para desplegarlo necesitas HTTPS, `COOKIE_SECURE=true`, un `APP_ORIGIN` correcto y límites de solicitudes compartidos entre procesos.
