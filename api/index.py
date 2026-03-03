import os
import sqlite3
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Habilitar CORS para permitir llamadas si se separa el frontend del backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# En Vercel, el sistema de archivos es de solo lectura excepto /tmp.
DB_PATH = '/tmp/adelantos.db' if os.environ.get('VERCEL') else 'adelantos.db'

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
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  role TEXT)''')
    conn.commit()
    conn.close()

inicializar_db()

class LoginData(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(data: LoginData):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT role FROM usuarios WHERE username=? AND password=?", (data.username, data.password))
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
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM usuarios")
        count = c.fetchone()[0]
        role = "admin" if count == 0 else "user"
        
        c.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)", (data.username, data.password, role))
        conn.commit()
        conn.close()
        return {"status": "ok", "msg": "Usuario registrado con éxito. Ya puedes iniciar sesión.", "role": role}
    except sqlite3.IntegrityError:
        return {"status": "error", "msg": "El nombre de usuario ya existe."}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.get("/api/registros")
def obtener_registros():
    try:
        conn = sqlite3.connect(DB_PATH)
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
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO registros 
            (ci, cliente, dinero_recibido, forma_recepcion, fecha_recepcion, referencia, factura, diferencia, telefono, moneda, estado) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
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
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE registros SET
            ci=?, cliente=?, dinero_recibido=?, forma_recepcion=?, fecha_recepcion=?, referencia=?, factura=?, diferencia=?, telefono=?, moneda=?, estado=?
            WHERE id=?
        """, (
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
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM registros WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
