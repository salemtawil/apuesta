# Open Source Audit

Fecha: 2026-07-15

## Repositorio actual

- Ruta: `C:\Users\salem\OneDrive\Documents\apuesta`
- Estado inicial: directorio vacío, sin repositorio Git.
- Código reutilizado: ninguno.
- Riesgo: bajo; no hay herencia técnica ni licencias internas que conservar.

## BenTartaglia/Decision-Support-Dashboard-SportsBetting

- URL: https://github.com/BenTartaglia/Decision-Support-Dashboard-SportsBetting
- Commit remoto inspeccionado: `5e5db3fa2d616c30ce24c779171a3f0e74e5144d`
- Licencia: no declarada en GitHub API y `/license` responde 404.
- Componentes útiles: separación entre predicción y decisión de apuesta, EV, Kelly, simulación de banca y presentación de value bets.
- Componentes descartados: dashboard Flask como arquitectura principal, integración directa XGBoost sin datasets propios, cualquier archivo de código por ausencia de licencia explícita.
- Riesgos técnicos: proyecto joven, sin licencia, baja señal de mantenimiento público, stack no alineado con Next.js/FastAPI.
- Dependencias observadas por metadatos: Python; descripción menciona Flask y XGBoost.
- Calidad del código: no evaluada por clonación incompleta; solo se auditaron metadatos remotos.
- Actividad reciente: creado 2026-03-17, último push 2026-04-15.
- Incompatibilidades: ausencia de licencia impide reutilización directa.
- Reutilización decidida: solo ideas reimplementadas desde cero.

## georgedouzas/sports-betting

- URL: https://github.com/georgedouzas/sports-betting
- Commit remoto inspeccionado: `25551a2abb897d8950d6675bda33e0342717d4bd`
- Licencia: MIT.
- Componentes útiles: dataloaders, bettors, evaluación, backtesting, interfaz compatible con modelos y separación por módulos.
- Componentes descartados: GUI Reflex, CLI completa, dependencia directa inicial.
- Riesgos técnicos: fuerte orientación a librería Python, no a producto multiusuario; dependencia futura debe quedar detrás de adapter.
- Dependencias: numpy, pandas, scikit-learn, pandera, aiohttp, Reflex opcional.
- Calidad del código: estructura empaquetada, typed package, tests, docs y tooling moderno.
- Actividad reciente: proyecto activo según changelog y metadatos.
- Incompatibilidades: dependencia directa aumenta peso del backend y acopla el dominio; no se incorpora en MVP.
- Reutilización decidida: inspiración para `BaseSportModel`, backtesting y adapters; no se copia código.

## lukegrady1/track-my-bets

- URL: https://github.com/lukegrady1/track-my-bets
- Commit remoto inspeccionado: `cbf0170562d229213c36a199f3d51cbbfe1036a0`
- Licencia: no declarada; no existe `LICENSE`.
- Componentes útiles: división frontend/backend, tracking de apuestas, banca, CSV y analítica de usuario.
- Componentes descartados: JWT propio, Vite como frontend principal, integraciones deportivas externas específicas, código fuente por falta de licencia.
- Riesgos técnicos: sin licencia, posible código prototipo, foco en NFL y sportsbook genérico.
- Dependencias: React, FastAPI, SQLAlchemy, Alembic, TanStack Query, Zod, Recharts.
- Calidad del código: estructura clara y útil como referencia conceptual.
- Actividad reciente: creado 2025-10-24, último push 2025-10-30.
- Incompatibilidades: no se puede reutilizar código directamente; auth preferida es Supabase.
- Reutilización decidida: patrón conceptual de tracker y analítica, reimplementado.

## rrajkowski/py-ai-betting

- URL solicitada: https://github.com/rrajkowski/py-ai-betting
- Estado: GitHub API y `git clone` devuelven 404; repositorio no público o no accesible.
- Licencia: no verificable.
- Componentes útiles: ninguno inspeccionable.
- Componentes descartados: dependencia directa y reutilización de código.
- Riesgos técnicos: inaccesible, no auditable.
- Reutilización decidida: crear interfaz IA opcional propia con mocks explícitos.

## Decisión global

BetAlpha Manager no será fork ni mezcla de stacks. Se implementará con Next.js App Router, TypeScript estricto, FastAPI, SQLAlchemy 2, Alembic y Supabase-ready. Las referencias aportan patrones, no código copiado.
