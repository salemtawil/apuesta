# Changelog

## 0.1.0 - En progreso

- Inicia BetAlpha Manager.
- Agrega auditoría open source y documentación de arquitectura.
- Agrega backend FastAPI y frontend Next.js como base MVP.
- Agrega persistencia SQLAlchemy/Alembic para el flujo MVP.
- Agrega endpoints CRUD para banca, sportsbook, evento, mercado, cuota, assessment, apuesta, settlement y postmortem.
- Agrega test API end-to-end del flujo MVP.
- Conecta el frontend a la API real y agrega acciones para seed, flujo MVP y settlement.
- Agrega estación de trabajo frontend con formularios manuales para banca, sportsbook, evento, mercado, cuota, assessment, apuesta, autopsia, CSV y capturas.
- Agrega `GET /api/v1/markets` para completar el flujo frontend manual.
- Agrega `import_rows`, parsing CSV persistente y confirmación de filas importadas como evento/mercado/cuota.
- Agrega edición de filas importadas antes de confirmar.
- Agrega analytics operativo por estado/tipo de apuesta y exportación CSV de apuestas.
- Agrega filtros de apuestas y detalle enriquecido de ticket en API y UI.
- Agrega control de banca con transacciones, exposicion por sportsbook, alertas e historial.
- Agrega capa de inteligencia deportiva con estadisticas, lesiones, mercado y analisis explicable por juego.
- Agrega pipeline de proveedor/sync, tracking de predicciones y backtesting/calibracion.
- Agrega conector de The Odds API y boton de sincronizacion de odds reales.
