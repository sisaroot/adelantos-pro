# Guía de Despliegue en Vercel (Migración a la Nube)

Actualmente, **Adelantos Pro** es una excelente aplicación de escritorio impulsada por **Python, Eel y SQLite**. Funciona de manera brillante en Windows, abriendo su propia ventana con la velocidad y seguridad de tener la base de datos local `adelantos.db`.

Sin embargo, **Vercel** es una plataforma de la nube (Cloud) pensada para páginas web, aplicaciones en JavaScript (Next.js, React) o Funciones "Serverless" rápidas, no para aplicaciones de escritorio.

Para subir este proyecto a GitHub y posteriormente a Vercel para que tu equipo pueda conectarse desde sus propios teléfonos o computadoras a través de internet, se necesita hacer una pequeña migración arquitectónica. Aquí tienes los pasos a seguir.

## El Problema con la Arquitectura Actual en Vercel
1. **Eel no se ejecuta en Vercel:** Eel fue diseñado para abrir una pestaña de Chrome localmente y comunicarse mediante WebSockets en tu PC. Vercel no soporta procesos largos de WebSockets nativamente ni aplicaciones con interfaz (GUI) propia.
2. **SQLite es efímero en Vercel:** Vercel borra todo el sistema de archivos entre ejecuciones (son servidores "sin estado"). Eso significa que cualquier registro guardado en `adelantos.db` se perdería casi al instante tras guardarlo.

## ¿Cómo Prepararlo para Vercel? (Paso a Paso)

Para lograr tu objetivo final en Vercel, debes transformar esta aplicación de escritorio en una **Aplicación Web con una API REST y una Base de Datos en la Nube**.

### 1. La Base de Datos (Cloud PostgreSQL)
No puedes usar SQLite. Deberás cambiar a un servicio de base de datos gratuito en la nube:
- Ve a **Supabase** o **Vercel Postgres**.
- Crea tu base de datos y un proyecto.
- Copia la URL de tu base de datos (Ej: `postgresql://user:pass@host/db`).
- Modifica el script de base de datos en Python usando una librería como `psycopg2` o `SQLAlchemy` para conectarte a esa URL en lugar de `adelantos.db`.

### 2. El Backend (De Eel a FastAPI/Flask)
Debes remover Eel. 
- Crea una carpeta llamada `api` en la raíz del proyecto.
- Mueve tu lógica de Python allá y conviértela en una API Rest (idealmente usando **FastAPI** o **Flask**).
- Por ejemplo, en vez de usar `@eel.expose`, crearías un endpoint `@app.route('/api/login', methods=['POST'])`.
- Vercel soporta nativamente funciones Serverless de Python en la carpeta `/api`. Necesitarás un archivo `requirements.txt` con las dependencias (ej: flask, psycopg2-binary).

### 3. El Frontend (Javascript Fetch)
La carpeta `web/` está casi lista para Vercel. Solo hay un cambio que debes hacer:
- Eliminar de `index.html` la importación `<script type="text/javascript" src="/eel.js"></script>`.
- En `app.js`, cambiar todas las llamadas de Eel como:
  ```javascript
  const res = await eel.obtener_registros()();
  ```
  Sustituirlas por llamadas web (Fetch/Axios) dirigidas a tu nueva API:
  ```javascript
  const request = await fetch('/api/registros');
  const res = await request.json();
  ```

### 4. Vercel.json (Opcional pero Recomendado)
Debes crear en la raíz un archivo `vercel.json` para decirle a Vercel dónde están las funciones de Python y cómo dirigir el tráfico de la web.

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index.py" }
  ]
}
```

## Resumen
¡Ya tienes todo el diseño, la lógica y las funcionalidades base completas y perfeccionadas! Tu equipo puede correrlo en tu máquina o instalarlo (el `.exe`) localmente en la oficina para que haya un equipo designado. Si en el futuro quieres verdaderamente alojarlo en internet en un dominio para acceso remoto, solo pide a Antigravity: *"Por favor adapta el backend a FastAPI y la base de datos a Supabase para subir a Vercel"*, y te guiaré durante toda esa migración con mucho gusto.
