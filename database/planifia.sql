-- MySQL 8.0.16 o superior. Ejecutar en la base configurada en DB_NAME.
-- Crea únicamente las tablas que faltan y conserva las tablas y datos existentes.

CREATE TABLE IF NOT EXISTS usuarios (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 nombre VARCHAR(80) NOT NULL,
 correo VARCHAR(254) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sesiones (
 token_hash CHAR(64) PRIMARY KEY,
 usuario_id BIGINT UNSIGNED NOT NULL,
 expira DATETIME NOT NULL,
 FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
 INDEX idx_sesion_usuario (usuario_id), INDEX idx_sesion_expira (expira)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tareas (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 usuario_id BIGINT UNSIGNED NOT NULL,
 titulo VARCHAR(120) NOT NULL,
 descripcion TEXT NOT NULL,
 asignatura VARCHAR(80) NOT NULL,
 fecha_entrega DATE NOT NULL,
 prioridad ENUM('baja','media','alta') NOT NULL DEFAULT 'media',
 dificultad TINYINT NOT NULL CHECK (dificultad BETWEEN 1 AND 5),
 tiempo_estimado INT NOT NULL CHECK (tiempo_estimado BETWEEN 15 AND 6000),
 estado ENUM('pendiente','completada') NOT NULL DEFAULT 'pendiente',
 fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
 INDEX idx_tareas_usuario_estado_fecha (usuario_id, estado, fecha_entrega)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS evaluaciones (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 usuario_id BIGINT UNSIGNED NOT NULL,
 nombre VARCHAR(120) NOT NULL,
 asignatura VARCHAR(80) NOT NULL,
 fecha DATE NOT NULL,
 prioridad ENUM('baja','media','alta') NOT NULL DEFAULT 'media',
 dificultad TINYINT NOT NULL CHECK (dificultad BETWEEN 1 AND 5),
 descripcion TEXT NOT NULL,
 tiempo_estimado INT NOT NULL DEFAULT 120 CHECK (tiempo_estimado BETWEEN 15 AND 6000),
 FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
 INDEX idx_evaluaciones_usuario_fecha (usuario_id, fecha)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS disponibilidad (
 usuario_id BIGINT UNSIGNED PRIMARY KEY,
 datos JSON NOT NULL,
 actualizada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS planes_estudio (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 usuario_id BIGINT UNSIGNED NOT NULL,
 contenido JSON NOT NULL,
 modelo VARCHAR(160) NOT NULL,
 guardado BOOLEAN NOT NULL DEFAULT FALSE,
 fecha_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
 INDEX idx_planes_usuario_guardado (usuario_id, guardado, fecha_generacion)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notificaciones (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 usuario_id BIGINT UNSIGNED NOT NULL,
 clave VARCHAR(160) NOT NULL,
 titulo VARCHAR(150) NOT NULL,
 mensaje TEXT NOT NULL,
 tipo ENUM('tarea','evaluacion','plan') NOT NULL,
 fecha_programada DATETIME NOT NULL,
 leida BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
 UNIQUE KEY uq_notificacion (usuario_id, clave),
 INDEX idx_notificacion_usuario_fecha (usuario_id, fecha_programada, leida)
) ENGINE=InnoDB;
