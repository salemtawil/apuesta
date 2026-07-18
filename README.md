# BetAlpha Manager

Herramienta privada para analizar cartelera deportiva, comparar cuotas reales, registrar apuestas, controlar banca y revisar resultados. Es apoyo a decisiones: no promete ganancias, no ejecuta apuestas y no solicita credenciales de casas de apuestas.

## Estructura

```text
./                 Next.js App Router listo para Vercel
backend/           FastAPI, sync de odds, modelos, tests y migraciones
docs/              arquitectura, auditoria, riesgos y notas tecnicas
supabase/          borradores RLS
templates/         plantilla CSV
```

## Frontend local

```powershell
cd C:\Proyectos\apuesta
copy .env.example .env.local
npm.cmd install
npm.cmd run dev
```

Frontend: http://localhost:3000

## Backend local

```powershell
cd C:\Proyectos\apuesta\backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000/docs

## Variables

Frontend:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Backend:

```env
THE_ODDS_API_KEY=tu_api_key
```

No subas secretos reales al repositorio.

## Vercel

El frontend ya esta en la raiz. Vercel debe usar:

```json
{
  "installCommand": "npm install",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs"
}
```

En Vercel agrega `NEXT_PUBLIC_API_BASE_URL` con la URL publica del backend, terminando en `/api/v1`.

El backend FastAPI se publica aparte, por ejemplo en Render, Railway, Fly.io, VPS o Docker.

## Validacion

```powershell
npm.cmd run lint
npm.cmd run build
```
