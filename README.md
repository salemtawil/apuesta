# BetAlpha Manager

Aplicación privada para registrar apuestas deportivas, estimar valor esperado, administrar banca y revisar resultados. Es una herramienta de apoyo a decisiones: no promete ganancias, no ejecuta apuestas y no solicita credenciales de Triunfobet.

## Estado

MVP en construcción. La Fase 0 está documentada y la Fase 1 tiene base backend/frontend.

## Estructura

```text
backend/      FastAPI, servicios de cálculo, tests y migraciones
frontend/     Next.js App Router
docs/         auditoría, arquitectura, datos, riesgos y ADRs
supabase/     borradores RLS
templates/    plantilla CSV Triunfobet
```

## Backend local

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000/docs

## Frontend local

```powershell
cd frontend
copy .env.example .env.local
npm.cmd install
npm.cmd run dev
```

Frontend: http://localhost:3000

Nota Windows: si el proyecto está dentro de OneDrive y `npm install` se queda extrayendo `next` o `@next/swc-win32-x64-msvc`, moverlo a una ruta local como `C:\Proyectos\apuesta` evita el bloqueo.

## Docker

```powershell
docker compose up --build
```

## Variables

Copiar `backend/.env.example` a `backend/.env`. No guardar secretos reales en el repositorio.

Para sincronizar odds reales desde The Odds API:

```env
THE_ODDS_API_KEY=tu_api_key
```

## CSV Triunfobet

Plantilla: `templates/triunfobet_import_template.csv`.

## API MVP

- `GET /api/v1/sports`
- `POST /api/v1/bankrolls`
- `POST /api/v1/bankroll-transactions`
- `GET /api/v1/bankroll-transactions`
- `GET /api/v1/bankroll-control`
- `POST /api/v1/sportsbooks`
- `POST /api/v1/events`
- `POST /api/v1/markets`
- `GET /api/v1/markets`
- `POST /api/v1/odds`
- `POST /api/v1/intelligence/team-stats`
- `GET /api/v1/intelligence/team-stats`
- `POST /api/v1/intelligence/injuries`
- `GET /api/v1/intelligence/injuries`
- `POST /api/v1/intelligence/market-movements`
- `GET /api/v1/intelligence/market-movements`
- `POST /api/v1/intelligence/analyze`
- `GET /api/v1/intelligence/analyses`
- `POST /api/v1/intelligence/providers`
- `GET /api/v1/intelligence/providers`
- `POST /api/v1/intelligence/sync/odds`
- `GET /api/v1/intelligence/sync/jobs`
- `GET /api/v1/intelligence/predictions`
- `PATCH /api/v1/intelligence/predictions/{prediction_id}`
- `POST /api/v1/intelligence/backtests/run`
- `GET /api/v1/intelligence/backtests`
- `POST /api/v1/assessments/stored`
- `POST /api/v1/bets`
- `GET /api/v1/bets`
- `GET /api/v1/bets/{bet_id}`
- `POST /api/v1/bets/{bet_id}/settle`
- `POST /api/v1/postmortems`
- `GET /api/v1/dashboard`
- `GET /api/v1/analytics/summary`
- `GET /api/v1/exports/bets.csv`
- `POST /api/v1/imports/csv/stored`
- `GET /api/v1/imports/rows`
- `PATCH /api/v1/imports/rows/{row_id}`
- `POST /api/v1/imports/rows/{row_id}/confirm`

## Guías rápidas

Para añadir un deporte: crear catálogo en `sports`, definir mercados soportados y agregar reglas de settlement/correlación si el deporte lo requiere.

Para añadir un modelo: implementar una clase con `fit`, `predict_proba`, `backtest`, `calibrate`, `explain`, `serialize` y `load`; registrar versión y guardar predicciones con fuente explícita.
