fn main() {
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(
        tauri_build::AppManifest::new().commands(&["api_request", "get_server", "set_server"]),
    ))
    .expect("No se pudo preparar Tauri");
}
