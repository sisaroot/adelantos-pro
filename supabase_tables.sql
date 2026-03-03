-- Ejecuta esto en el editor SQL de Supabase para inicializar las tablas

CREATE TABLE IF NOT EXISTS registros (
    id SERIAL PRIMARY KEY,
    ci TEXT,
    cliente TEXT,
    dinero_recibido REAL,
    forma_recepcion TEXT,
    fecha_recepcion TEXT,
    referencia TEXT,
    factura REAL,
    diferencia REAL,
    telefono TEXT,
    moneda TEXT DEFAULT 'USD',
    estado TEXT DEFAULT 'Pendiente'
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
);
