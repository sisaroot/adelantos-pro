import eel
import sqlite3
import os
import sys

# Support PyInstaller executable path
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, 'adelantos.db')

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                  estado TEXT DEFAULT 'Pendiente')''')
    
    # Try to add 'moneda' to existing table if it doesn't exist
    try:
        c.execute("ALTER TABLE registros ADD COLUMN moneda TEXT DEFAULT 'USD'")
        print("Migración: Columna 'moneda' agregada.")
    except sqlite3.OperationalError:
        pass # Column already exists

    # Try to add 'estado' to existing table if it doesn't exist
    try:
        c.execute("ALTER TABLE registros ADD COLUMN estado TEXT DEFAULT 'Pendiente'")
        print("Migración: Columna 'estado' agregada.")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  role TEXT)''')
    
    conn.commit()
    conn.close()

# Start DB
inicializar_db()

# Expose web folder
eel.init('web')

@eel.expose
def login(username, password):
    """Database login verification"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT role FROM usuarios WHERE username=? AND password=?", (username, password))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {"status": "ok", "role": row[0]}
        else:
            return {"status": "error", "msg": "Credenciales inválidas o usuario no existe."}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@eel.expose
def registrar_usuario(username, password):
    """Registers a new user"""
    if not username or not password:
        return {"status": "error", "msg": "Debes llenar todos los campos."}
        
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if it's the first user (make them admin)
        c.execute("SELECT COUNT(*) FROM usuarios")
        count = c.fetchone()[0]
        role = "admin" if count == 0 else "user"
        
        c.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        
        return {"status": "ok", "msg": "Usuario registrado con éxito. Ya puedes iniciar sesión.", "role": role}
    except sqlite3.IntegrityError:
        return {"status": "error", "msg": "El nombre de usuario ya existe."}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@eel.expose
def guardar_registro(datos):
    """Saves a new record to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO registros 
            (ci, cliente, dinero_recibido, forma_recepcion, fecha_recepcion, referencia, factura, diferencia, telefono, moneda, estado) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos['ci'],
            datos['cliente'],
            float(datos['dinero_recibido']),
            datos['forma_recepcion'],
            datos['fecha_recepcion'],
            datos['referencia'],
            float(datos['factura']) if datos['factura'] else 0.0,
            float(datos['diferencia']) if datos['diferencia'] else 0.0,
            datos['telefono'],
            datos.get('moneda', 'USD'),
            datos.get('estado', 'Pendiente')
        ))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "msg": "Registro guardado exitosamente."}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@eel.expose
def actualizar_registro(datos):
    """Updates an existing record in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            UPDATE registros SET
            ci=?, cliente=?, dinero_recibido=?, forma_recepcion=?, fecha_recepcion=?, referencia=?, factura=?, diferencia=?, telefono=?, moneda=?, estado=?
            WHERE id=?
        """, (
            datos['ci'],
            datos['cliente'],
            float(datos['dinero_recibido']),
            datos['forma_recepcion'],
            datos['fecha_recepcion'],
            datos['referencia'],
            float(datos['factura']) if datos['factura'] else 0.0,
            float(datos['diferencia']) if datos['diferencia'] else 0.0,
            datos['telefono'],
            datos.get('moneda', 'USD'),
            datos.get('estado', 'Pendiente'),
            int(datos['id'])
        ))
        
        conn.commit()
        conn.close()
        return {"status": "ok", "msg": "Registro actualizado exitosamente."}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@eel.expose
def obtener_registros():
    """Returns all records, most recent first."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, ci, cliente, dinero_recibido, forma_recepcion, fecha_recepcion, referencia, factura, diferencia, telefono, moneda, estado FROM registros ORDER BY id DESC")
        filas = c.fetchall()
        conn.close()
        
        registros = []
        for f in filas:
            registros.append({
                "id": f[0],
                "ci": f[1],
                "cliente": f[2],
                "dinero_recibido": f[3],
                "forma_recepcion": f[4],
                "fecha_recepcion": f[5],
                "referencia": f[6],
                "factura": f[7],
                "diferencia": f[8],
                "telefono": f[9],
                "moneda": f[10] if len(f) > 10 else 'USD',
                "estado": f[11] if len(f) > 11 else 'Pendiente'
            })
        return {"status": "ok", "data": registros}
    except Exception as e:
         return {"status": "error", "msg": str(e)}

@eel.expose
def eliminar_registro(id_db):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM registros WHERE id=?", (id_db,))
        conn.commit()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# Start App
eel.start('index.html', size=(1400, 850), port=0)
