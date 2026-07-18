# Despliegue en GitHub y Vercel

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

## Frontend en Vercel

1. Importa el repositorio desde GitHub.
2. Vercel usara `vercel.json` para construir Next.js desde la raiz del repo.
3. Agrega esta variable en Vercel:

```env
NEXT_PUBLIC_API_BASE_URL=https://tu-backend.com/api/v1
```

## Backend

Vercel despliega la app Next.js que ahora esta en la raiz. El backend FastAPI debe estar publicado aparte, por ejemplo en Render, Railway, Fly.io, VPS o Docker.

Cuando tengas la URL publica del backend, actualiza `NEXT_PUBLIC_API_BASE_URL` en Vercel.

## No subir secretos

Estos archivos/carpetas ya estan ignorados:

- `.env`
- `.env.*`
- `node_modules/`
- `.next/`
- `*.db`
- `*.sqlite`
- `.venv/`
