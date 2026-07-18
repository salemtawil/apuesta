"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  API_BASE,
  AnalyticsSummary,
  AssessmentRead,
  Bankroll,
  BankrollControl,
  BacktestRun,
  Bet,
  BetDetail,
  DataProvider,
  Dashboard,
  EventItem,
  GameAnalysis,
  ImportRow,
  MarketRead,
  OddsRead,
  PredictionRecord,
  Sport,
  Sportsbook,
  SyncJobRun,
  TeamStat,
  TheOddsEventsResponse,
  TheOddsSyncResponse,
  getJson,
  patchJson,
  postForm,
  postJson,
} from "@/lib/api";

const navItems = [
  ["Hoy", "#hoy"],
  ["Mis Apuestas", "#tickets"],
  ["Banca", "#banca"],
  ["Avanzado", "#avanzado"],
];

const sportSyncOptions = [
  { key: "baseball_mlb", label: "MLB", group: "USA" },
  { key: "basketball_wnba", label: "WNBA", group: "USA" },
  { key: "basketball_nba", label: "NBA Summer", group: "USA" },
  { key: "americanfootball_nfl", label: "NFL", group: "USA" },
  { key: "americanfootball_nfl_preseason", label: "NFL Pre", group: "USA" },
  { key: "icehockey_nhl", label: "NHL", group: "USA" },
  { key: "mma_mixed_martial_arts", label: "UFC/MMA", group: "Combate" },
  { key: "boxing_boxing", label: "Boxeo", group: "Combate" },
  { key: "soccer_fifa_world_cup", label: "Mundial", group: "Futbol" },
  { key: "soccer_mexico_ligamx", label: "Liga MX", group: "Futbol" },
  { key: "soccer_epl", label: "Premier", group: "Futbol" },
  { key: "soccer_spain_la_liga", label: "La Liga", group: "Futbol" },
  { key: "soccer_germany_bundesliga", label: "Bundesliga", group: "Futbol" },
  { key: "soccer_italy_serie_a", label: "Serie A", group: "Futbol" },
  { key: "soccer_france_ligue_one", label: "Ligue 1", group: "Futbol" },
  { key: "soccer_usa_mls", label: "MLS", group: "Futbol" },
  { key: "soccer_conmebol_copa_libertadores", label: "Libertadores", group: "Futbol" },
  { key: "soccer_conmebol_copa_sudamericana", label: "Sudamericana", group: "Futbol" },
  { key: "soccer_argentina_primera_division", label: "Argentina", group: "Futbol" },
  { key: "soccer_brazil_campeonato", label: "Brasil A", group: "Futbol" },
  { key: "baseball_npb", label: "NPB Japon", group: "Mas deportes" },
  { key: "baseball_kbo", label: "KBO Corea", group: "Mas deportes" },
  { key: "rugbyleague_nrl", label: "Rugby NRL", group: "Mas deportes" },
  { key: "cricket_international_t20", label: "Cricket T20", group: "Mas deportes" },
  { key: "aussierules_afl", label: "AFL", group: "Mas deportes" },
  { key: "lacrosse_pll", label: "Lacrosse", group: "Mas deportes" },
];

const popularUsSportKeys = ["baseball_mlb", "basketball_wnba", "americanfootball_nfl", "soccer_usa_mls"];
const coreMarketKeys = ["h2h"];
const standardMarketKeys = ["h2h", "spreads", "totals"];
const marketSyncOptions = [
  { key: "h2h", label: "Ganador", note: "moneyline / 1X2" },
  { key: "spreads", label: "Handicap", note: "spread" },
  { key: "totals", label: "Altas/Bajas", note: "total puntos/goles" },
];
const triunfobetStyleKeys = [
  "soccer_mexico_ligamx",
  "soccer_epl",
  "soccer_spain_la_liga",
  "soccer_italy_serie_a",
  "soccer_germany_bundesliga",
  "baseball_mlb",
  "basketball_wnba",
  "icehockey_nhl",
  "mma_mixed_martial_arts",
  "boxing_boxing",
];
const popularSoccerKeys = [
  "soccer_fifa_world_cup",
  "soccer_mexico_ligamx",
  "soccer_epl",
  "soccer_spain_la_liga",
  "soccer_germany_bundesliga",
  "soccer_italy_serie_a",
  "soccer_france_ligue_one",
  "soccer_usa_mls",
  "soccer_conmebol_copa_libertadores",
  "soccer_conmebol_copa_sudamericana",
];

type BestPrice = {
  selectionId: string;
  selectionName: string;
  decimalOdds: number;
  sportsbookName: string;
};

type DateFilterMode = "today" | "tomorrow" | "next24" | "next48" | "next7" | "all";
type DecisionFilterMode = "all" | "Mejor lectura" | "Revisar" | "Sin ventaja clara" | "Faltan cuotas" | "Actualizar cuotas";

type ForecastLine = {
  label: string;
  selectionName: string;
  line: number | null;
  decimalOdds: number;
  sportsbookName: string;
  sportsbookCount: number;
};

type MarketForecast = {
  probableWinner: string;
  winnerProbability: number | null;
  probabilityGap: number | null;
  moneylineLean: string;
  spread: ForecastLine | null;
  total: ForecastLine | null;
  confidence: "Alta" | "Media" | "Baja";
  confidenceReasons: string[];
  recommendation: string;
  decisionLabel: string;
  decisionTone: "positive" | "warning" | "muted";
};

type SimpleGame = {
  event: EventItem;
  sportName: string;
  sportSlug: string;
  startsLabel: string;
  bestHome: BestPrice | null;
  bestAway: BestPrice | null;
  bestDraw: BestPrice | null;
  sportsbookCount: number;
  marketCount: number;
  favorite: string;
  riskLabel: string;
  decisionLabel: string;
  decisionTone: "positive" | "warning" | "muted";
  forecast: MarketForecast;
};

const emptyDashboard: Dashboard = {
  bankroll_count: 0,
  bankroll_balance: "0",
  total_staked: "0",
  settled_profit_loss: "0",
  roi: "0",
  yield_value: "0",
  open_bets: 0,
  exposure: "0",
};

const emptyAnalytics: AnalyticsSummary = {
  total_bets: 0,
  open_bets: 0,
  settled_bets: 0,
  total_staked: "0",
  profit_loss: "0",
  roi: "0",
  yield_value: "0",
  by_status: [],
  by_bet_type: [],
};

const emptyBankrollControl: BankrollControl = {
  bankrolls: [],
  transactions: [],
  exposures: [],
  alerts: [],
};

const nowIso = () => new Date().toISOString();

