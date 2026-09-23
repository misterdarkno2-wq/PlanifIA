use reqwest::{header, Client, Method, Url};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{fs, path::PathBuf, time::Duration};
use tauri::{Manager, State};
use tokio::sync::Mutex;

#[derive(Clone, Deserialize, Serialize)]
struct Connection {
    server: String,
    #[serde(default)]
    session: String,
}

struct Backend {
    client: Client,
    connection: Mutex<Connection>,
    file: PathBuf,
}

#[derive(Serialize)]
struct ApiResponse {
    status: u16,
    data: Value,
}

fn server_url(input: &str) -> Result<String, String> {
    let url = Url::parse(input.trim()).map_err(|_| "Escribe una dirección HTTPS válida.")?;
    if url.scheme() != "https"
        || url.host_str().is_none()
        || !url.username().is_empty()
        || url.password().is_some()
        || url.query().is_some()
        || url.fragment().is_some()
        || url.path() != "/"
    {
        return Err("Usa solo la dirección HTTPS del servidor, sin /app ni contraseñas.".into());
    }
    Ok(url.as_str().trim_end_matches('/').to_owned())
}

fn api_path(path: &str) -> bool {
    path.starts_with('/')
        && path.len() < 512
        && !path.contains("..")
        && path
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '/' || c == '_' || c == '-')
        && !path.starts_with("//")
}

impl Backend {
    fn save(&self, connection: &Connection) -> Result<(), String> {
        let bytes = serde_json::to_vec(connection).map_err(|_| "No se pudo guardar la sesión.")?;
        let temporary = self.file.with_extension("tmp");
        fs::write(&temporary, bytes)
            .map_err(|_| "No se pudo guardar la sesión en este dispositivo.")?;
        fs::rename(temporary, &self.file)
            .map_err(|_| "No se pudo actualizar la sesión.".to_string())
    }
}

#[tauri::command]
async fn get_server(backend: State<'_, Backend>) -> Result<String, String> {
    Ok(backend.connection.lock().await.server.clone())
}

#[tauri::command]
async fn set_server(server: String, backend: State<'_, Backend>) -> Result<(), String> {
    let server = server_url(&server)?;
    let health = backend
        .client
        .get(format!("{server}/api/health"))
        .timeout(Duration::from_secs(15))
        .send()
        .await
        .map_err(|_| {
            "No se pudo conectar. Revisa la dirección y que tu servidor siga encendido."
        })?;
    if !health.status().is_success() {
        return Err("El servidor no está listo. Revisa FastAPI y la conexión con MySQL.".into());
    }
    let data: Value = health
        .json()
        .await
        .map_err(|_| "Esta dirección no responde como PlanifIA.")?;
    if data.get("estado").and_then(Value::as_str) != Some("ok")
        || data.get("conexion").and_then(Value::as_str) != Some("PyMySQL")
    {
        return Err("Esta dirección no responde como PlanifIA.".into());
    }
    let mut connection = backend.connection.lock().await;
    if connection.server != server {
        let next = Connection {
            server,
            session: String::new(),
        };
        backend.save(&next)?;
        *connection = next;
    }
    Ok(())
}

#[tauri::command]
async fn api_request(
    path: String,
    method: String,
    body: Option<Value>,
    backend: State<'_, Backend>,
) -> Result<ApiResponse, String> {
    if !api_path(&path) || !matches!(method.as_str(), "GET" | "POST" | "PUT" | "PATCH" | "DELETE") {
        return Err("Solicitud no válida.".into());
    }
    // La cookie permanece en el almacenamiento privado de la app, fuera del JavaScript.
    let connection = backend.connection.lock().await.clone();
    let mut request = backend
        .client
        .request(
            Method::from_bytes(method.as_bytes()).unwrap(),
            format!("{}/api{path}", connection.server),
        )
        .header("X-Planifia-Request", "1");
    if !connection.session.is_empty() {
        request = request.header(
            header::COOKIE,
            format!("planifia_session={}", connection.session),
        );
    }
    if let Some(body) = body {
        request = request.json(&body);
    }
    let response = request.send().await.map_err(|error| {
        if error.is_timeout() {
            "El servidor tardó demasiado. Comprueba el estado antes de volver a intentarlo."
                .to_string()
        } else {
            "No pudimos conectar. Revisa tu conexión y la dirección del servidor en Conexión."
                .to_string()
        }
    })?;
    let status = response.status().as_u16();
    if (300..400).contains(&status) {
        return Err("El servidor cambió de dirección. Actualízala en Conexión.".into());
    }
    let mut next = connection.clone();
    if path == "/auth/login" && status == 200 {
        next.session = response
            .headers()
            .get_all(header::SET_COOKIE)
            .iter()
            .filter_map(|h| h.to_str().ok())
            .filter_map(|h| h.split(';').next()?.strip_prefix("planifia_session="))
            .find(|token| {
                !token.is_empty()
                    && token
                        .chars()
                        .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_')
            })
            .ok_or("El servidor no entregó una sesión válida.")?
            .to_owned();
    }
    if (path == "/auth/logout" && status == 204) || status == 401 {
        next.session.clear();
    }
    let data = if status == 204 {
        Value::Null
    } else {
        response.json().await.map_err(|_| {
            "El servidor devolvió una respuesta inesperada. Revisa la dirección en Conexión."
        })?
    };
    let mut current = backend.connection.lock().await;
    if current.server != connection.server || current.session != connection.session {
        return Err("Tu conexión o sesión cambió. Vuelve a abrir esta pantalla.".into());
    }
    if next.session != current.session {
        backend.save(&next)?;
        *current = next;
    }
    Ok(ApiResponse { status, data })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let directory = app.path().app_data_dir()?;
            fs::create_dir_all(&directory)?;
            let file = directory.join("connection.json");
            let mut connection: Connection = if file.exists() {
                serde_json::from_slice(&fs::read(&file)?)?
            } else {
                serde_json::from_str(include_str!("../default-server.json"))?
            };
            connection.server = server_url(&connection.server).map_err(std::io::Error::other)?;
            let client = Client::builder()
                .https_only(true)
                .redirect(reqwest::redirect::Policy::none())
                .connect_timeout(Duration::from_secs(15))
                .timeout(Duration::from_secs(200))
                .build()?;
            app.manage(Backend {
                client,
                connection: Mutex::new(connection),
                file,
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            api_request,
            get_server,
            set_server
        ])
        .run(tauri::generate_context!())
        .expect("No se pudo iniciar PlanifIA");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validates_server_without_embedded_credentials_or_paths() {
        assert_eq!(
            server_url(" https://example.com/ ").unwrap(),
            "https://example.com"
        );
        for invalid in [
            "http://example.com",
            "https://user:secret@example.com",
            "https://example.com/app",
            "https://example.com?x=1",
            "https://example.com/#token",
            "file:///etc/passwd",
        ] {
            assert!(server_url(invalid).is_err());
        }
    }

    #[test]
    fn restricts_requests_to_api_paths() {
        for path in ["/auth/login", "/tareas/12/estado", "/planificacion/generar"] {
            assert!(api_path(path));
        }
        for path in [
            "//evil.com",
            "https://evil.com",
            "/../auth",
            "/%2e%2e/",
            "/auth?url=x",
            "/auth\\login",
            "/auth\r\nCookie:x",
        ] {
            assert!(!api_path(path));
        }
    }
}
