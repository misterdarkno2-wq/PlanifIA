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

## App Android con Tauri 2

La app incluye las mismas pantallas, tareas, planes y Lumi de la web, con navegación inferior y tus assets de marca. FastAPI, MySQL y Ollama siguen en el servidor: la IA utiliza la GPU del PC. El teléfono necesita Internet; esta versión no ofrece edición sin conexión ni notificaciones push.

### Probar el APK

Descarga la aplicación desde [GitHub Releases: Android 1.1.0 de prueba](https://github.com/misterdarkno2-wq/PlanifIA/releases/tag/v1.1.0-android-preview.1).

Instala `PlanifIA-android-arm64.apk` de la carpeta `dist` en un Android 7 o posterior con procesador ARM64. Es una compilación optimizada para pruebas, firmada con la clave de depuración de este equipo. Android puede pedir permiso para instalar desde el navegador o gestor de archivos.

1. Mantén FastAPI, Ollama y el túnel encendidos en el PC.
2. Abre PlanifIA y entra con tu cuenta existente, o regístrate.
3. En **Conexión**, comprueba o cambia la dirección HTTPS si el túnel ha cambiado. Usa solo `https://nombre.trycloudflare.com`, sin `/app` ni `/api`.

La dirección inicial está en `src-tauri/default-server.json`; se puede cambiar después desde la app. Cambiarla cierra la sesión local. El túnel temporal deja de funcionar al detenerlo; para uso permanente necesitas una dirección HTTPS estable.

### Compilar en Windows

Instala [los requisitos oficiales de Tauri](https://v2.tauri.app/start/prerequisites/): Node.js LTS, Rust, Visual Studio Build Tools con C++ y Android Studio. En el SDK Manager de Android instala Platform 36, Build Tools 36, Platform Tools, Command-line Tools y NDK (Side by side). En este equipo se usa NDK `29.0.13846066`.

Desde la raíz del proyecto, en PowerShell:

```powershell
npm.cmd ci
$env:JAVA_HOME = "$env:USERPROFILE\.jdks\jbr-21.0.11"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:NDK_HOME = "$env:ANDROID_HOME\ndk\29.0.13846066"
rustup target add aarch64-linux-android
npm.cmd run android:apk
```

El APK se genera dentro de `src-tauri/gen/android/app/build/outputs/apk/`. El proyecto Android ya está incluido: no necesitas ejecutar `android:init` de nuevo. Usa **JDK 21**: la ruta anterior corresponde a este equipo. En otro equipo puedes instalar Temurin 21 o descargar JDK 21 desde Android Studio y ajustar `JAVA_HOME`. El Java 25 de algunas versiones nuevas de Android Studio no es compatible con el Gradle incluido. Si tu instalación usa otro NDK o SDK, ajusta esas rutas.

Para probar con un móvil conectado por USB (activa Depuración USB y acepta el equipo), o con un emulador abierto en Android Studio:

```powershell
npm.cmd run android:dev
```

Para probar las pantallas como ventana de Windows:

```powershell
npm.cmd run desktop:dev
```

La conexión de la app usa peticiones HTTPS desde Rust y reutiliza las sesiones de FastAPI. La cookie se guarda en el directorio privado de la aplicación; no se expone al JavaScript, no se incluye en copias de seguridad Android y se elimina al salir de la cuenta. El APK contiene solamente el frontend y el cliente nativo; no contiene `.env`, credenciales MySQL ni Ollama. No hay que abrir CORS ni cambiar las protecciones del navegador.

Para publicar en Google Play necesitas una compilación de distribución y tu propia clave de firma: sigue la [guía oficial de Android](https://v2.tauri.app/distribute/google-play/). La clave de depuración sirve para probar. Compilar para iPhone requiere macOS, Xcode y firma de Apple; desde este equipo Windows se prepara Android.

Para reproducir el APK optimizado de prueba, después de haber ejecutado `android:apk` una vez (crea la clave de depuración), usa las mismas variables de entorno anteriores:

```powershell
npm.cmd run tauri -- android build --apk --target aarch64
New-Item -ItemType Directory -Path dist -Force | Out-Null
& "$env:ANDROID_HOME\build-tools\36.0.0\apksigner.bat" sign --ks "$env:USERPROFILE\.android\debug.keystore" --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out dist/PlanifIA-android-arm64.apk src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release-unsigned.apk
& "$env:ANDROID_HOME\build-tools\36.0.0\apksigner.bat" verify dist/PlanifIA-android-arm64.apk
```

La contraseña `android` es la estándar de la clave de depuración; no uses esa clave para publicar. Los APK, las claves y las carpetas de compilación están excluidos de Git.

Se comprobaron registro, acceso, persistencia de sesión, tareas, XP de Lumi y generación/guardado con Ollama en Tauri para Windows, además de la interfaz a 390 y 1440 píxeles. El APK se compiló y su firma se verificó. Falta probarlo en un teléfono Android: el emulador de este PC necesita habilitar la aceleración de virtualización.

```powershell
npm.cmd run test:mobile
cargo test --manifest-path src-tauri/Cargo.toml --lib
```

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
