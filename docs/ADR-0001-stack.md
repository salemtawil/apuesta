# ADR 0001 - Stack principal

## Estado

Aceptada.

## Contexto

El producto necesita UI privada, API tipada, cálculos auditables, migraciones y despliegue cloud sencillo.

## Decisión

Usar Next.js App Router con TypeScript para frontend y FastAPI con SQLAlchemy 2 para backend. Supabase provee Auth, PostgreSQL y Storage.

## Consecuencias

- Se evita mezclar Flask, Reflex, Streamlit y React.
- La lógica crítica vive en servicios Python testeables.
- El frontend consume API REST estable y puede desplegarse en Vercel.
