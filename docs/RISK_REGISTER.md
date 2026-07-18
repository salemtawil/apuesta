# Risk Register

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Licencias externas ausentes | Alto | No copiar código; solo ideas reimplementadas. |
| Confundir score con probabilidad | Alto | UI y API separan probabilidad, EV, score y disclaimers. |
| Kelly mal aplicado | Alto | Tests, límites conservadores y Kelly fraccionado por defecto. |
| Parlays correlacionados | Alto | Reglas heurísticas, warnings y probabilidad conjunta manual. |
| Data leakage en modelos | Alto | Walk-forward, snapshots de features y odds conocidas al momento. |
| Supabase no configurado localmente | Medio | Adapter local y `.env.example`, sin secretos. |
| OCR/IA costosa o inventada | Medio | Módulo opcional, confirmación humana y mocks claros. |
| Alcance MVP demasiado amplio | Alto | Priorizar flujo end-to-end y dejar backlog posterior. |
| Manejo de dinero con redondeos | Alto | Usar `Decimal` en backend y tests de settlement. |
| Scraping indebido | Alto | Sin scraping agresivo ni credenciales de Triunfobet. |
