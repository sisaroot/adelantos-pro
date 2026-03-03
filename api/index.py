import os
import sqlite3
try:
    import psycopg2
except ImportError:
    pass # Solo se usa en producción/Nube

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel proveerá la variable DATABASE_URL para Postgres.
DB_URL = os.environ.get('DATABASE_URL')
# Local fallback
LOCAL_DB = 'adelantos.db'

def get_db():
    if DB_URL:
        # En Postgres Vercel usualmente requiere sslmode
        conn = psycopg2.connect(DB_URL)
        return conn, 'postgres'
    else:
        conn = sqlite3.connect(LOCAL_DB)
        return conn, 'sqlite'

def inicializar_db():
    conn, db_type = get_db()
    c = conn.cursor()
    
    if db_type == 'postgres':
        # PostgreSQL syntax
        c.execute('''CREATE TABLE IF NOT EXISTS registros
                     (id SERIAL PRIMARY KEY,
                      ci TEXT, cliente TEXT, dinero_recibido REAL,
                      forma_recepcion TEXT, fecha_recepcion TEXT, referencia TEXT,
                      factura REAL, diferencia REAL, telefono TEXT,
                      moneda TEXT DEFAULT 'USD', estado TEXT DEFAULT 'Pendiente')''')
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                     (id SERIAL PRIMARY KEY,
                      username TEXT UNIQUE, password TEXT, role TEXT)''')
    else:
        # SQLite syntax
        c.execute('''CREATE TABLE IF NOT EXISTS registros
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ci TEXT, cliente TEXT, dinero_recibido REAL,
                      forma_recepcion TEXT, fecha_recepcion TEXT, referencia TEXT,
                      factura REAL, diferencia REAL, telefono TEXT,
                      moneda TEXT DEFAULT 'USD', estado TEXT DEFAULT 'Pendiente')''')
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE, password TEXT, role TEXT)''')
                      
    conn.commit()
    conn.close()

inicializar_db()

class LoginData(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(data: LoginData):
    try:
        conn, db_type = get_db()
        c = conn.cursor()
        
        query = "SELECT role FROM usuarios WHERE username=%s AND password=%s" if db_type == 'postgres' else "SELECT role FROM usuarios WHERE username=? AND password=?"
        c.execute(query, (data.username, data.password))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {"status": "ok", "role": row[0]}
        else:
            return {"status": "error", "msg": "Credenciales inválidas o usuario no existe."}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.post("/api/register")
def registrar_usuario(data: LoginData):
    if not data.username or not data.password:
        return {"status": "error", "msg": "Debes llenar todos los campos."}
        
    try:
        conn, db_type = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM usuarios")
        count_val = c.fetchone()[0]
        role = "admin" if count_val == 0 else "user"
        
        query = "INSERT INTO usuarios (username, password, role) VALUES (%s, %s, %s)" if db_type == 'postgres' else "INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)"
        c.execute(query, (data.username, data.password, role))
        conn.commit()
        conn.close()
        return {"status": "ok", "msg": "Usuario registrado con éxito. Ya puedes iniciar sesión.", "role": role}
    except Exception as e:
        if "UNIQUE constraint" in str(e) or "unique constraint" in str(e).lower():
            return {"status": "error", "msg": "El nombre de usuario ya existe."}
        return {"status": "error", "msg": str(e)}

@app.get("/api/registros")
def obtener_registros():
    try:
        conn, db_type = get_db()
        c = conn.cursor()
        c.execute("SELECT id, ci, cliente, dinero_recibido, forma_recepcion, fecha_recepcion, referencia, factura, diferencia, telefono, moneda, estado FROM registros ORDER BY id DESC")
        filas = c.fetchall()
        conn.close()
        
        registros = []
        for f in filas:
            registros.append({
                "id": f[0], "ci": f[1], "cliente": f[2], "dinero_recibido": f[3],
                "forma_recepcion": f[4], "fecha_recepcion": f[5], "referencia": f[6],
                "factura": f[7], "diferencia": f[8], "telefono": f[9],
                "moneda": f[10], "estado": f[11]
            })
        return {"status": "ok", "data": registros}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.post("/api/registros")
async def guardar_registro(request: Request):
    datos = await request.json()
    try:
        conn, db_type = get_db()
        c = conn.cursor()
        
        query = """
            INSERT INTO registros 
            (ci, cliente, dinero_recibido, forma_recepcion, fecha_recepcion, referencia, factura, diferencia, telefono, moneda, estado) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """ if db_type == 'postgres' else """
            INSERT INTO registros 
            (ci, cliente, dinero_recibido, forma_recepcion, fecha_recepcion, referencia, factura, diferencia, telefono, moneda, estado) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        c.execute(query, (
            datos.get('ci'), datos.get('cliente'), float(datos.get('dinero_recibido', 0)),
            datos.get('forma_recepcion'), datos.get('fecha_recepcion'), datos.get('referencia'),
            float(datos.get('factura', 0)) if datos.get('factura') else 0.0,
            float(datos.get('diferencia', 0)) if datos.get('diferencia') else 0.0,
            datos.get('telefono'), datos.get('moneda', 'USD'), datos.get('estado', 'Pendiente')
        ))
        conn.commit()
        conn.close()
        return {"status": "ok", "msg": "Registro guardado exitosamente"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.put("/api/registros/{id}")
async def actualizar_registro(id: int, request: Request):
    datos = await request.json()
    try:
        conn, db_type = get_db()
        c = conn.cursor()
        
        query = """
            UPDATE registros SET
            ci=%s, cliente=%s, dinero_recibido=%s, forma_recepcion=%s, fecha_recepcion=%s, referencia=%s, factura=%s, diferencia=%s, telefono=%s, moneda=%s, estado=%s
            WHERE id=%s
        """ if db_type == 'postgres' else """
            UPDATE registros SET
            ci=?, cliente=?, dinero_recibido=?, forma_recepcion=?, fecha_recepcion=?, referencia=?, factura=?, diferencia=?, telefono=?, moneda=?, estado=?
            WHERE id=?
        """
        
        c.execute(query, (
            datos.get('ci'), datos.get('cliente'), float(datos.get('dinero_recibido', 0)),
            datos.get('forma_recepcion'), datos.get('fecha_recepcion'), datos.get('referencia'),
            float(datos.get('factura', 0)) if datos.get('factura') else 0.0,
            float(datos.get('diferencia', 0)) if datos.get('diferencia') else 0.0,
            datos.get('telefono'), datos.get('moneda', 'USD'), datos.get('estado', 'Pendiente'), id
        ))
        conn.commit()
        conn.close()
        return {"status": "ok", "msg": "Registro actualizado exitosamente"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.delete("/api/registros/{id}")
def eliminar_registro(id: int):
    try:
        conn, db_type = get_db()
        c = conn.cursor()
        query = "DELETE FROM registros WHERE id=%s" if db_type == 'postgres' else "DELETE FROM registros WHERE id=?"
        c.execute(query, (id,))
        conn.commit()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
