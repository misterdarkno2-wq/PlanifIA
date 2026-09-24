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

## Encender el servidor de planifia.cl en este PC

La web está en [planifia.cl](https://planifia.cl) y el servidor en `https://api.planifia.cl`. Cloudflare conecta esa dirección fija con el puerto 8001 de este equipo. Al reiniciar no necesitas volver a configurar DNS ni crear otro túnel.

1. Abre **Ollama** desde Inicio. Si ya aparece junto al reloj, déjalo abierto.
2. Abre PowerShell y ejecuta:

```powershell
cd C:\Users\Admin\Downloads\planifia
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --env-file .env.public
```

3. Abre **otra terminal de PowerShell** y ejecuta:

```powershell
& "$env:LOCALAPPDATA\PlanifIA\cloudflared.exe" tunnel --config "$env:USERPROFILE\.cloudflared\planifia.yml" run planifia
```

4. Abre [PlanifIA](https://planifia.cl). Puedes comprobar el servidor en [api.planifia.cl/api/health](https://api.planifia.cl/api/health): debe responder con `estado: ok`.

Mantén ambas terminales abiertas y el PC conectado a Internet, sin suspender. Ctrl+C detiene cada proceso. Con el PC apagado las pantallas siguen alojadas en GitHub Pages, pero las cuentas, tareas y la IA necesitan el servidor encendido. Estos pasos son manuales; no hay un servicio de inicio automático instalado.

El archivo local `.env.public` ya está preparado en este equipo y contiene:

```dotenv
APP_ORIGIN=https://api.planifia.cl
COOKIE_SECURE=true
WEB_ORIGINS=https://planifia.cl,https://www.planifia.cl,https://misterdarkno2-wq.github.io
```

Las credenciales MySQL siguen en `.env`. Las credenciales y la configuración del túnel están en `%USERPROFILE%\.cloudflared`, fuera del repositorio. Conserva esos archivos en este equipo y no publiques sus claves. En otro PC debes volver a autorizar y configurar el túnel.

Si aparece **puerto 8001 ocupado**, ya hay un servidor usando ese puerto: comprueba `/api/health` antes de abrir otra instancia. No ejecutes `tunnel --url`: eso crea una dirección temporal distinta.

### Configuración del dominio

- NIC Chile delega el DNS a `kaiser.ns.cloudflare.com` y `sloan.ns.cloudflare.com`.
- Cloudflare tiene cuatro registros A para `@`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153` y `185.199.111.153`, con estado **Solo DNS**.
- `www` es un CNAME a `misterdarkno2-wq.github.io`, con estado **Solo DNS**.
- `api` apunta al túnel de Cloudflare llamado `planifia`, que dirige las solicitudes a `http://127.0.0.1:8001`.
- El dominio personalizado de GitHub Pages es `planifia.cl`. La variable `PLANIFIA_API_URL` del repositorio debe ser `https://api.planifia.cl`.

Tras cambiar DNS por primera vez, la propagación y la emisión de los certificados HTTPS pueden tardar. No es necesario repetir esos cambios cada vez que enciendes el PC.

## Web en GitHub Pages

Abre [PlanifIA](https://planifia.cl). Pages publica las pantallas; las cuentas, tareas, Lumi y los planes se procesan en FastAPI y se guardan en MySQL. Ollama sigue usando la GPU del PC. Mantén el servidor y el túnel encendidos.

El despliegue se actualiza al subir cambios del frontend a `main`. La variable del repositorio **PLANIFIA_API_URL** contiene `https://api.planifia.cl`. La web usa esa dirección fija e ignora las direcciones temporales guardadas por versiones anteriores.

El servidor autoriza exclusivamente los orígenes indicados en `.env`:

```dotenv
WEB_ORIGINS=https://planifia.cl,https://www.planifia.cl,https://misterdarkno2-wq.github.io
```

Reinicia FastAPI después de modificarlo. Pages utiliza una sesión por pestaña que sobrevive a la recarga; al cerrar sesión se revoca en el servidor. No requiere cookies de terceros. La web servida por FastAPI y la app Android conservan sus sesiones habituales. El despliegue incluye solo los archivos de `frontend`; no publica `.env`, MySQL, claves ni archivos de compilación de Android.

## App Android con Tauri 2

La app incluye las mismas pantallas, tareas, planes y Lumi de la web, con navegación inferior y tus assets de marca. FastAPI, MySQL y Ollama siguen en el servidor: la IA utiliza la GPU del PC. El teléfono necesita Internet; esta versión no ofrece edición sin conexión ni notificaciones push.

### Probar el APK

Descarga la aplicación desde [GitHub Releases: Android 1.2.0 de prueba](https://github.com/misterdarkno2-wq/PlanifIA/releases/tag/v1.2.0-android-preview.1).

Instala `PlanifIA-android-arm64.apk` de la carpeta `dist` en un Android 7 o posterior con procesador ARM64. Es una compilación optimizada para pruebas, firmada con la clave de depuración de este equipo. Android puede pedir permiso para instalar desde el navegador o gestor de archivos.

1. Mantén FastAPI, Ollama y el túnel encendidos en el PC.
2. Abre PlanifIA y entra con tu cuenta existente, o regístrate.
3. La app se conecta automáticamente a `https://api.planifia.cl`. No necesitas configurar ninguna dirección.

Al actualizar desde un APK con un túnel temporal, la app migra al dominio fijo y pide iniciar sesión de nuevo. Si ya usaba el dominio actual, conserva la sesión. El túnel `planifia` mantiene la misma dirección al reiniciarlo. El icono utiliza el símbolo proporcionado con margen, guardado en `src-tauri/app-icon.png`.

### Avisos en la bandeja de Android

Con el APK **1.2.0** o posterior, abre **Notificaciones → Activar avisos** y acepta el permiso de Android. Pulsa **Probar aviso** y deja la app en segundo plano: se programa una notificación para unos 10 segundos después.

- Entregas pendientes y pruebas: a las 09:00 del día anterior y del mismo día, según `APP_TIMEZONE` (por defecto, Chile).
- Sesiones del último plan guardado: 10 minutos antes. Si faltan menos de 10 minutos, se avisa al comenzar. Los descansos y actividades eliminadas o completadas se omiten.
- Se programan hasta 64 avisos de los próximos 30 días. Abre la app periódicamente para renovar la lista. Puedes sincronizarla manualmente desde Notificaciones.
- Al editar, completar o eliminar actividades en este teléfono se actualizan los avisos. Al cerrar sesión o desactivarlos se cancelan. Cada cuenta activa sus propios avisos.
- Los avisos ya sincronizados funcionan sin conexión, con la app cerrada y tras reiniciar Android. Los cambios hechos desde la web u otro dispositivo se sincronizan al abrir la app. Esto no usa notificaciones push desde un servidor.
- Android puede retrasar los avisos por ahorro de batería o No molestar. **Forzar detención** los bloquea hasta volver a abrir la app. Si denegaste el permiso, actívalo en **Ajustes → Aplicaciones → PlanifIA → Notificaciones**.

Reinicia FastAPI tras actualizar el código para habilitar `/api/notificaciones/programadas`. No requiere tablas nuevas. El PC y el túnel deben estar encendidos para sincronizar; después Android conserva los avisos programados. Los horarios y límites están en `backend/services/mobile_reminders.py`.

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

El contrato de los avisos guardados se comprueba además con la implementación Android del complemento:

```powershell
cd src-tauri\gen\android
.\gradlew.bat :app:testUniversalReleaseUnitTest -x :app:rustBuildUniversalRelease
cd ..\..\..
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
