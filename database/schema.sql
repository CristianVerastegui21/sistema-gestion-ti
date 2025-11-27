-- Versión para MySQL 8.0
CREATE TABLE IF NOT EXISTS categorias_equipos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    vida_util_anos INT DEFAULT 5,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proveedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    razon_social VARCHAR(255) NOT NULL,
    ruc VARCHAR(20) UNIQUE NOT NULL,
    direccion TEXT,
    telefono VARCHAR(50),
    email VARCHAR(100),
    contacto_nombre VARCHAR(100),
    contacto_telefono VARCHAR(50),
    sitio_web VARCHAR(255),
    notas TEXT,
    calificacion DECIMAL(2,1),
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ubicaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    edificio VARCHAR(100),
    aula_oficina VARCHAR(100),
    piso VARCHAR(50),
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(255),
    email VARCHAR(100) UNIQUE,
    rol VARCHAR(50) DEFAULT 'usuario',
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS equipos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_inventario VARCHAR(50) UNIQUE NOT NULL,
    categoria_id INT,
    nombre VARCHAR(255) NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100),
    especificaciones JSON,
    proveedor_id INT,
    fecha_compra DATE,
    costo_compra DECIMAL(10, 2),
    fecha_garantia_fin DATE,
    ubicacion_actual_id INT,
    estado_operativo VARCHAR(50) DEFAULT 'operativo',
    estado_fisico VARCHAR(50) DEFAULT 'bueno',
    asignado_a_id INT,
    notas TEXT,
    imagen_url TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias_equipos(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (ubicacion_actual_id) REFERENCES ubicaciones(id),
    FOREIGN KEY (asignado_a_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS contratos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id INT,
    numero_contrato VARCHAR(50),
    tipo VARCHAR(50),
    fecha_inicio DATE,
    fecha_fin DATE,
    monto_total DECIMAL(12, 2),
    estado VARCHAR(20),
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
);

CREATE TABLE IF NOT EXISTS mantenimientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipo_id INT,
    tipo VARCHAR(50),
    fecha_programada DATE,
    fecha_realizada DATE,
    descripcion TEXT,
    costo DECIMAL(10, 2) DEFAULT 0,
    estado VARCHAR(50) DEFAULT 'programado',
    prioridad VARCHAR(20) DEFAULT 'media',
    tecnico_id INT,
    observaciones TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id),
    FOREIGN KEY (tecnico_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS movimientos_equipos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipo_id INT,
    ubicacion_origen_id INT,
    ubicacion_destino_id INT,
    usuario_responsable_id INT,
    motivo TEXT,
    observaciones TEXT,
    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id),
    FOREIGN KEY (ubicacion_origen_id) REFERENCES ubicaciones(id),
    FOREIGN KEY (ubicacion_destino_id) REFERENCES ubicaciones(id),
    FOREIGN KEY (usuario_responsable_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(50),
    titulo VARCHAR(255),
    mensaje TEXT,
    equipo_id INT,
    mantenimiento_id INT,
    leida BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_lectura TIMESTAMP,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id),
    FOREIGN KEY (mantenimiento_id) REFERENCES mantenimientos(id)
);

-- Datos semilla (Seed Data)
INSERT INTO categorias_equipos (nombre, vida_util_anos) VALUES 
('Laptops', 3), ('PCs Escritorio', 5), ('Servidores', 5), ('Proyectores', 4);

INSERT INTO ubicaciones (edificio, aula_oficina, piso) VALUES 
('Pabellón A', 'Lab 101', '1'), ('Administracion', 'Oficina 202', '2');

INSERT INTO usuarios (nombre_completo, email, rol) VALUES 
('Admin TI', 'admin@universidad.edu', 'admin');