# Estrategia de datos y creditos

Fecha de revision: 2026-07-18.

## Que trae The Odds API

The Odds API entrega datos JSON de deportes activos, eventos proximos/en vivo, casas de apuesta, cuotas por mercado y, en algunos deportes, resultados/scores.

Datos principales que nos sirven:

- Deportes activos: `GET /v4/sports/`. No consume creditos.
- Eventos por deporte: `GET /v4/sports/{sport}/events`. No trae cuotas y no consume creditos.
- Odds actuales: `GET /v4/sports/{sport}/odds`. Trae eventos, bookmakers, mercados, selecciones, precio/cuota, linea y hora de actualizacion.
- Scores: `GET /v4/sports/{sport}/scores`. Sirve para resultados recientes o live cuando la liga esta cubierta.
- Event markets: `GET /v4/sports/{sport}/events/{eventId}/markets`. Sirve para saber mercados disponibles de un evento concreto.

## Como se gastan los creditos

Para odds actuales:

```text
costo = cantidad de mercados x cantidad de regiones
```

Ejemplos con region `us`:

- 1 deporte + ganador: 1 credito.
- 1 deporte + ganador, handicap, altas/bajas: 3 creditos.
- 10 deportes + ganador: 10 creditos.
- 10 deportes + 3 mercados: 30 creditos.

La app usa region `us` por ahora, asi que el costo estimado es:

```text
deportes seleccionados x mercados seleccionados
```

## Triunfobet observado

En la pagina publica de Triunfobet/Altenar se ven deportes como:

- Futbol
- Beisbol
- Baloncesto
- Futbol americano
- Hockey
- MMA
- Automovilismo
- E-sports
- Tenis
- Boxeo
- Tenis de mesa
- Voleibol
- Cricket
- Dardos
- Golf
- Rugby
- Padel
- Baloncesto 3x3
- Futbol sala
- Lacrosse
- Badminton
- Waterpolo

Triunfobet tambien documenta BetBuilder con mercados como ganador, total de goles/puntos, handicap, tarjetas y estadisticas especificas del evento.

## Regla de uso recomendada

Con 500 creditos mensuales, no conviene sincronizar todo cada rato.

Flujo recomendado:

1. Primero usar preset **Ahorro**: pocas ligas + mercado ganador.
2. Revisar si hay juegos interesantes.
3. Solo ampliar a handicap y altas/bajas en deportes/juegos que realmente vas a evaluar.
4. Evitar `Todo disponible` salvo una revision ocasional.
5. No sincronizar deportes fuera de temporada.
6. Priorizar futbol, beisbol, baloncesto, hockey y MMA porque cruzan mejor con Triunfobet y The Odds API.

## Mercados que conviene soportar primero

Base realista para la app:

- `h2h`: ganador / moneyline / 1X2.
- `spreads`: handicap.
- `totals`: altas/bajas.

Siguiente fase:

- tarjetas en futbol, si el proveedor devuelve ese mercado para el evento.
- props de jugadores, solo cuando el deporte y la casa lo tengan disponible.
- BetBuilder no debe sincronizarse en masa; se debe analizar manualmente por evento porque cambia mucho y puede gastar creditos rapido.

## Decision de producto

La app debe comportarse asi:

- Mostrar costo estimado antes de sincronizar.
- Sincronizar por defecto solo ganador.
- Permitir activar handicap y altas/bajas manualmente.
- Separar deportes compatibles con Triunfobet de deportes experimentales.
- Guardar creditos restantes despues de cada sync.
- Mas adelante, usar `/events` gratis para listar eventos primero y luego pedir odds solo de los mejores candidatos.

