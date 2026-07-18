# Implementation Plan

## Fase 0 - Auditoría y plan

- Inspeccionar repo actual.
- Auditar referencias externas.
- Crear documentación de arquitectura, datos, riesgos y plan.
- Definir estructura final.

## Fase 1 - Fundación

- Crear monorepo `frontend` y `backend`.
- Configurar FastAPI, SQLAlchemy, Alembic, tests, lint y env.
- Configurar Next.js, Tailwind, diseño responsive, navegación y páginas base.
- Health check, errores, logs y README ejecutable.

## Fase 2 - Tracker y banca

- CRUD de banca, eventos, mercados, selecciones, cuotas y apuestas.
- Liquidación de resultados y movimientos de banca.
- Dashboard básico con ROI, yield y drawdown.

## Fase 3 - Motor BetAlpha

- Odds math, vig, EV, Kelly, stake, score, warnings, exposición y correlación.

## Fase 4 - Importación Triunfobet

- Entrada manual móvil, CSV, plantilla, adjuntos y vista de transcripción asistida.

## Fase 5 - Modelos y backtesting

- `BaseSportModel`, baseline sin vig, registro de modelos, backtesting temporal y métricas.

## Fase 6 - Reportes y autopsia

- CLV, ROI avanzado, calibración, postmortems, export CSV y backlog PDF.

## Comandos iniciales

```powershell
npm.cmd create next-app@latest frontend -- --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -e "backend[dev]"
backend\.venv\Scripts\pytest backend\tests
```
