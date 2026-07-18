# Despliegue en GitHub y Vercel

Este proyecto queda preparado para Vercel gratis en un solo repo:

- Next.js vive en la raiz del proyecto.
- FastAPI vive en `backend/`.
- Vercel expone FastAPI mediante `api/index.py`.
- El frontend llama al backend por `/api/v1` cuando esta publicado.

## Subir a GitHub

```powershell
cd C:\Proyectos\apuesta
git init
git add .
git commit -m "Initial BetAlpha MVP"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

Si el repo ya existe, usa solo:

```powershell
cd C:\Proyectos\apuesta
git add .
git commit -m "Prepare Vercel deployment"
git push
```

## Configurar Vercel

1. Importa el repo desde GitHub.
2. En Vercel, deja **Root Directory** vacio o en `.`.
3. No uses `frontend` como carpeta raiz.
4. No uses el JSON de `services`.
5. Vercel leera `vercel.json` desde la raiz.

Valores esperados:

```text
Framework Preset: Next.js
Install Command: npm install && python -m pip install -r requirements.txt
Build Command: npm run build
Output Directory: .next
```

## Variables de entorno

En Vercel agrega:

```env
THE_ODDS_API_KEY=tu_api_key
```

Opcional:

```env
NEXT_PUBLIC_API_BASE_URL=/api/v1
```

Puedes omitir `NEXT_PUBLIC_API_BASE_URL` porque la app ya usa `/api/v1` automaticamente cuando no esta en localhost.

## Base de datos

Sin configurar nada mas, Vercel usara SQLite temporal en `/tmp`. Esto sirve para probar gratis, pero no es persistente: Vercel puede borrar esos datos cuando reinicia la funcion.

Para produccion real, lo recomendable es usar una base Postgres gratuita como Supabase o Neon y poner en Vercel:

```env
BETALPHA_DATABASE_URL=postgresql+psycopg://usuario:password@host:5432/database
```

## Probar despues del deploy

Cuando Vercel termine, abre:

```text
https://tu-app.vercel.app/api/v1/dashboard
```

Debe responder JSON. Si eso funciona, la app ya puede leer datos reales desde el backend integrado.

## No Subir Secretos

Estos archivos/carpetas ya estan ignorados:

- `.env`
- `.env.*`
- `node_modules/`
- `.next/`
- `*.db`
- `*.sqlite`
- `.venv/`
