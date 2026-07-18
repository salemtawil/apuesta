# Implementation Status

## Fase 0

Estado: completada inicialmente.

- Repositorio actual inspeccionado: vacío, sin Git.
- Referencias externas auditadas con licencias y riesgos.
- Arquitectura, modelo de datos, plan y riesgos documentados.

## Fase 1

Estado: completada para la base MVP.

- Frontend Next.js generado.
- Pantalla inicial del frontend reemplazada por dashboard operativo.
- Backend FastAPI creado con endpoints de salud, odds, assessments, tickets, settlement, CSV y adjuntos.
- Servicios críticos de odds, BetAlpha Score, correlación y settlement implementados.
- Persistencia SQLAlchemy conectada para deportes, sportsbooks, bancas, eventos, mercados, cuotas, assessments, apuestas, liquidación, imports, adjuntos y postmortems.
- Migración Alembic inicial ampliada al esquema MVP y validada con `python -m alembic upgrade head`.
- Base de datos local, migraciones y flujo inicial validados.
- Tests backend: `python -m pytest` ejecutado, 12 passed.
- Ruff backend: `python -m ruff check .` ejecutado correctamente.
- Import de API backend: `python -c "import fastapi, app.main"` ejecutado correctamente.
- Frontend build: verificado en `C:\Proyectos\apuesta\frontend`.
- Frontend checks: `npm.cmd install --no-audit --no-fund`, `npm.cmd run build` y `npm.cmd run lint` ejecutados correctamente.

## Fase 2

Estado: en progreso.

- Flujo API end-to-end cubierto por test: banca -> evento -> mercado -> cuota -> assessment -> apuesta -> liquidación -> postmortem -> dashboard.
- Frontend conectado a API real con `NEXT_PUBLIC_API_BASE_URL` y cliente `fetch`.
- Dashboard carga `/dashboard`, `/sports`, `/sportsbooks`, `/bankrolls`, `/events` y `/bets`.
- UI permite crear flujo MVP y liquidar apuestas abiertas.
- UI ampliada con formularios manuales para banca, sportsbook, evento, mercado, cuota, assessment, apuesta y autopsia.
- UI permite importar CSV y subir capturas usando endpoints multipart.
- Backend agrega `GET /api/v1/markets` para alimentar selects de mercado/selección.
- Backend agrega `import_rows`, migración `0002_import_rows`, parsing CSV por fila y confirmación humana.
- UI muestra filas importadas, estado, errores y botón para confirmar filas pendientes.
- UI permite editar campos clave de filas importadas antes de confirmarlas.
- Confirmar una fila importada crea evento, mercado, selección y snapshot de cuota con fuente `csv`.
- Backend agrega `PATCH /api/v1/imports/rows/{row_id}` para corregir imports inválidos o pendientes.
- Backend agrega `GET /api/v1/analytics/summary` con buckets por estado y tipo de apuesta.
- Backend agrega `GET /api/v1/exports/bets.csv` para exportar apuestas registradas.
- UI agrega panel de analytics operativo y enlace de exportación CSV.
- Backend agrega filtros en `GET /api/v1/bets` por estado, tipo, banca, sportsbook y fechas.
- Backend agrega `GET /api/v1/bets/{bet_id}` con detalle de legs, evento, mercado, banca, sportsbook y autopsias.
- UI agrega filtros operativos para apuestas y panel de detalle de ticket.
- Backend agrega movimientos manuales de banca: depositos, retiros y ajustes.
- Backend agrega `GET /api/v1/bankroll-control` con historial, exposicion por sportsbook y alertas de riesgo.
- UI agrega panel de banca con formulario de movimiento, alertas, exposicion por casa e historial.
- Backend agrega capa de inteligencia deportiva: snapshots estadisticos, lesiones, movimiento de mercado y analisis explicable.
- Migracion `0003_sports_intelligence` agrega tablas para estadisticas, lesiones, mercado y analisis.
- UI agrega seccion Inteligencia para sincronizar odds reales, generar analisis, ver probabilidades, fair odds, edge, factores y riesgos.
- Migracion `0004_prediction_pipeline` agrega proveedores, sync jobs, tracking de predicciones y backtests.
- Backend agrega endpoints de proveedores, sincronizacion de odds, predicciones evaluables y backtesting/calibracion.
- UI agrega tracking de predicciones, botones de evaluacion y panel de calibracion/backtesting.
- Backend agrega conector real de The Odds API para sincronizar deportes, eventos, sportsbooks, mercados y cuotas actuales.
- UI agrega boton `Sync odds reales` con resumen de eventos, cuotas y requests restantes.
- UI visible limpiada para operar solo con acciones reales; los controles de seed/sync de prueba ya no aparecen.
- Servidores locales validados: FastAPI `http://127.0.0.1:8000`, Next `http://localhost:3000`.
- Browser integrado validado contra `http://localhost:3000`: render de secciones y botón Sincronizar sin errores.
- Browser integrado validado para bandeja de importación: fila CSV confirmada visible.
- Pendiente: filtros analíticos avanzados, OCR real para capturas y tests E2E Playwright.