function money(value: string | number, currency = "USD") {
  return new Intl.NumberFormat("es-VE", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function pct(value: string | number) {
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function shortDate(value: string) {
  return new Intl.DateTimeFormat("es-VE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function localDateKey(value: Date | string) {
  const date = typeof value === "string" ? new Date(value) : value;
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function targetDateKey(mode: DateFilterMode) {
  const date = new Date();
  if (mode === "tomorrow") date.setDate(date.getDate() + 1);
  return localDateKey(date);
}

function isGameInsideDateFilter(startsAt: string, mode: DateFilterMode) {
  if (mode === "all") return true;
  if (mode === "today" || mode === "tomorrow") return localDateKey(startsAt) === targetDateKey(mode);

  const now = new Date();
  const starts = new Date(startsAt);
  const hoursByMode: Record<Exclude<DateFilterMode, "today" | "tomorrow" | "all">, number> = {
    next24: 24,
    next48: 48,
    next7: 24 * 7,
  };
  const windowEnd = new Date(now.getTime() + hoursByMode[mode] * 60 * 60 * 1000);
  return starts >= now && starts <= windowEnd;
}

function dateFilterLabel(mode: DateFilterMode) {
  if (mode === "all") return "Todos los proximos";
  if (mode === "next24") return "Proximas 24h";
  if (mode === "next48") return "Proximas 48h";
  if (mode === "next7") return "Proximos 7 dias";
  const date = new Date();
  if (mode === "tomorrow") date.setDate(date.getDate() + 1);
  return new Intl.DateTimeFormat("es-VE", { dateStyle: "medium" }).format(date);
}

function selectBetterPrice(current: BestPrice | null, candidate: BestPrice) {
  if (!current || candidate.decimalOdds > current.decimalOdds) return candidate;
  return current;
}

function lineLabel(value: number | null) {
  if (value === null || Number.isNaN(value)) return "";
  return value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
}

function totalLineLabel(value: number | null) {
  if (value === null || Number.isNaN(value)) return "";
  return value.toFixed(1);
}

function probabilityLabel(value: number | null) {
  return value === null ? "Sin prob." : `${Math.round(value * 100)}%`;
}

function normalizedMoneyline(
  homeTeam: string | null,
  awayTeam: string | null,
  homePrice: BestPrice | null,
  awayPrice: BestPrice | null,
  drawPrice: BestPrice | null,
) {
  if (!homePrice || !awayPrice) {
    return {
      probableWinner: "Sin lectura suficiente",
      winnerProbability: null,
      probabilityGap: null,
      moneylineLean: "Moneyline incompleto",
    };
  }

  const homeRaw = 1 / homePrice.decimalOdds;
  const awayRaw = 1 / awayPrice.decimalOdds;
  const drawRaw = drawPrice ? 1 / drawPrice.decimalOdds : 0;
  const total = homeRaw + awayRaw + drawRaw;
  const homeProbability = homeRaw / total;
  const awayProbability = awayRaw / total;
  const drawProbability = drawPrice ? drawRaw / total : 0;
  const outcomes = [
    { name: homeTeam ?? homePrice.selectionName, probability: homeProbability },
    { name: awayTeam ?? awayPrice.selectionName, probability: awayProbability },
    ...(drawPrice ? [{ name: "Empate", probability: drawProbability }] : []),
  ].sort((left, right) => right.probability - left.probability);
  const probableWinner = outcomes[0]?.name ?? "Sin lectura suficiente";
  const winnerProbability = outcomes[0]?.probability ?? null;
  const probabilityGap = outcomes.length > 1 ? outcomes[0].probability - outcomes[1].probability : 0;

  return {
    probableWinner,
    winnerProbability,
    probabilityGap,
    moneylineLean: `${probableWinner} ${probabilityLabel(winnerProbability)}`,
  };
}

function bestMarketLine(
  eventMarkets: MarketRead[],
  oddsBySelection: Map<string, OddsRead[]>,
  sportsbooksById: Map<string, Sportsbook>,
  marketType: "spread" | "total",
  preferredSelection?: string,
): ForecastLine | null {
  const candidates: Array<ForecastLine & { key: string }> = [];

  eventMarkets
    .filter((market) => market.market_type === marketType)
    .forEach((market) => {
      const line = market.line === null ? null : Number(market.line);
      const selectionOdds = oddsBySelection.get(market.selection.id) ?? [];
      const sportsbookIds = new Set(selectionOdds.map((item) => item.sportsbook_id));
      const bestPrice = selectionOdds.reduce<BestPrice | null>((current, item) => {
        const candidate = {
          selectionId: market.selection.id,
          selectionName: market.selection.selection_name,
          decimalOdds: Number(item.decimal_odds),
          sportsbookName: sportsbooksById.get(item.sportsbook_id)?.name ?? "Sportsbook",
        };
        return selectBetterPrice(current, candidate);
      }, null);

      if (!bestPrice) return;

      const lineText = marketType === "total" ? totalLineLabel(line) : lineLabel(line);
      candidates.push({
        key: `${market.selection.selection_name}-${lineText}`,
        label:
          marketType === "spread"
            ? `${market.selection.selection_name} ${lineText}`
            : `${market.selection.selection_name} ${lineText}`,
        selectionName: market.selection.selection_name,
        line,
        decimalOdds: bestPrice.decimalOdds,
        sportsbookName: bestPrice.sportsbookName,
        sportsbookCount: sportsbookIds.size,
      });
    });

  if (!candidates.length) return null;

  const filtered = preferredSelection
    ? candidates.filter((candidate) => candidate.selectionName === preferredSelection)
    : candidates;
  const pool = filtered.length ? filtered : candidates;

  return pool.sort((left, right) => {
    const coverage = right.sportsbookCount - left.sportsbookCount;
    if (coverage) return coverage;
    return right.decimalOdds - left.decimalOdds;
  })[0];
}

function buildMarketForecast({
  event,
  eventMarkets,
  homePrice,
  awayPrice,
  drawPrice,
  sportsbookCount,
  sportsbooksById,
  oddsBySelection,
}: {
  event: EventItem;
  eventMarkets: MarketRead[];
  homePrice: BestPrice | null;
  awayPrice: BestPrice | null;
  drawPrice: BestPrice | null;
  sportsbookCount: number;
  sportsbooksById: Map<string, Sportsbook>;
  oddsBySelection: Map<string, OddsRead[]>;
}): MarketForecast {
  const moneyline = normalizedMoneyline(event.home_team, event.away_team, homePrice, awayPrice, drawPrice);
  const spread = bestMarketLine(
    eventMarkets,
    oddsBySelection,
    sportsbooksById,
    "spread",
    moneyline.probableWinner,
  );
  const total = bestMarketLine(eventMarkets, oddsBySelection, sportsbooksById, "total");
  const hasCorePrices = Boolean(homePrice && awayPrice);
  const gap = moneyline.probabilityGap ?? 0;
  let score = 0;
  const reasons: string[] = [];

  if (sportsbookCount >= 8) {
    score += 2;
    reasons.push("buena cobertura de casas");
  } else if (sportsbookCount >= 3) {
    score += 1;
    reasons.push("cobertura media");
  } else {
    reasons.push("pocas casas comparadas");
  }

  if (spread) {
    score += 1;
    reasons.push("handicap disponible");
  }
  if (total) {
    score += 1;
    reasons.push("total disponible");
  }
  if (gap >= 0.12) {
    score += 2;
    reasons.push("favorito claro por mercado");
  } else if (gap >= 0.06) {
    score += 1;
    reasons.push("ventaja moderada en moneyline");
  } else if (hasCorePrices) {
    reasons.push("moneyline cerrado");
  }

  const confidence: MarketForecast["confidence"] = !hasCorePrices ? "Baja" : score >= 6 ? "Alta" : score >= 3 ? "Media" : "Baja";
  const decisionTone: MarketForecast["decisionTone"] = !hasCorePrices ? "muted" : confidence === "Alta" ? "positive" : "warning";
  const decisionLabel = !hasCorePrices ? "Faltan cuotas" : gap < 0.04 ? "Sin ventaja clara" : confidence === "Alta" ? "Mejor lectura" : "Revisar";
  const recommendation = !hasCorePrices
    ? "Actualiza cuotas antes de decidir."
    : gap < 0.04
      ? "Partido parejo: mejor esperar una línea con valor o evitar forzar entrada."
      : spread && total
        ? "Usa ganador probable como lectura base y confirma si el handicap o total mantienen precio razonable."
        : "Hay señal de moneyline, pero faltan mercados para validar handicap y total.";

  return {
    probableWinner: moneyline.probableWinner,
    winnerProbability: moneyline.winnerProbability,
    probabilityGap: moneyline.probabilityGap,
    moneylineLean: moneyline.moneylineLean,
    spread,
    total,
    confidence,
    confidenceReasons: reasons,
    recommendation,
    decisionLabel,
    decisionTone,
  };
}

function buildSimpleGames(
  events: EventItem[],
  sports: Sport[],
  markets: MarketRead[],
  odds: OddsRead[],
  sportsbooks: Sportsbook[],
): SimpleGame[] {
  const sportsById = new Map(sports.map((sport) => [sport.id, sport]));
  const sportsbooksById = new Map(sportsbooks.map((sportsbook) => [sportsbook.id, sportsbook]));
  const marketsByEvent = new Map<string, MarketRead[]>();
  const oddsBySelection = new Map<string, OddsRead[]>();

  markets.forEach((market) => {
    const current = marketsByEvent.get(market.event_id) ?? [];
    current.push(market);
    marketsByEvent.set(market.event_id, current);
  });
  odds.forEach((item) => {
    const current = oddsBySelection.get(item.market_selection_id) ?? [];
    current.push(item);
    oddsBySelection.set(item.market_selection_id, current);
  });

  return events
    .slice()
    .sort((left, right) => new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime())
    .map((event) => {
      const eventMarkets = marketsByEvent.get(event.id) ?? [];
      const moneylineMarkets = eventMarkets.filter((market) => market.market_type === "moneyline");
      const sportsbookIds = new Set<string>();
      const homeCandidates: BestPrice[] = [];
      const awayCandidates: BestPrice[] = [];
      const drawCandidates: BestPrice[] = [];

      moneylineMarkets.forEach((market) => {
        const selectionOdds = oddsBySelection.get(market.selection.id) ?? [];
        selectionOdds.forEach((item) => {
          sportsbookIds.add(item.sportsbook_id);
          const candidate = {
            selectionId: market.selection.id,
            selectionName: market.selection.selection_name,
            decimalOdds: Number(item.decimal_odds),
            sportsbookName: sportsbooksById.get(item.sportsbook_id)?.name ?? "Sportsbook",
          };
          if (event.home_team && market.selection.selection_name === event.home_team) {
            homeCandidates.push(candidate);
          }
          if (event.away_team && market.selection.selection_name === event.away_team) {
            awayCandidates.push(candidate);
          }
          if (market.selection.selection_name.toLowerCase() === "draw") {
            drawCandidates.push({ ...candidate, selectionName: "Empate" });
          }
        });
      });

      const homePrice = homeCandidates.reduce<BestPrice | null>(selectBetterPrice, null);
      const awayPrice = awayCandidates.reduce<BestPrice | null>(selectBetterPrice, null);
      const drawPrice = drawCandidates.reduce<BestPrice | null>(selectBetterPrice, null);
      const hasCorePrices = Boolean(homePrice && awayPrice);
      const riskLabel = sportsbookIds.size >= 8 ? "Cobertura buena" : sportsbookIds.size >= 3 ? "Cobertura media" : "Poca cobertura";
      const forecast = buildMarketForecast({
        event,
        eventMarkets,
        homePrice,
        awayPrice,
        drawPrice,
        sportsbookCount: sportsbookIds.size,
        sportsbooksById,
        oddsBySelection,
      });

      return {
        event,
        sportName: sportsById.get(event.sport_id)?.name ?? event.league_name,
        sportSlug: sportsById.get(event.sport_id)?.slug ?? "",
        startsLabel: shortDate(event.starts_at),
        bestHome: homePrice,
        bestAway: awayPrice,
        bestDraw: drawPrice,
        sportsbookCount: sportsbookIds.size,
        marketCount: eventMarkets.length,
        favorite: forecast.probableWinner,
        riskLabel,
        decisionLabel: hasCorePrices ? forecast.decisionLabel : "Actualizar cuotas",
        decisionTone: forecast.decisionTone,
        forecast,
      };
    })
    .sort((left, right) => {
      const leftReady = Number(Boolean(left.bestHome && left.bestAway));
      const rightReady = Number(Boolean(right.bestHome && right.bestAway));
      return rightReady - leftReady || new Date(left.event.starts_at).getTime() - new Date(right.event.starts_at).getTime();
    });
}

export default function DashboardClient() {
  const [dashboard, setDashboard] = useState<Dashboard>(emptyDashboard);
  const [sports, setSports] = useState<Sport[]>([]);
  const [sportsbooks, setSportsbooks] = useState<Sportsbook[]>([]);
  const [bankrolls, setBankrolls] = useState<Bankroll[]>([]);
  const [bankrollControl, setBankrollControl] = useState<BankrollControl>(emptyBankrollControl);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [markets, setMarkets] = useState<MarketRead[]>([]);
  const [odds, setOdds] = useState<OddsRead[]>([]);
  const [teamStats, setTeamStats] = useState<TeamStat[]>([]);
  const [analyses, setAnalyses] = useState<GameAnalysis[]>([]);
  const [providers, setProviders] = useState<DataProvider[]>([]);
  const [syncJobs, setSyncJobs] = useState<SyncJobRun[]>([]);
  const [predictionRecords, setPredictionRecords] = useState<PredictionRecord[]>([]);
  const [backtests, setBacktests] = useState<BacktestRun[]>([]);
  const [lastGameAnalysis, setLastGameAnalysis] = useState<GameAnalysis | null>(null);
  const [importRows, setImportRows] = useState<ImportRow[]>([]);
  const [importEdits, setImportEdits] = useState<Record<string, Partial<ImportRow>>>({});
  const [analytics, setAnalytics] = useState<AnalyticsSummary>(emptyAnalytics);
  const [bets, setBets] = useState<Bet[]>([]);
  const [betDetail, setBetDetail] = useState<BetDetail | null>(null);
  const [lastAssessment, setLastAssessment] = useState<AssessmentRead | null>(null);
  const [selectedSimpleGameId, setSelectedSimpleGameId] = useState<string | null>(null);
  const [selectedSportKeys, setSelectedSportKeys] = useState<string[]>(["baseball_mlb"]);
  const [selectedMarketKeys, setSelectedMarketKeys] = useState<string[]>(coreMarketKeys);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Listo para sincronizar con FastAPI.");
  const [error, setError] = useState<string | null>(null);

  const [bankrollForm, setBankrollForm] = useState({
    name: "Banca principal",
    currency: "USD",
    starting_balance: "1000.00",
    unit_size: "10.00",
  });
  const [sportsbookForm, setSportsbookForm] = useState({ name: "Triunfobet", country: "VE" });
  const [transactionForm, setTransactionForm] = useState({
    bankroll_id: "",
    transaction_type: "deposit",
    amount: "100.00",
    note: "Movimiento manual",
  });
  const [eventForm, setEventForm] = useState({
    sport_id: "",
    league_name: "Liga",
    home_team: "Equipo A",
    away_team: "Equipo B",
    event_name: "Equipo A vs Equipo B",
    starts_at: "2026-01-01T20:00:00Z",
  });
  const [marketForm, setMarketForm] = useState({
    event_id: "",
    market_type: "spread",
    selection_name: "Equipo A +3.5",
    line: "3.5",
  });
  const [oddsForm, setOddsForm] = useState({
    sportsbook_id: "",
    market_selection_id: "",
    decimal_odds: "1.91",
  });
  const [assessmentForm, setAssessmentForm] = useState({
    event_id: "",
    market_selection_id: "",
    odds_snapshot_id: "",
    bankroll_id: "",
    estimated_probability: "0.56",
  });
  const [analysisForm, setAnalysisForm] = useState({
    event_id: "",
    offered_home_odds: "1.91",
    offered_away_odds: "1.91",
  });
  const [betForm, setBetForm] = useState({
    bankroll_id: "",
    sportsbook_id: "",
    event_id: "",
    market_selection_id: "",
    odds_at_placement: "1.91",
    estimated_probability_at_placement: "0.56",
    stake: "10.00",
    bet_type: "single",
  });
  const [betFilters, setBetFilters] = useState({
    status: "",
    bet_type: "",
    bankroll_id: "",
    sportsbook_id: "",
    date_from: "",
    date_to: "",
  });
  const [postmortemForm, setPostmortemForm] = useState({
    bet_id: "",
    analysis_quality: "buena_apuesta_gano",
    result_quality: "ganada",
    primary_failure_reason: "",
    lessons: "Se respeto el proceso y el stake definido.",
  });

  const primaryBankroll = bankrolls[0];
  const currency = primaryBankroll?.currency ?? "USD";

  const metrics = useMemo(
    () => [
      ["Banca actual", money(dashboard.bankroll_balance, currency), `${dashboard.bankroll_count} banca(s)`],
      ["P&L liquidado", money(dashboard.settled_profit_loss, currency), "resultados registrados"],
      ["ROI", pct(dashboard.roi), "sobre stake total"],
      ["Yield", pct(dashboard.yield_value), "stake liquidado"],
      ["Apuestas abiertas", String(dashboard.open_bets), "tickets pendientes"],
      ["Exposicion abierta", money(dashboard.exposure, currency), "riesgo vivo"],
    ],
    [currency, dashboard],
  );
  const simpleGames = useMemo(
    () => buildSimpleGames(events, sports, markets, odds, sportsbooks),
    [events, sports, markets, odds, sportsbooks],
  );
  const selectedSimpleGame = simpleGames.find((game) => game.event.id === selectedSimpleGameId) ?? null;
  const lastOddsSync = syncJobs.find((job) => job.provider_key === "the_odds_api");

  function betsPath(filters = betFilters) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const query = params.toString();
    return query ? `/bets?${query}` : "/bets";
  }

  function applyDefaults(next: {
    nextSports?: Sport[];
    nextSportsbooks?: Sportsbook[];
    nextBankrolls?: Bankroll[];
    nextEvents?: EventItem[];
    nextMarkets?: MarketRead[];
    nextOdds?: OddsRead[];
    nextBets?: Bet[];
  }) {
    const sport = next.nextSports?.[0] ?? sports[0];
    const sportsbook = next.nextSportsbooks?.[0] ?? sportsbooks[0];
    const bankroll = next.nextBankrolls?.[0] ?? bankrolls[0];
    const event = next.nextEvents?.[0] ?? events[0];
    const market = next.nextMarkets?.[0] ?? markets[0];
    const odd = next.nextOdds?.[0] ?? odds[0];
    const openBet = (next.nextBets ?? bets).find((bet) => bet.status === "open");

    if (sport) setEventForm((current) => ({ ...current, sport_id: current.sport_id || sport.id }));
    if (event) {
      setMarketForm((current) => ({ ...current, event_id: current.event_id || event.id }));
      setAssessmentForm((current) => ({ ...current, event_id: current.event_id || event.id }));
      setBetForm((current) => ({ ...current, event_id: current.event_id || event.id }));
      setAnalysisForm((current) => ({ ...current, event_id: current.event_id || event.id }));
    }
    if (sportsbook) {
      setOddsForm((current) => ({ ...current, sportsbook_id: current.sportsbook_id || sportsbook.id }));
      setBetForm((current) => ({ ...current, sportsbook_id: current.sportsbook_id || sportsbook.id }));
    }
    if (bankroll) {
      setAssessmentForm((current) => ({ ...current, bankroll_id: current.bankroll_id || bankroll.id }));
      setBetForm((current) => ({ ...current, bankroll_id: current.bankroll_id || bankroll.id }));
      setTransactionForm((current) => ({ ...current, bankroll_id: current.bankroll_id || bankroll.id }));
    }
    if (market) {
      setOddsForm((current) => ({
        ...current,
        market_selection_id: current.market_selection_id || market.selection.id,
      }));
      setAssessmentForm((current) => ({
        ...current,
        event_id: current.event_id || market.event_id,
        market_selection_id: current.market_selection_id || market.selection.id,
      }));
      setBetForm((current) => ({
        ...current,
        event_id: current.event_id || market.event_id,
        market_selection_id: current.market_selection_id || market.selection.id,
      }));
    }
    if (odd) {
      setAssessmentForm((current) => ({
        ...current,
        odds_snapshot_id: current.odds_snapshot_id || odd.id,
      }));
      setBetForm((current) => ({
        ...current,
        odds_at_placement: current.odds_at_placement || odd.decimal_odds,
      }));
    }
    if (openBet) setPostmortemForm((current) => ({ ...current, bet_id: current.bet_id || openBet.id }));
  }

  async function refresh(filters = betFilters) {
    setError(null);
    try {
      const [
        nextDashboard,
        nextSports,
        nextSportsbooks,
        nextBankrolls,
        nextEvents,
        nextMarkets,
        nextOdds,
        nextBets,
        nextImportRows,
        nextAnalytics,
        nextBankrollControl,
        nextTeamStats,
        nextAnalyses,
        nextProviders,
        nextSyncJobs,
        nextPredictionRecords,
        nextBacktests,
      ] = await Promise.all([
        getJson<Dashboard>("/dashboard"),
        getJson<Sport[]>("/sports"),
        getJson<Sportsbook[]>("/sportsbooks"),
        getJson<Bankroll[]>("/bankrolls"),
        getJson<EventItem[]>("/events"),
        getJson<MarketRead[]>("/markets"),
        getJson<OddsRead[]>("/odds"),
        getJson<Bet[]>(betsPath(filters)),
        getJson<ImportRow[]>("/imports/rows"),
        getJson<AnalyticsSummary>("/analytics/summary"),
        getJson<BankrollControl>("/bankroll-control"),
        getJson<TeamStat[]>("/intelligence/team-stats"),
        getJson<GameAnalysis[]>("/intelligence/analyses"),
        getJson<DataProvider[]>("/intelligence/providers"),
        getJson<SyncJobRun[]>("/intelligence/sync/jobs"),
        getJson<PredictionRecord[]>("/intelligence/predictions"),
        getJson<BacktestRun[]>("/intelligence/backtests"),
      ]);
      setDashboard(nextDashboard);
      setSports(nextSports);
      setSportsbooks(nextSportsbooks);
      setBankrolls(nextBankrolls);
      setEvents(nextEvents);
      setMarkets(nextMarkets);
      setOdds(nextOdds);
      setBets(nextBets);
      if (betDetail && !nextBets.some((bet) => bet.id === betDetail.id)) setBetDetail(null);
      setImportRows(nextImportRows);
      setAnalytics(nextAnalytics);
      setBankrollControl(nextBankrollControl);
      setTeamStats(nextTeamStats);
      setAnalyses(nextAnalyses);
      setProviders(nextProviders);
      setSyncJobs(nextSyncJobs);
      setPredictionRecords(nextPredictionRecords);
      setBacktests(nextBacktests);
      setLastGameAnalysis(nextAnalyses[0] ?? null);
      applyDefaults({ nextSports, nextSportsbooks, nextBankrolls, nextEvents, nextMarkets, nextOdds, nextBets });
      setMessage("Datos sincronizados con FastAPI.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo cargar la API.");
    }
  }

  useEffect(() => {
    // Initial API synchronization for this client-side dashboard.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runAction(label: string, action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      await refresh();
      setMessage(label);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Accion no completada.");
    } finally {
      setBusy(false);
    }
  }

  async function createBankroll(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("Banca creada.", async () => {
      await postJson<Bankroll>("/bankrolls", bankrollForm);
    });
  }

  async function createSportsbook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("Sportsbook creado.", async () => {
      await postJson<Sportsbook>("/sportsbooks", sportsbookForm);
    });
  }

  async function createBankrollTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("Movimiento de banca registrado.", async () => {
      const bankrollId = transactionForm.bankroll_id || bankrolls[0]?.id;
      if (!bankrollId) throw new Error("Crea una banca antes de registrar movimientos.");
      await postJson<{ id: string }>("/bankroll-transactions", {
        bankroll_id: bankrollId,
        transaction_type: transactionForm.transaction_type,
        amount: transactionForm.amount,
        note: transactionForm.note,
      });
    });
  }

  async function createEventMarketOdds(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("Evento, mercado y cuota creados.", async () => {
      const createdEvent = await postJson<EventItem>("/events", {
        ...eventForm,
        sport_id: eventForm.sport_id || sports[0]?.id,
        timezone: "UTC",
      });
      const createdMarket = await postJson<MarketRead>("/markets", {
        ...marketForm,
        event_id: createdEvent.id,
        line: marketForm.line || null,
      });
      const sportsbookId = oddsForm.sportsbook_id || sportsbooks[0]?.id;
      if (!sportsbookId) throw new Error("Crea un sportsbook antes de registrar cuotas.");
      await postJson<OddsRead>("/odds", {
        sportsbook_id: sportsbookId,
        market_selection_id: createdMarket.selection.id,
        decimal_odds: oddsForm.decimal_odds,
        captured_at: nowIso(),
      });
    });
  }

  async function createAssessment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("Assessment guardado.", async () => {
      const assessment = await postJson<AssessmentRead>("/assessments/stored", {
        ...assessmentForm,
        event_id: assessmentForm.event_id || events[0]?.id,
        market_selection_id: assessmentForm.market_selection_id || markets[0]?.selection.id,
        odds_snapshot_id: assessmentForm.odds_snapshot_id || odds[0]?.id,
        bankroll_id: assessmentForm.bankroll_id || bankrolls[0]?.id,
        generated_at: nowIso(),
        explanation: "Probabilidad manual ingresada desde la UI MVP.",
      });
      setLastAssessment(assessment);
    });
  }

  async function runOddsSync() {
    setBusy(true);
    setError(null);
    try {
      const synced = await postJson<TheOddsSyncResponse>("/intelligence/sync/odds", {
        sport_keys: selectedSportKeys.length ? selectedSportKeys : ["baseball_mlb"],
        regions: "us",
        markets: selectedMarketKeys.length ? selectedMarketKeys : coreMarketKeys,
      });
      await refresh();
      setMessage(
        `Datos reales actualizados para ${selectedSportKeys.length || 1} deporte(s): ${synced.events_upserted} juegos, ${synced.odds_inserted} cuotas. Creditos restantes: ${synced.requests_remaining ?? "n/d"}.`,
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudieron sincronizar odds reales.");
    } finally {
      setBusy(false);
    }
  }

  async function runCandidateScan() {
    setBusy(true);
    setError(null);
    try {
      const scanned = await postJson<TheOddsEventsResponse>("/intelligence/events/candidates", {
        sport_keys: selectedSportKeys.length ? selectedSportKeys : ["baseball_mlb"],
      });
      await refresh();
      setMessage(
        `Candidatos cargados sin odds completas: ${scanned.events_upserted} juegos. Creditos restantes: ${scanned.requests_remaining ?? "n/d"}.`,
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudieron buscar candidatos.");
    } finally {
      setBusy(false);
    }
  }

  async function runOddsSyncForGame(game: SimpleGame) {
    if (!game.sportSlug) {
      setError("No se pudo identificar el deporte de este juego.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const synced = await postJson<TheOddsSyncResponse>("/intelligence/sync/odds", {
        sport_keys: [game.sportSlug],
        regions: "us",
        markets: selectedMarketKeys.length ? selectedMarketKeys : coreMarketKeys,
      });
      await refresh();
      setSelectedSimpleGameId(game.event.id);
      setMessage(
        `Cuotas cargadas para ${game.sportName}: ${synced.events_upserted} juegos, ${synced.odds_inserted} cuotas. Creditos restantes: ${synced.requests_remaining ?? "n/d"}.`,
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudieron cargar cuotas para este candidato.");
    } finally {
      setBusy(false);
    }
  }

  function prepareSimpleGame(game: SimpleGame) {
    setSelectedSimpleGameId(game.event.id);
    setAnalysisForm((current) => ({
      ...current,
      event_id: game.event.id,
      offered_home_odds: game.bestHome ? String(game.bestHome.decimalOdds) : current.offered_home_odds,
      offered_away_odds: game.bestAway ? String(game.bestAway.decimalOdds) : current.offered_away_odds,
    }));
    setBetForm((current) => ({
      ...current,
      event_id: game.event.id,
      market_selection_id: game.bestHome?.selectionId ?? game.bestAway?.selectionId ?? current.market_selection_id,
      odds_at_placement: game.bestHome
        ? String(game.bestHome.decimalOdds)
        : game.bestAway
          ? String(game.bestAway.decimalOdds)
          : current.odds_at_placement,
    }));
    setAssessmentForm((current) => ({
      ...current,
      event_id: game.event.id,
      market_selection_id: game.bestHome?.selectionId ?? game.bestAway?.selectionId ?? current.market_selection_id,
    }));
    window.setTimeout(() => {
      document.getElementById("partido-preparado")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 0);
    setMessage(`${game.event.event_name} preparado. Ya puedes revisar el resumen visible del partido.`);
  }

  async function createGameAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("Analisis del juego generado.", async () => {
      const selectedEvent = analysisForm.event_id || events[0]?.id;
      if (!selectedEvent) throw new Error("Crea o selecciona un evento antes de analizar.");
      const analysis = await postJson<GameAnalysis>("/intelligence/analyze", {
        event_id: selectedEvent,
        offered_home_odds: analysisForm.offered_home_odds || null,
        offered_away_odds: analysisForm.offered_away_odds || null,
      });
      setLastGameAnalysis(analysis);
    });
  }

  async function evaluatePrediction(predictionId: string, result: "win" | "loss" | "void") {
    await runAction(`Prediccion marcada como ${result}.`, async () => {
      await patchJson<PredictionRecord>(`/intelligence/predictions/${predictionId}`, { result });
    });
  }

  async function runBacktest() {
    await runAction("Backtest ejecutado.", async () => {
      await postJson<BacktestRun>("/intelligence/backtests/run", {});
    });
  }

  async function createBet(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("Apuesta creada.", async () => {
      const bankroll = bankrolls.find((item) => item.id === betForm.bankroll_id) ?? bankrolls[0];
      if (!bankroll) throw new Error("Crea una banca antes de crear apuestas.");
      await postJson<Bet>("/bets", {
        bankroll_id: betForm.bankroll_id || bankroll.id,
        sportsbook_id: betForm.sportsbook_id || sportsbooks[0]?.id,
        bet_type: betForm.bet_type,
        stake: betForm.stake,
        currency: bankroll.currency,
        legs: [
          {
            event_id: betForm.event_id || events[0]?.id,
            market_selection_id: betForm.market_selection_id || markets[0]?.selection.id,
            odds_at_placement: betForm.odds_at_placement,
            estimated_probability_at_placement: betForm.estimated_probability_at_placement,
          },
        ],
      });
    });
  }

  async function settleBet(betId: string, result: "win" | "loss" | "void") {
    await runAction(`Apuesta liquidada como ${result}.`, async () => {
      await postJson<Bet>(`/bets/${betId}/settle`, { result });
    });
  }

  async function loadBetDetail(betId: string) {
    setBusy(true);
    setError(null);
    try {
      const detail = await getJson<BetDetail>(`/bets/${betId}`);
      setBetDetail(detail);
      setMessage("Detalle de apuesta cargado.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No se pudo cargar el detalle.");
    } finally {
      setBusy(false);
    }
  }

  async function resetBetFilters() {
    const clearedFilters = {
      status: "",
      bet_type: "",
      bankroll_id: "",
      sportsbook_id: "",
      date_from: "",
      date_to: "",
    };
    setBetFilters(clearedFilters);
    setBetDetail(null);
    await refresh(clearedFilters);
  }

  async function createPostmortem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("Autopsia guardada.", async () => {
      await postJson<{ id: string }>("/postmortems", {
        ...postmortemForm,
        bet_id: postmortemForm.bet_id || bets[0]?.id,
        process_followed: true,
        reviewed_by_user: true,
      });
    });
  }

  async function uploadFile(event: FormEvent<HTMLFormElement>, path: string, label: string) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("file") as HTMLInputElement | null;
    const file = input?.files?.[0];
    if (!file) {
      setError("Selecciona un archivo primero.");
      return;
    }
    await runAction(label, async () => {
      const form = new FormData();
      form.append("file", file);
      await postForm<{ status: string }>(path, form);
      event.currentTarget.reset();
    });
  }

  async function confirmImportRow(rowId: string) {
    await runAction("Fila importada confirmada como evento, mercado y cuota.", async () => {
      await postJson<{ event_id: string; market_id: string; odds_snapshot_id: string }>(
        `/imports/rows/${rowId}/confirm`,
        {},
      );
    });
  }

  function importValue(row: ImportRow, key: keyof ImportRow) {
    const edited = importEdits[row.id]?.[key];
    return typeof edited === "string" ? edited : String(row[key] ?? "");
  }

  function updateImportEdit(rowId: string, key: keyof ImportRow, value: string) {
    setImportEdits((current) => ({
      ...current,
      [rowId]: {
        ...(current[rowId] ?? {}),
        [key]: value,
      },
    }));
  }

  async function saveImportRow(row: ImportRow) {
    await runAction("Fila importada actualizada.", async () => {
      const edited = importEdits[row.id] ?? {};
      await patchJson<ImportRow>(`/imports/rows/${row.id}`, {
        sport: edited.sport ?? row.sport,
        league: edited.league ?? row.league,
        event: edited.event ?? row.event,
        market_type: edited.market_type ?? row.market_type,
        selection: edited.selection ?? row.selection,
        odds: edited.odds ?? row.odds,
        sportsbook: edited.sportsbook ?? row.sportsbook,
        captured_at: edited.captured_at ?? row.captured_at,
      });
      setImportEdits((current) => {
        const next = { ...current };
        delete next[row.id];
        return next;
      });
    });
  }

  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 border-r border-[var(--border)] bg-[var(--panel)] px-4 py-5 lg:block">
          <div className="mb-7">
            <p className="text-xs font-semibold uppercase text-[var(--muted)]">Privado</p>
            <h1 className="mt-1 text-2xl font-semibold">BetAlpha Manager</h1>
          </div>
          <nav className="space-y-1">
            {navItems.map(([item, href]) => (
              <a
                className="block rounded-md px-3 py-2 text-sm text-[var(--muted)] hover:bg-[var(--soft)] hover:text-[var(--foreground)]"
                href={href}
                key={item}
              >
                {item}
              </a>
            ))}
          </nav>
        </aside>

        <section className="flex-1">
          <header className="border-b border-[var(--border)] bg-[var(--panel)] px-4 py-4 sm:px-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm text-[var(--muted)]">API: {API_BASE}</p>
                <h2 className="text-2xl font-semibold">Panel de decisiones</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="btn" disabled={busy} onClick={() => refresh()}>Sincronizar</button>
              </div>
            </div>
          </header>

          <div className="space-y-6 px-4 py-5 sm:px-6">
            <div className={error ? "notice notice-error" : "notice"}>
              <span>{error ?? message}</span>
            </div>

            <SimpleToday
              busy={busy}
              games={simpleGames}
              lastOddsSync={lastOddsSync}
              onLoadOddsForGame={runOddsSyncForGame}
              onPrepareGame={prepareSimpleGame}
              onRefresh={runOddsSync}
              onScanEvents={runCandidateScan}
              selectedMarketKeys={selectedMarketKeys}
              setSelectedMarketKeys={setSelectedMarketKeys}
              selectedSportKeys={selectedSportKeys}
              setSelectedSportKeys={setSelectedSportKeys}
              selectedGame={selectedSimpleGame}
            />

            <details className="advanced-shell" id="avanzado">
              <summary>Avanzado: banca, apuestas, importaciones y backtesting</summary>
              <div className="mt-5 space-y-6">
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
              {metrics.map(([label, value, note]) => (
                <div className="metric" key={label}>
                  <p className="text-xs font-medium text-[var(--muted)]">{label}</p>
                  <p className="mt-2 text-2xl font-semibold">{value}</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">{note}</p>
                </div>
              ))}
            </section>

            <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]" id="banca">
              <Panel title="Control de banca">
                <form className="form-grid" onSubmit={createBankrollTransaction}>
                  <SelectField label="Banca" value={transactionForm.bankroll_id} onChange={(bankroll_id) => setTransactionForm({ ...transactionForm, bankroll_id })} options={bankrolls.map((bankroll) => [bankroll.id, bankroll.name])} />
                  <label className="field">
                    <span>Tipo</span>
                    <select value={transactionForm.transaction_type} onChange={(event) => setTransactionForm({ ...transactionForm, transaction_type: event.target.value })}>
                      <option value="deposit">Deposito</option>
                      <option value="withdrawal">Retiro</option>
                      <option value="adjustment">Ajuste</option>
                    </select>
                  </label>
                  <Field label="Monto" value={transactionForm.amount} onChange={(amount) => setTransactionForm({ ...transactionForm, amount })} />
                  <Field label="Nota" value={transactionForm.note} onChange={(note) => setTransactionForm({ ...transactionForm, note })} />
                  <button className="btn btn-primary" disabled={busy}>Registrar movimiento</button>
                </form>

                <div className="mt-4 grid gap-2">
                  {bankrollControl.alerts.map((alert) => (
                    <div className={alert.severity === "high" ? "risk-alert risk-alert-high" : "risk-alert"} key={`${alert.code}-${alert.message}`}>
                      <p className="font-semibold">{alert.code}</p>
                      <p className="text-sm">{alert.message}</p>
                    </div>
                  ))}
                  {!bankrollControl.alerts.length ? <p className="text-sm text-[var(--muted)]">Sin alertas de riesgo activas.</p> : null}
                </div>
              </Panel>

              <Panel title="Exposicion por sportsbook">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--muted)]">
                        {["Casa", "Abiertas", "Liquidadas", "Exposicion", "Stake", "P&L", "ROI"].map((head) => <th className="px-3 py-2 font-semibold" key={head}>{head}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {bankrollControl.exposures.map((exposure) => (
                        <tr className="border-b border-[var(--border)] last:border-0" key={exposure.sportsbook_id}>
                          <td className="px-3 py-2">{exposure.sportsbook_name}</td>
                          <td className="px-3 py-2">{exposure.open_bets}</td>
                          <td className="px-3 py-2">{exposure.settled_bets}</td>
                          <td className="px-3 py-2">{money(exposure.open_exposure, currency)}</td>
                          <td className="px-3 py-2">{money(exposure.total_staked, currency)}</td>
                          <td className={Number(exposure.profit_loss) >= 0 ? "px-3 py-2 text-positive" : "px-3 py-2 text-negative"}>{money(exposure.profit_loss, currency)}</td>
                          <td className="px-3 py-2">{pct(exposure.roi)}</td>
                        </tr>
                      ))}
                      {!bankrollControl.exposures.length ? <tr><td className="px-3 py-3 text-[var(--muted)]" colSpan={7}>Sin sportsbooks registrados.</td></tr> : null}
                    </tbody>
                  </table>
                </div>
              </Panel>
            </section>

            <section className="panel overflow-hidden">
              <div className="panel-header">
                <div>
                  <h3>Historial de banca</h3>
                  <p>Depositos, retiros, ajustes y liquidaciones.</p>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--muted)]">
                      {["Banca", "Tipo", "Monto", "Saldo posterior", "Nota"].map((head) => <th className="px-4 py-3 font-semibold" key={head}>{head}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {bankrollControl.transactions.map((transaction) => (
                      <tr className="border-b border-[var(--border)] last:border-0" key={transaction.id}>
                        <td className="px-4 py-3">{bankrolls.find((bankroll) => bankroll.id === transaction.bankroll_id)?.name ?? "-"}</td>
                        <td className="px-4 py-3">{transaction.transaction_type}</td>
                        <td className={Number(transaction.amount) >= 0 ? "px-4 py-3 text-positive" : "px-4 py-3 text-negative"}>{money(transaction.amount, currency)}</td>
                        <td className="px-4 py-3">{money(transaction.balance_after, currency)}</td>
                        <td className="px-4 py-3">{transaction.note ?? "-"}</td>
                      </tr>
                    ))}
                    {!bankrollControl.transactions.length ? <tr><td className="px-4 py-6 text-[var(--muted)]" colSpan={5}>Sin movimientos registrados.</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]" id="inteligencia">
              <Panel title="Inteligencia deportiva">
                <div className="flex flex-wrap gap-2">
                  <button className="btn btn-primary" disabled={busy} onClick={runOddsSync}>Actualizar juegos reales</button>
                  <button className="btn btn-primary" disabled={busy} onClick={runBacktest}>Backtest</button>
                </div>
                <form className="form-grid mt-4" onSubmit={createGameAnalysis}>
                  <SelectField label="Evento" value={analysisForm.event_id} onChange={(event_id) => setAnalysisForm({ ...analysisForm, event_id })} options={events.map((event) => [event.id, event.event_name])} />
                  <Field label="Cuota local" value={analysisForm.offered_home_odds} onChange={(offered_home_odds) => setAnalysisForm({ ...analysisForm, offered_home_odds })} />
                  <Field label="Cuota visitante" value={analysisForm.offered_away_odds} onChange={(offered_away_odds) => setAnalysisForm({ ...analysisForm, offered_away_odds })} />
                  <button className="btn btn-primary" disabled={busy}>Generar analisis</button>
                </form>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div><dt>Snapshots</dt><dd>{teamStats.length}</dd></div>
                  <div><dt>Analisis guardados</dt><dd>{analyses.length}</dd></div>
                  <div><dt>Proveedores</dt><dd>{providers.length}</dd></div>
                  <div><dt>Sync jobs</dt><dd>{syncJobs.length}</dd></div>
                  <div><dt>Predicciones</dt><dd>{predictionRecords.length}</dd></div>
                  <div><dt>Backtests</dt><dd>{backtests.length}</dd></div>
                </dl>
              </Panel>

              <Panel title="Analisis del juego">
                {lastGameAnalysis ? (
                  <GameAnalysisCard analysis={lastGameAnalysis} />
                ) : (
                  <p className="text-sm text-[var(--muted)]">Actualiza juegos reales, selecciona un partido y genera un analisis explicable.</p>
                )}
              </Panel>
            </section>

            <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
              <Panel title="Tracking de predicciones">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[680px] text-left text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--muted)]">
                        {["Seleccion", "Prob.", "Fair", "Cuota", "Edge", "Resultado", "Accion"].map((head) => <th className="px-3 py-2 font-semibold" key={head}>{head}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {predictionRecords.map((record) => (
                        <tr className="border-b border-[var(--border)] last:border-0" key={record.id}>
                          <td className="px-3 py-2">{record.selection_name}</td>
                          <td className="px-3 py-2">{pct(record.estimated_probability)}</td>
                          <td className="px-3 py-2">{Number(record.fair_odds).toFixed(2)}</td>
                          <td className="px-3 py-2">{record.offered_odds ? Number(record.offered_odds).toFixed(2) : "-"}</td>
                          <td className={Number(record.edge ?? 0) >= 0 ? "px-3 py-2 text-positive" : "px-3 py-2 text-negative"}>{record.edge ? pct(record.edge) : "-"}</td>
                          <td className="px-3 py-2">{record.result ?? "pendiente"}</td>
                          <td className="px-3 py-2">
                            {!record.result ? (
                              <div className="flex flex-wrap gap-2">
                                <button className="mini-btn" disabled={busy} onClick={() => evaluatePrediction(record.id, "win")}>Win</button>
                                <button className="mini-btn" disabled={busy} onClick={() => evaluatePrediction(record.id, "loss")}>Loss</button>
                                <button className="mini-btn" disabled={busy} onClick={() => evaluatePrediction(record.id, "void")}>Void</button>
                              </div>
                            ) : "-"}
                          </td>
                        </tr>
                      ))}
                      {!predictionRecords.length ? <tr><td className="px-3 py-3 text-[var(--muted)]" colSpan={7}>Sin predicciones registradas.</td></tr> : null}
                    </tbody>
                  </table>
                </div>
              </Panel>

              <Panel title="Calibracion y backtesting">
                {backtests[0] ? (
                  <BacktestCard backtest={backtests[0]} />
                ) : (
                  <p className="text-sm text-[var(--muted)]">Evalua predicciones y ejecuta un backtest para medir Brier, calibracion y ROI plano.</p>
                )}
              </Panel>
            </section>

            <section className="grid gap-5 xl:grid-cols-[1fr_1fr]" id="alta manual">
              <Panel title="Banca y sportsbook">
                <form className="form-grid" onSubmit={createBankroll}>
                  <Field label="Nombre" value={bankrollForm.name} onChange={(name) => setBankrollForm({ ...bankrollForm, name })} />
                  <Field label="Moneda" value={bankrollForm.currency} onChange={(currencyValue) => setBankrollForm({ ...bankrollForm, currency: currencyValue.toUpperCase() })} />
                  <Field label="Banca inicial" value={bankrollForm.starting_balance} onChange={(starting_balance) => setBankrollForm({ ...bankrollForm, starting_balance })} />
                  <Field label="Unidad" value={bankrollForm.unit_size} onChange={(unit_size) => setBankrollForm({ ...bankrollForm, unit_size })} />
                  <button className="btn btn-primary" disabled={busy}>Crear banca</button>
                </form>
                <form className="form-grid mt-4" onSubmit={createSportsbook}>
                  <Field label="Casa" value={sportsbookForm.name} onChange={(name) => setSportsbookForm({ ...sportsbookForm, name })} />
                  <Field label="Pais" value={sportsbookForm.country} onChange={(country) => setSportsbookForm({ ...sportsbookForm, country: country.toUpperCase() })} />
                  <button className="btn" disabled={busy}>Crear sportsbook</button>
                </form>
              </Panel>

              <Panel title="Evento, mercado y cuota">
                <form className="form-grid" onSubmit={createEventMarketOdds}>
                  <label className="field">
                    <span>Deporte</span>
                    <select value={eventForm.sport_id} onChange={(e) => setEventForm({ ...eventForm, sport_id: e.target.value })}>
                      <option value="">Seleccionar</option>
                      {sports.map((sport) => <option key={sport.id} value={sport.id}>{sport.name}</option>)}
                    </select>
                  </label>
                  <Field label="Liga" value={eventForm.league_name} onChange={(league_name) => setEventForm({ ...eventForm, league_name })} />
                  <Field label="Local" value={eventForm.home_team} onChange={(home_team) => setEventForm({ ...eventForm, home_team })} />
                  <Field label="Visitante" value={eventForm.away_team} onChange={(away_team) => setEventForm({ ...eventForm, away_team })} />
                  <Field label="Evento" value={eventForm.event_name} onChange={(event_name) => setEventForm({ ...eventForm, event_name })} />
                  <Field label="Inicio ISO" value={eventForm.starts_at} onChange={(starts_at) => setEventForm({ ...eventForm, starts_at })} />
                  <Field label="Mercado" value={marketForm.market_type} onChange={(market_type) => setMarketForm({ ...marketForm, market_type })} />
                  <Field label="Seleccion" value={marketForm.selection_name} onChange={(selection_name) => setMarketForm({ ...marketForm, selection_name })} />
                  <Field label="Linea" value={marketForm.line} onChange={(line) => setMarketForm({ ...marketForm, line })} />
                  <Field label="Cuota decimal" value={oddsForm.decimal_odds} onChange={(decimal_odds) => setOddsForm({ ...oddsForm, decimal_odds })} />
                  <button className="btn btn-primary" disabled={busy}>Guardar cuota</button>
                </form>
              </Panel>
            </section>

            <section className="grid gap-5 xl:grid-cols-[1fr_1fr]" id="evaluacion">
              <Panel title="Evaluar valor">
                <form className="form-grid" onSubmit={createAssessment}>
                  <SelectField label="Evento" value={assessmentForm.event_id} onChange={(event_id) => setAssessmentForm({ ...assessmentForm, event_id })} options={events.map((event) => [event.id, event.event_name])} />
                  <SelectField label="Seleccion" value={assessmentForm.market_selection_id} onChange={(market_selection_id) => setAssessmentForm({ ...assessmentForm, market_selection_id })} options={markets.map((market) => [market.selection.id, `${market.market_type} - ${market.selection.selection_name}`])} />
                  <SelectField label="Cuota" value={assessmentForm.odds_snapshot_id} onChange={(odds_snapshot_id) => setAssessmentForm({ ...assessmentForm, odds_snapshot_id })} options={odds.map((item) => [item.id, `${Number(item.decimal_odds).toFixed(2)} (${pct(item.implied_probability)})`])} />
                  <SelectField label="Banca" value={assessmentForm.bankroll_id} onChange={(bankroll_id) => setAssessmentForm({ ...assessmentForm, bankroll_id })} options={bankrolls.map((bankroll) => [bankroll.id, bankroll.name])} />
                  <Field label="Probabilidad estimada" value={assessmentForm.estimated_probability} onChange={(estimated_probability) => setAssessmentForm({ ...assessmentForm, estimated_probability })} />
                  <button className="btn btn-primary" disabled={busy}>Calcular y guardar EV</button>
                </form>
                {lastAssessment ? <AssessmentCard assessment={lastAssessment} currency={currency} /> : null}
              </Panel>

              <Panel title="Crear apuesta">
                <form className="form-grid" onSubmit={createBet}>
                  <SelectField label="Banca" value={betForm.bankroll_id} onChange={(bankroll_id) => setBetForm({ ...betForm, bankroll_id })} options={bankrolls.map((bankroll) => [bankroll.id, bankroll.name])} />
                  <SelectField label="Sportsbook" value={betForm.sportsbook_id} onChange={(sportsbook_id) => setBetForm({ ...betForm, sportsbook_id })} options={sportsbooks.map((book) => [book.id, book.name])} />
                  <SelectField label="Evento" value={betForm.event_id} onChange={(event_id) => setBetForm({ ...betForm, event_id })} options={events.map((event) => [event.id, event.event_name])} />
                  <SelectField label="Seleccion" value={betForm.market_selection_id} onChange={(market_selection_id) => setBetForm({ ...betForm, market_selection_id })} options={markets.map((market) => [market.selection.id, market.selection.selection_name])} />
                  <Field label="Stake" value={betForm.stake} onChange={(stake) => setBetForm({ ...betForm, stake })} />
                  <Field label="Cuota" value={betForm.odds_at_placement} onChange={(odds_at_placement) => setBetForm({ ...betForm, odds_at_placement })} />
                  <Field label="Probabilidad" value={betForm.estimated_probability_at_placement} onChange={(estimated_probability_at_placement) => setBetForm({ ...betForm, estimated_probability_at_placement })} />
                  <button className="btn btn-primary" disabled={busy}>Crear apuesta</button>
                </form>
              </Panel>
            </section>

            <section className="panel overflow-hidden" id="tickets">
              <div className="panel-header">
                <div>
                  <h3>Apuestas registradas</h3>
                  <p>Liquidacion manual; la banca se actualiza en backend.</p>
                </div>
                <a className="btn" href={`${API_BASE}/exports/bets.csv`}>Exportar CSV</a>
              </div>
              <div className="border-b border-[var(--border)] p-4">
                <div className="form-grid">
                  <label className="field">
                    <span>Estado</span>
                    <select value={betFilters.status} onChange={(event) => setBetFilters({ ...betFilters, status: event.target.value })}>
                      <option value="">Todos</option>
                      <option value="open">Open</option>
                      <option value="win">Win</option>
                      <option value="loss">Loss</option>
                      <option value="void">Void</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>Tipo</span>
                    <select value={betFilters.bet_type} onChange={(event) => setBetFilters({ ...betFilters, bet_type: event.target.value })}>
                      <option value="">Todos</option>
                      <option value="single">Single</option>
                      <option value="parlay">Parlay</option>
                    </select>
                  </label>
                  <SelectField label="Banca" value={betFilters.bankroll_id} onChange={(bankroll_id) => setBetFilters({ ...betFilters, bankroll_id })} options={bankrolls.map((bankroll) => [bankroll.id, bankroll.name])} />
                  <SelectField label="Sportsbook" value={betFilters.sportsbook_id} onChange={(sportsbook_id) => setBetFilters({ ...betFilters, sportsbook_id })} options={sportsbooks.map((book) => [book.id, book.name])} />
                  <label className="field">
                    <span>Desde</span>
                    <input type="date" value={betFilters.date_from} onChange={(event) => setBetFilters({ ...betFilters, date_from: event.target.value })} />
                  </label>
                  <label className="field">
                    <span>Hasta</span>
                    <input type="date" value={betFilters.date_to} onChange={(event) => setBetFilters({ ...betFilters, date_to: event.target.value })} />
                  </label>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button className="btn btn-primary" disabled={busy} onClick={() => refresh()}>Aplicar filtros</button>
                  <button className="btn" disabled={busy} onClick={resetBetFilters}>Limpiar filtros</button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[980px] text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--muted)]">
                      {["Tipo", "Banca", "Casa", "Stake", "Cuota", "Retorno", "P&L", "Estado", "Acciones"].map((head) => <th className="px-4 py-3 font-semibold" key={head}>{head}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {bets.map((bet) => (
                      <tr className="border-b border-[var(--border)] last:border-0" key={bet.id}>
                        <td className="px-4 py-3">{bet.bet_type}</td>
                        <td className="px-4 py-3">{bankrolls.find((bankroll) => bankroll.id === bet.bankroll_id)?.name ?? "-"}</td>
                        <td className="px-4 py-3">{sportsbooks.find((book) => book.id === bet.sportsbook_id)?.name ?? "-"}</td>
                        <td className="px-4 py-3">{money(bet.stake, bet.currency)}</td>
                        <td className="px-4 py-3">{Number(bet.combined_decimal_odds).toFixed(2)}</td>
                        <td className="px-4 py-3">{money(bet.potential_return, bet.currency)}</td>
                        <td className={Number(bet.profit_loss ?? 0) >= 0 ? "px-4 py-3 text-positive" : "px-4 py-3 text-negative"}>{bet.profit_loss ? money(bet.profit_loss, bet.currency) : "-"}</td>
                        <td className="px-4 py-3"><span className={bet.status === "open" ? "badge badge-muted" : "badge"}>{bet.status}</span></td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-2">
                            <button className="mini-btn" disabled={busy} onClick={() => loadBetDetail(bet.id)}>Detalle</button>
                            {bet.status === "open" ? (
                              <>
                              <button className="mini-btn" disabled={busy} onClick={() => settleBet(bet.id, "win")}>Win</button>
                              <button className="mini-btn" disabled={busy} onClick={() => settleBet(bet.id, "loss")}>Loss</button>
                              <button className="mini-btn" disabled={busy} onClick={() => settleBet(bet.id, "void")}>Void</button>
                              </>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!bets.length ? <tr><td className="px-4 py-6 text-[var(--muted)]" colSpan={9}>No hay apuestas creadas con esos filtros.</td></tr> : null}
                  </tbody>
                </table>
              </div>
              {betDetail ? <BetDetailPanel detail={betDetail} currency={currency} onClose={() => setBetDetail(null)} /> : null}
            </section>

            <section className="grid gap-5 xl:grid-cols-[1fr_1fr]" id="importar">
              <Panel title="Importar CSV y captura">
                <form className="form-grid" onSubmit={(event) => uploadFile(event, "/imports/csv/stored", "CSV importado.")}>
                  <label className="field full-span">
                    <span>CSV Triunfobet</span>
                    <input name="file" type="file" accept=".csv,text/csv" />
                  </label>
                  <button className="btn" disabled={busy}>Subir CSV</button>
                </form>
                <form className="form-grid mt-4" onSubmit={(event) => uploadFile(event, "/attachments/screenshots", "Captura recibida.")}>
                  <label className="field full-span">
                    <span>Captura</span>
                    <input name="file" type="file" accept="image/*" />
                  </label>
                  <button className="btn" disabled={busy}>Subir captura</button>
                </form>
              </Panel>

              <Panel title="Autopsia">
                <form className="form-grid" onSubmit={createPostmortem}>
                  <SelectField label="Apuesta" value={postmortemForm.bet_id} onChange={(bet_id) => setPostmortemForm({ ...postmortemForm, bet_id })} options={bets.map((bet) => [bet.id, `${bet.bet_type} ${money(bet.stake, bet.currency)} ${bet.status}`])} />
                  <Field label="Calidad analisis" value={postmortemForm.analysis_quality} onChange={(analysis_quality) => setPostmortemForm({ ...postmortemForm, analysis_quality })} />
                  <Field label="Calidad resultado" value={postmortemForm.result_quality} onChange={(result_quality) => setPostmortemForm({ ...postmortemForm, result_quality })} />
                  <Field label="Motivo principal" value={postmortemForm.primary_failure_reason} onChange={(primary_failure_reason) => setPostmortemForm({ ...postmortemForm, primary_failure_reason })} />
                  <label className="field full-span">
                    <span>Lecciones</span>
                    <textarea value={postmortemForm.lessons} onChange={(event) => setPostmortemForm({ ...postmortemForm, lessons: event.target.value })} />
                  </label>
                  <button className="btn btn-primary" disabled={busy}>Guardar autopsia</button>
                </form>
              </Panel>
            </section>

            <section className="panel overflow-hidden">
              <div className="panel-header">
                <div>
                  <h3>Filas importadas pendientes</h3>
                  <p>Revisa cada fila antes de convertirla en datos reales.</p>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[980px] text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--muted)]">
                      {["Fila", "Estado", "Deporte", "Evento", "Mercado", "Seleccion", "Cuota", "Error", "Accion"].map((head) => (
                        <th className="px-4 py-3 font-semibold" key={head}>{head}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {importRows.map((row) => (
                      <tr className="border-b border-[var(--border)] last:border-0" key={row.id}>
                        <td className="px-4 py-3">{row.row_number}</td>
                        <td className="px-4 py-3"><span className={row.status === "confirmed" ? "badge" : "badge badge-muted"}>{row.status}</span></td>
                        <td className="px-4 py-3">
                          <input
                            className="table-input"
                            disabled={row.status === "confirmed"}
                            value={importValue(row, "sport")}
                            onChange={(event) => updateImportEdit(row.id, "sport", event.target.value)}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            className="table-input"
                            disabled={row.status === "confirmed"}
                            value={importValue(row, "event")}
                            onChange={(event) => updateImportEdit(row.id, "event", event.target.value)}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            className="table-input"
                            disabled={row.status === "confirmed"}
                            value={importValue(row, "market_type")}
                            onChange={(event) => updateImportEdit(row.id, "market_type", event.target.value)}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            className="table-input"
                            disabled={row.status === "confirmed"}
                            value={importValue(row, "selection")}
                            onChange={(event) => updateImportEdit(row.id, "selection", event.target.value)}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            className="table-input w-24"
                            disabled={row.status === "confirmed"}
                            value={importValue(row, "odds")}
                            onChange={(event) => updateImportEdit(row.id, "odds", event.target.value)}
                          />
                        </td>
                        <td className="px-4 py-3 text-negative">{row.error_message ?? "-"}</td>
                        <td className="px-4 py-3">
                          {row.status !== "confirmed" ? (
                            <div className="flex flex-wrap gap-2">
                              <button className="mini-btn" disabled={busy} onClick={() => saveImportRow(row)}>Guardar</button>
                              {row.status === "pending_review" ? (
                                <button className="mini-btn" disabled={busy} onClick={() => confirmImportRow(row.id)}>Confirmar</button>
                              ) : null}
                            </div>
                          ) : "Confirmada"}
                        </td>
                      </tr>
                    ))}
                    {!importRows.length ? (
                      <tr><td className="px-4 py-6 text-[var(--muted)]" colSpan={9}>No hay filas importadas.</td></tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="grid gap-5 xl:grid-cols-[1fr_1fr]" id="analytics">
              <Panel title="Analytics operativo">
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div><dt>Total apuestas</dt><dd>{analytics.total_bets}</dd></div>
                  <div><dt>Liquidadas</dt><dd>{analytics.settled_bets}</dd></div>
                  <div><dt>Stake total</dt><dd>{money(analytics.total_staked, currency)}</dd></div>
                  <div><dt>P&L</dt><dd className={Number(analytics.profit_loss) >= 0 ? "text-positive" : "text-negative"}>{money(analytics.profit_loss, currency)}</dd></div>
                  <div><dt>ROI</dt><dd>{pct(analytics.roi)}</dd></div>
                  <div><dt>Abiertas</dt><dd>{analytics.open_bets}</dd></div>
                </dl>
              </Panel>

              <Panel title="Buckets">
                <div className="space-y-4">
                  <BucketTable title="Por estado" rows={analytics.by_status} currency={currency} />
                  <BucketTable title="Por tipo" rows={analytics.by_bet_type} currency={currency} />
                </div>
              </Panel>
            </section>
              </div>
            </details>
          </div>
        </section>
      </div>
    </main>
  );
}

function SimpleToday({
  busy,
  games,
  lastOddsSync,
  onLoadOddsForGame,
  onPrepareGame,
  onRefresh,
  onScanEvents,
  selectedMarketKeys,
  setSelectedMarketKeys,
  selectedSportKeys,
  setSelectedSportKeys,
  selectedGame,
}: {
  busy: boolean;
  games: SimpleGame[];
  lastOddsSync: SyncJobRun | undefined;
  onLoadOddsForGame: (game: SimpleGame) => void;
  onPrepareGame: (game: SimpleGame) => void;
  onRefresh: () => void;
  onScanEvents: () => void;
  selectedMarketKeys: string[];
  setSelectedMarketKeys: (marketKeys: string[]) => void;
  selectedSportKeys: string[];
  setSelectedSportKeys: (sportKeys: string[]) => void;
  selectedGame: SimpleGame | null;
}) {
  const [dateFilterMode, setDateFilterMode] = useState<DateFilterMode>("today");
  const [decisionFilterMode, setDecisionFilterMode] = useState<DecisionFilterMode>("all");
  const timeFilteredGames = games.filter((game) => isGameInsideDateFilter(game.event.starts_at, dateFilterMode));
  const filteredGames = decisionFilterMode === "all"
    ? timeFilteredGames
    : timeFilteredGames.filter((game) => game.decisionLabel === decisionFilterMode);
  const visibleGames = filteredGames.slice(0, 60);
  const decisionCounts = timeFilteredGames.reduce<Record<DecisionFilterMode, number>>(
    (counts, game) => {
      const label = game.decisionLabel as DecisionFilterMode;
      if (label in counts) counts[label] += 1;
      counts.all += 1;
      return counts;
    },
    { all: 0, "Mejor lectura": 0, Revisar: 0, "Sin ventaja clara": 0, "Faltan cuotas": 0, "Actualizar cuotas": 0 },
  );
  const sportGroups = Array.from(new Set(sportSyncOptions.map((option) => option.group)));
  const selectedSportLabels = sportSyncOptions
    .filter((option) => selectedSportKeys.includes(option.key))
    .map((option) => option.label)
    .join(", ");
  const estimatedSyncCredits = Math.max(1, selectedSportKeys.length) * Math.max(1, selectedMarketKeys.length);
  const selectedMarketLabels = marketSyncOptions
    .filter((option) => selectedMarketKeys.includes(option.key))
    .map((option) => option.label)
    .join(", ");

  function toggleSport(key: string) {
    if (selectedSportKeys.includes(key)) {
      const next = selectedSportKeys.filter((sportKey) => sportKey !== key);
      setSelectedSportKeys(next.length ? next : ["baseball_mlb"]);
      return;
    }
    setSelectedSportKeys([...selectedSportKeys, key]);
  }

  function toggleMarket(key: string) {
    if (selectedMarketKeys.includes(key)) {
      const next = selectedMarketKeys.filter((marketKey) => marketKey !== key);
      setSelectedMarketKeys(next.length ? next : coreMarketKeys);
      return;
    }
    setSelectedMarketKeys([...selectedMarketKeys, key]);
  }

  return (
    <section className="simple-shell" id="hoy">
      <div className="simple-header">
        <div>
          <p className="text-sm font-semibold uppercase text-[var(--muted)]">Modo simple</p>
          <h2>Cartelera</h2>
          <p>Actualiza ligas reales y filtra por hoy, madrugada, proximas horas o toda la cartelera cargada.</p>
        </div>
        <div className="simple-header-actions">
          <button className="btn" disabled={busy} onClick={onScanEvents}>Buscar candidatos</button>
          <button className="btn btn-primary" disabled={busy} onClick={onRefresh}>Actualizar cuotas</button>
        </div>
      </div>

      <div className="sport-sync-panel">
        <div>
          <p className="sport-sync-title">Deportes para sincronizar</p>
          <p className="sport-sync-note">Triunfobet ofrece mas deportes que The Odds API no siempre cubre en vivo; sincroniza primero lo que vayas a evaluar hoy.</p>
          <p>{selectedSportLabels || "MLB"} · ordenados del proximo a empezar hasta el ultimo. Cada liga seleccionada puede consumir creditos.</p>
        </div>
        <p className="sport-sync-note">Mercados: {selectedMarketLabels || "Ganador"} · costo estimado: {estimatedSyncCredits} credito(s).</p>
        <div className="sport-picker">
          <div className="market-sync-box">
            <div>
              <span>Mercados</span>
              <small>Menos mercados = menos creditos</small>
            </div>
            <div className="sport-chip-row">
              {marketSyncOptions.map((option) => (
                <button
                  className={selectedMarketKeys.includes(option.key) ? "sport-chip sport-chip-active" : "sport-chip"}
                  disabled={busy}
                  key={option.key}
                  onClick={() => toggleMarket(option.key)}
                  title={option.note}
                  type="button"
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          <div className="sport-preset-row">
            <button
              className="mini-btn"
              disabled={busy}
              onClick={() => {
                setSelectedSportKeys(["soccer_mexico_ligamx", "soccer_epl", "baseball_mlb", "basketball_wnba"]);
                setSelectedMarketKeys(coreMarketKeys);
              }}
              type="button"
            >
              Ahorro
            </button>
            <button
              className="mini-btn"
              disabled={busy}
              onClick={() => {
                setSelectedSportKeys(triunfobetStyleKeys);
                setSelectedMarketKeys(standardMarketKeys);
              }}
              type="button"
            >
              Triunfobet amplio
            </button>
          <button
            className="mini-btn"
            disabled={busy}
            onClick={() => setSelectedSportKeys(popularSoccerKeys)}
            type="button"
          >
            Futbol top
          </button>
            <button
              className="mini-btn"
              disabled={busy}
              onClick={() => {
                setSelectedSportKeys(popularUsSportKeys);
                setSelectedMarketKeys(coreMarketKeys);
              }}
              type="button"
            >
              USA principales
            </button>
            <button
              className="mini-btn"
              disabled={busy}
              onClick={() => {
                setSelectedSportKeys([...new Set([...popularUsSportKeys, ...popularSoccerKeys])]);
                setSelectedMarketKeys(standardMarketKeys);
              }}
              type="button"
            >
              Todas populares
            </button>
            <button
              className="mini-btn"
              disabled={busy}
              onClick={() => {
                setSelectedSportKeys(sportSyncOptions.map((option) => option.key));
                setSelectedMarketKeys(coreMarketKeys);
              }}
              type="button"
            >
              Todo disponible
            </button>
          </div>
          {sportGroups.map((group) => (
            <div className="sport-group" key={group}>
              <span>{group}</span>
              <div className="sport-chip-row">
                {sportSyncOptions
                  .filter((option) => option.group === group)
                  .map((option) => (
                    <button
                      className={selectedSportKeys.includes(option.key) ? "sport-chip sport-chip-active" : "sport-chip"}
                      disabled={busy}
                      key={option.key}
                      onClick={() => toggleSport(option.key)}
                      type="button"
                    >
                      {option.label}
                    </button>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="simple-stats">
        <div>
          <dt>Juegos en vista</dt>
          <dd>{filteredGames.length}</dd>
        </div>
        <div>
          <dt>Fecha</dt>
          <dd>{dateFilterLabel(dateFilterMode)}</dd>
        </div>
        <div>
          <dt>Total cargados</dt>
          <dd>{games.length}</dd>
        </div>
      </div>

      <div className="date-filter-row" aria-label="Filtro de fecha">
        {[
          ["today", "Hoy"],
          ["tomorrow", "Mañana"],
          ["next24", "24h"],
          ["next48", "48h"],
          ["next7", "7 dias"],
          ["all", "Todos"],
        ].map(([mode, label]) => (
          <button
            className={dateFilterMode === mode ? "date-filter-btn date-filter-active" : "date-filter-btn"}
            key={mode}
            onClick={() => setDateFilterMode(mode as DateFilterMode)}
            type="button"
          >
            {label}
          </button>
        ))}
        <span>Ultima sync: {lastOddsSync ? new Date(lastOddsSync.finished_at ?? lastOddsSync.started_at).toLocaleTimeString("es-VE", { hour: "2-digit", minute: "2-digit" }) : "Sin sync"} · Registros: {lastOddsSync?.records_upserted ?? 0}</span>
        <p>Usa 24h o 48h para incluir partidos de madrugada y ligas de otros paises sin depender solo del calendario local.</p>
      </div>

      <div className="decision-filter-row" aria-label="Filtro de lectura">
        {[
          ["all", "Todos"],
          ["Mejor lectura", "Mejor lectura"],
          ["Revisar", "Revisar"],
          ["Sin ventaja clara", "Sin ventaja clara"],
          ["Faltan cuotas", "Faltan cuotas"],
          ["Actualizar cuotas", "Actualizar cuotas"],
        ].map(([mode, label]) => (
          <button
            className={decisionFilterMode === mode ? "decision-filter-btn decision-filter-active" : "decision-filter-btn"}
            key={mode}
            onClick={() => setDecisionFilterMode(mode as DecisionFilterMode)}
            type="button"
          >
            {label} <span>{decisionCounts[mode as DecisionFilterMode] ?? 0}</span>
          </button>
        ))}
      </div>

      {selectedGame ? <ForecastGamePanel game={selectedGame} /> : null}

      <div className="simple-grid">
        {visibleGames.map((game) => (
          <ForecastGameCard
            game={game}
            isSelected={selectedGame?.event.id === game.event.id}
            key={game.event.id}
            onLoadOdds={onLoadOddsForGame}
            onPrepare={onPrepareGame}
          />
        ))}
        {!visibleGames.length ? (
          <div className="empty-simple">
            <h3>No hay juegos para {dateFilterLabel(dateFilterMode)}</h3>
            <p>Selecciona ligas, presiona Actualizar juegos reales o cambia a Todos para revisar la cartelera completa cargada.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function ForecastGamePanel({ game }: { game: SimpleGame }) {
  const { forecast } = game;

  return (
    <div className="prepared-panel" id="partido-preparado">
      <div>
        <p className="text-sm font-semibold uppercase text-[var(--muted)]">Pronostico de mercado</p>
        <h3>{game.event.event_name}</h3>
        <p>{game.startsLabel} · {game.sportName}</p>
      </div>
      <dl>
        <div>
          <dt>Ganador probable</dt>
          <dd>{forecast.probableWinner} · {probabilityLabel(forecast.winnerProbability)}</dd>
        </div>
        <div>
          <dt>Handicap</dt>
          <dd>{forecast.spread ? `${forecast.spread.label} · ${forecast.spread.decimalOdds.toFixed(2)}` : "Sin handicap"}</dd>
        </div>
        <div>
          <dt>Total puntos</dt>
          <dd>{forecast.total ? `${forecast.total.label} · ${forecast.total.decimalOdds.toFixed(2)}` : "Sin total"}</dd>
        </div>
        <div>
          <dt>Mejor cuota local</dt>
          <dd>{game.bestHome ? `${game.bestHome.decimalOdds.toFixed(2)} en ${game.bestHome.sportsbookName}` : "Sin cuota"}</dd>
        </div>
        <div>
          <dt>Mejor cuota visitante</dt>
          <dd>{game.bestAway ? `${game.bestAway.decimalOdds.toFixed(2)} en ${game.bestAway.sportsbookName}` : "Sin cuota"}</dd>
        </div>
        <div>
          <dt>{game.bestDraw ? "Mejor cuota empate" : "Confianza"}</dt>
          <dd>
            {game.bestDraw
              ? `${game.bestDraw.decimalOdds.toFixed(2)} en ${game.bestDraw.sportsbookName}`
              : `${forecast.confidence} · ${forecast.confidenceReasons.slice(0, 2).join(", ")}`}
          </dd>
        </div>
      </dl>
      <div className="forecast-callout">
        <strong>{forecast.decisionLabel}</strong>
        <p>{forecast.recommendation}</p>
      </div>
      <div className="prepared-next">
        <p>
          Lectura basada en cuotas reales guardadas. No es una garantia: confirma lineups, lesiones y cambios de linea antes de apostar.
        </p>
        <a className="btn" href="#avanzado">Abrir avanzado</a>
      </div>
    </div>
  );
}

function ForecastGameCard({
  game,
  isSelected,
  onLoadOdds,
  onPrepare,
}: {
  game: SimpleGame;
  isSelected: boolean;
  onLoadOdds: (game: SimpleGame) => void;
  onPrepare: (game: SimpleGame) => void;
}) {
  const { forecast } = game;
  const needsOdds = !(game.bestHome && game.bestAway);

  return (
    <article className={isSelected ? "game-card game-card-selected" : "game-card"}>
      <div className="game-card-top">
        <div>
          <p className="game-meta">{game.sportName} · {game.startsLabel}</p>
          <h3>{game.event.event_name}</h3>
        </div>
        <span className={`decision-pill decision-${game.decisionTone}`}>{game.decisionLabel}</span>
      </div>

      <div className="forecast-main">
        <div>
          <span>Ganador probable</span>
          <strong>{forecast.probableWinner}</strong>
          <small>{probabilityLabel(forecast.winnerProbability)} mercado sin margen</small>
        </div>
        <div>
          <span>Confianza</span>
          <strong>{forecast.confidence}</strong>
          <small>{forecast.probabilityGap === null ? "Sin diferencial" : `${Math.round(forecast.probabilityGap * 100)} pts de ventaja`}</small>
        </div>
      </div>

      <dl className="game-lines">
        <div>
          <dt>Moneyline</dt>
          <dd>{forecast.moneylineLean}</dd>
        </div>
        <div>
          <dt>Handicap</dt>
          <dd>{forecast.spread ? forecast.spread.label : "Sin handicap"}</dd>
        </div>
        <div>
          <dt>Total</dt>
          <dd>{forecast.total ? forecast.total.label : "Sin total"}</dd>
        </div>
        <div>
          <dt>Mejores cuotas</dt>
          <dd>
            {game.bestHome ? `${game.event.home_team}: ${game.bestHome.decimalOdds.toFixed(2)}` : "Local sin cuota"}
            {" / "}
            {game.bestAway ? `${game.event.away_team}: ${game.bestAway.decimalOdds.toFixed(2)}` : "Visitante sin cuota"}
            {game.bestDraw ? ` / Empate: ${game.bestDraw.decimalOdds.toFixed(2)}` : ""}
          </dd>
        </div>
      </dl>

      <div className="game-read">
        <p><span>Lectura:</span> {forecast.recommendation}</p>
        <p><span>Cobertura:</span> {game.riskLabel} · {game.sportsbookCount} casas · {game.marketCount} mercados</p>
      </div>

      <div className="game-actions">
        {needsOdds ? (
          <button className="btn btn-primary" onClick={() => onLoadOdds(game)}>Traer cuotas</button>
        ) : (
          <button className="btn" onClick={() => onPrepare(game)}>{isSelected ? "Pronostico abierto" : "Ver pronostico"}</button>
        )}
        <a className="mini-btn" href="#avanzado">Ver avanzado</a>
      </div>
    </article>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function PreparedGamePanel({ game }: { game: SimpleGame }) {
  return (
    <div className="prepared-panel" id="partido-preparado">
      <div>
        <p className="text-sm font-semibold uppercase text-[var(--muted)]">Partido preparado</p>
        <h3>{game.event.event_name}</h3>
        <p>{game.startsLabel} · {game.sportName}</p>
      </div>
      <dl>
        <div>
          <dt>Mejor cuota local</dt>
          <dd>{game.bestHome ? `${game.bestHome.decimalOdds.toFixed(2)} en ${game.bestHome.sportsbookName}` : "Sin cuota"}</dd>
        </div>
        <div>
          <dt>Mejor cuota visitante</dt>
          <dd>{game.bestAway ? `${game.bestAway.decimalOdds.toFixed(2)} en ${game.bestAway.sportsbookName}` : "Sin cuota"}</dd>
        </div>
        <div>
          <dt>Lectura rapida</dt>
          <dd>{game.decisionLabel} · {game.riskLabel}</dd>
        </div>
      </dl>
      <div className="prepared-next">
        <p>
          El partido ya quedó cargado en los formularios avanzados. Para registrar una apuesta,
          abre Avanzado y usa Crear apuesta.
        </p>
        <a className="btn" href="#avanzado">Abrir avanzado</a>
      </div>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function SimpleGameCard({
  game,
  isSelected,
  onPrepare,
}: {
  game: SimpleGame;
  isSelected: boolean;
  onPrepare: (game: SimpleGame) => void;
}) {
  return (
    <article className={isSelected ? "game-card game-card-selected" : "game-card"}>
      <div className="game-card-top">
        <div>
          <p className="game-meta">{game.sportName} · {game.startsLabel}</p>
          <h3>{game.event.event_name}</h3>
        </div>
        <span className={`decision-pill decision-${game.decisionTone}`}>{game.decisionLabel}</span>
      </div>

      <dl className="game-lines">
        <div>
          <dt>{game.event.home_team ?? "Local"}</dt>
          <dd>{game.bestHome ? `${game.bestHome.decimalOdds.toFixed(2)} · ${game.bestHome.sportsbookName}` : "Sin cuota"}</dd>
        </div>
        <div>
          <dt>{game.event.away_team ?? "Visitante"}</dt>
          <dd>{game.bestAway ? `${game.bestAway.decimalOdds.toFixed(2)} · ${game.bestAway.sportsbookName}` : "Sin cuota"}</dd>
        </div>
      </dl>

      <div className="game-read">
        <p><span>Favorito mercado:</span> {game.favorite}</p>
        <p><span>Cobertura:</span> {game.riskLabel} · {game.sportsbookCount} casas · {game.marketCount} mercados</p>
      </div>

      <div className="game-actions">
        <button className="btn" onClick={() => onPrepare(game)}>{isSelected ? "Preparado" : "Preparar análisis"}</button>
        <a className="mini-btn" href="#avanzado">Ver avanzado</a>
      </div>
    </article>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="panel p-4">
      <h3>{title}</h3>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: [string, string][];
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Seleccionar</option>
        {options.map(([id, labelText]) => <option key={id} value={id}>{labelText}</option>)}
      </select>
    </label>
  );
}

function AssessmentCard({ assessment, currency }: { assessment: AssessmentRead; currency: string }) {
  return (
    <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
      <div><dt>Grade</dt><dd>{assessment.grade}</dd></div>
      <div><dt>Score</dt><dd>{assessment.score}</dd></div>
      <div><dt>EV</dt><dd>{pct(assessment.expected_value)}</dd></div>
      <div><dt>Edge</dt><dd>{pct(assessment.edge)}</dd></div>
      <div><dt>Stake</dt><dd>{money(assessment.recommended_stake, currency)}</dd></div>
      <div><dt>Warnings</dt><dd>{assessment.warnings.length}</dd></div>
    </dl>
  );
}

function BetDetailPanel({
  detail,
  currency,
  onClose,
}: {
  detail: BetDetail;
  currency: string;
  onClose: () => void;
}) {
  return (
    <div className="border-t border-[var(--border)] p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h3>Detalle de apuesta</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {detail.sportsbook_name} · {detail.bankroll_name} · {new Date(detail.created_at).toLocaleString("es-VE")}
          </p>
        </div>
        <button className="mini-btn" onClick={onClose}>Cerrar</button>
      </div>

      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3 xl:grid-cols-6">
        <div><dt>Tipo</dt><dd>{detail.bet_type}</dd></div>
        <div><dt>Estado</dt><dd>{detail.status}</dd></div>
        <div><dt>Stake</dt><dd>{money(detail.stake, detail.currency || currency)}</dd></div>
        <div><dt>Cuota</dt><dd>{Number(detail.combined_decimal_odds).toFixed(2)}</dd></div>
        <div><dt>Retorno posible</dt><dd>{money(detail.potential_return, detail.currency || currency)}</dd></div>
        <div><dt>P&L</dt><dd className={Number(detail.profit_loss ?? 0) >= 0 ? "text-positive" : "text-negative"}>{detail.profit_loss ? money(detail.profit_loss, detail.currency || currency) : "-"}</dd></div>
      </dl>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--muted)]">
              {["Evento", "Liga", "Mercado", "Seleccion", "Linea", "Cuota", "Prob.", "EV"].map((head) => <th className="px-3 py-2 font-semibold" key={head}>{head}</th>)}
            </tr>
          </thead>
          <tbody>
            {detail.legs.map((leg) => (
              <tr className="border-b border-[var(--border)] last:border-0" key={leg.id}>
                <td className="px-3 py-2">{leg.event_name}</td>
                <td className="px-3 py-2">{leg.league_name}</td>
                <td className="px-3 py-2">{leg.market_type}</td>
                <td className="px-3 py-2">{leg.selection_name}</td>
                <td className="px-3 py-2">{leg.line_at_placement ?? "-"}</td>
                <td className="px-3 py-2">{Number(leg.odds_at_placement).toFixed(2)}</td>
                <td className="px-3 py-2">{leg.estimated_probability_at_placement ? pct(leg.estimated_probability_at_placement) : "-"}</td>
                <td className="px-3 py-2">{leg.ev_at_placement ? pct(leg.ev_at_placement) : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4">
        <h4 className="text-sm font-semibold">Autopsias</h4>
        <div className="mt-2 grid gap-2">
          {detail.postmortems.map((postmortem) => (
            <div className="detail-note" key={postmortem.id}>
              <p className="font-semibold">{postmortem.analysis_quality}</p>
              <p className="text-sm text-[var(--muted)]">{postmortem.lessons ?? postmortem.primary_failure_reason ?? "Sin notas."}</p>
            </div>
          ))}
          {!detail.postmortems.length ? <p className="text-sm text-[var(--muted)]">Sin autopsias asociadas.</p> : null}
        </div>
      </div>
    </div>
  );
}

function GameAnalysisCard({ analysis }: { analysis: GameAnalysis }) {
  return (
    <div>
      <p className="text-sm text-[var(--muted)]">{analysis.summary}</p>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div><dt>Prob. local</dt><dd>{pct(analysis.estimated_home_probability)}</dd></div>
        <div><dt>Prob. visitante</dt><dd>{pct(analysis.estimated_away_probability)}</dd></div>
        <div><dt>Fair odds local</dt><dd>{Number(analysis.fair_home_odds).toFixed(2)}</dd></div>
        <div><dt>Fair odds visitante</dt><dd>{Number(analysis.fair_away_odds).toFixed(2)}</dd></div>
        <div><dt>Confianza</dt><dd>{pct(analysis.confidence_score)}</dd></div>
        <div><dt>Modelo</dt><dd>{analysis.model_version}</dd></div>
        <div><dt>Edge local</dt><dd className={Number(analysis.home_edge ?? 0) >= 0 ? "text-positive" : "text-negative"}>{analysis.home_edge ? pct(analysis.home_edge) : "-"}</dd></div>
        <div><dt>Edge visitante</dt><dd className={Number(analysis.away_edge ?? 0) >= 0 ? "text-positive" : "text-negative"}>{analysis.away_edge ? pct(analysis.away_edge) : "-"}</dd></div>
      </dl>

      <div className="mt-4 grid gap-3">
        {analysis.factors.map((factor) => (
          <div className="detail-note" key={`${factor.label}-${factor.detail}`}>
            <p className="font-semibold">{factor.label} · {factor.direction}</p>
            <p className="text-sm text-[var(--muted)]">{factor.detail}</p>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <h4 className="text-sm font-semibold">Riesgos</h4>
        <div className="mt-2 grid gap-2">
          {analysis.risks.map((risk) => <div className="risk-alert" key={risk}>{risk}</div>)}
          {!analysis.risks.length ? <p className="text-sm text-[var(--muted)]">Sin riesgos criticos detectados por el modelo.</p> : null}
        </div>
      </div>
    </div>
  );
}

function BacktestCard({ backtest }: { backtest: BacktestRun }) {
  return (
    <div>
      <p className="text-sm text-[var(--muted)]">{backtest.summary}</p>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div><dt>Muestra</dt><dd>{backtest.sample_size}</dd></div>
        <div><dt>Brier</dt><dd>{Number(backtest.brier_score).toFixed(4)}</dd></div>
        <div><dt>Error calib.</dt><dd>{pct(backtest.calibration_error)}</dd></div>
        <div><dt>ROI plano</dt><dd className={Number(backtest.roi_if_flat_bet) >= 0 ? "text-positive" : "text-negative"}>{pct(backtest.roi_if_flat_bet)}</dd></div>
      </dl>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[460px] text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--muted)]">
              {["Bucket", "Pred.", "Prob.", "Win rate", "Error"].map((head) => <th className="px-3 py-2 font-semibold" key={head}>{head}</th>)}
            </tr>
          </thead>
          <tbody>
            {backtest.buckets.map((bucket) => (
              <tr className="border-b border-[var(--border)] last:border-0" key={bucket.bucket}>
                <td className="px-3 py-2">{bucket.bucket}</td>
                <td className="px-3 py-2">{bucket.predictions}</td>
                <td className="px-3 py-2">{pct(bucket.average_probability)}</td>
                <td className="px-3 py-2">{pct(bucket.actual_win_rate)}</td>
                <td className="px-3 py-2">{pct(bucket.calibration_error)}</td>
              </tr>
            ))}
            {!backtest.buckets.length ? <tr><td className="px-3 py-3 text-[var(--muted)]" colSpan={5}>Sin buckets disponibles.</td></tr> : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function BucketTable({
  title,
  rows,
  currency,
}: {
  title: string;
  rows: AnalyticsSummary["by_status"];
  currency: string;
}) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold">{title}</h4>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px] text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-xs uppercase text-[var(--muted)]">
              {["Bucket", "Apuestas", "Stake", "P&L", "ROI"].map((head) => <th className="px-3 py-2 font-semibold" key={head}>{head}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr className="border-b border-[var(--border)] last:border-0" key={row.label}>
                <td className="px-3 py-2">{row.label}</td>
                <td className="px-3 py-2">{row.bets}</td>
                <td className="px-3 py-2">{money(row.stake, currency)}</td>
                <td className={Number(row.profit_loss) >= 0 ? "px-3 py-2 text-positive" : "px-3 py-2 text-negative"}>{money(row.profit_loss, currency)}</td>
                <td className="px-3 py-2">{pct(row.roi)}</td>
              </tr>
            ))}
            {!rows.length ? <tr><td className="px-3 py-3 text-[var(--muted)]" colSpan={5}>Sin datos suficientes.</td></tr> : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
