const localApiBase = "http://127.0.0.1:8000/api/v1";
const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE_URL;

export const API_BASE =
  typeof window !== "undefined" &&
  window.location.hostname !== "localhost" &&
  (configuredApiBase?.includes("127.0.0.1") || configuredApiBase?.includes("localhost"))
    ? "/api/v1"
    : configuredApiBase ??
  (typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? "/api/v1"
    : localApiBase);

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getJson<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function postJson<T>(path: string, body: JsonValue): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function patchJson<T>(path: string, body: JsonValue): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function postForm<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export type Dashboard = {
  bankroll_count: number;
  bankroll_balance: string;
  total_staked: string;
  settled_profit_loss: string;
  roi: string;
  yield_value: string;
  open_bets: number;
  exposure: string;
};

export type AnalyticsBucket = {
  label: string;
  bets: number;
  stake: string;
  profit_loss: string;
  roi: string;
};

export type AnalyticsSummary = {
  total_bets: number;
  open_bets: number;
  settled_bets: number;
  total_staked: string;
  profit_loss: string;
  roi: string;
  yield_value: string;
  by_status: AnalyticsBucket[];
  by_bet_type: AnalyticsBucket[];
};

export type Sport = {
  id: string;
  name: string;
  slug: string;
};

export type Sportsbook = {
  id: string;
  name: string;
  country: string | null;
};

export type Bankroll = {
  id: string;
  name: string;
  currency: string;
  starting_balance: string;
  current_balance: string;
  unit_size: string;
  max_stake_pct: string;
  daily_stop_pct: string;
};

export type BankrollTransaction = {
  id: string;
  bankroll_id: string;
  transaction_type: string;
  amount: string;
  balance_after: string;
  note: string | null;
};

export type SportsbookExposure = {
  sportsbook_id: string;
  sportsbook_name: string;
  open_bets: number;
  settled_bets: number;
  open_exposure: string;
  total_staked: string;
  profit_loss: string;
  roi: string;
};

export type RiskAlert = {
  severity: string;
  code: string;
  message: string;
};

export type BankrollControl = {
  bankrolls: Bankroll[];
  transactions: BankrollTransaction[];
  exposures: SportsbookExposure[];
  alerts: RiskAlert[];
};

export type EventItem = {
  id: string;
  sport_id: string;
  league_name: string;
  home_team: string | null;
  away_team: string | null;
  event_name: string;
  starts_at: string;
  timezone: string;
  venue: string | null;
  status: string;
};

export type Bet = {
  id: string;
  bankroll_id: string;
  sportsbook_id: string;
  bet_type: string;
  stake: string;
  combined_decimal_odds: string;
  potential_return: string;
  actual_return: string | null;
  profit_loss: string | null;
  status: string;
  currency: string;
};

export type BetLegDetail = {
  id: string;
  event_id: string;
  event_name: string;
  league_name: string;
  market_selection_id: string;
  market_type: string;
  selection_name: string;
  odds_at_placement: string;
  line_at_placement: string | null;
  estimated_probability_at_placement: string | null;
  fair_odds_at_placement: string | null;
  ev_at_placement: string | null;
  result: string;
};

export type BetDetail = Bet & {
  bankroll_name: string;
  sportsbook_name: string;
  notes: string | null;
  source: string;
  created_at: string;
  updated_at: string;
  legs: BetLegDetail[];
  postmortems: {
    id: string;
    bet_id: string;
    analysis_quality: string;
    result_quality: string | null;
    process_followed: boolean;
    primary_failure_reason: string | null;
    secondary_failure_reason: string | null;
    lessons: string | null;
    generated_summary: string | null;
    reviewed_by_user: boolean;
  }[];
};

export type MarketRead = {
  id: string;
  event_id: string;
  market_type: string;
  period: string | null;
  participant: string | null;
  line: string | null;
  status: string;
  selection: {
    id: string;
    market_id: string;
    selection_name: string;
    participant: string | null;
  };
};

export type OddsRead = {
  id: string;
  sportsbook_id: string;
  market_selection_id: string;
  decimal_odds: string;
  american_odds: number | null;
  implied_probability: string;
  captured_at: string;
  source: string;
  is_closing_line: boolean;
};

export type TeamStat = {
  id: string;
  sport_id: string;
  team_name: string;
  league_name: string;
  season: string;
  sample_label: string;
  games_played: number;
  wins: number;
  losses: number;
  offensive_rating: string | null;
  defensive_rating: string | null;
  pace: string | null;
  recent_form: string | null;
  home_away_split: string | null;
  rest_days: number | null;
  injury_impact: string | null;
  source: string;
  captured_at: string;
  raw_payload: string | null;
};

export type GameAnalysis = {
  id: string;
  event_id: string;
  generated_at: string;
  model_version: string;
  estimated_home_probability: string;
  estimated_away_probability: string;
  fair_home_odds: string;
  fair_away_odds: string;
  confidence_score: string;
  summary: string;
  factors: {
    label: string;
    direction: string;
    impact: string;
    detail: string;
  }[];
  risks: string[];
  home_edge: string | null;
  away_edge: string | null;
};

export type DataProvider = {
  id: string;
  provider_key: string;
  name: string;
  sport_slug: string | null;
  base_url: string | null;
  api_key_env: string | null;
  status: string;
  last_sync_at: string | null;
  notes: string | null;
};

export type SyncJobRun = {
  id: string;
  provider_key: string;
  job_type: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  records_upserted: number;
  error_message: string | null;
};

export type TheOddsSyncResponse = {
  job: SyncJobRun;
  sports_seen: number;
  events_upserted: number;
  markets_upserted: number;
  odds_inserted: number;
  sportsbooks_upserted: number;
  requests_used: string | null;
  requests_remaining: string | null;
  errors: string[];
  sports: Sport[];
  events: EventItem[];
  markets: MarketRead[];
  odds: OddsRead[];
  sportsbooks: Sportsbook[];
};

export type TheOddsEventsResponse = {
  job: SyncJobRun;
  sports_seen: number;
  events_upserted: number;
  requests_used: string | null;
  requests_remaining: string | null;
  errors: string[];
  sports: Sport[];
  events: EventItem[];
};

export type PredictionRecord = {
  id: string;
  event_id: string;
  analysis_id: string | null;
  market_type: string;
  selection_name: string;
  estimated_probability: string;
  fair_odds: string;
  offered_odds: string | null;
  edge: string | null;
  confidence_score: string;
  result: string | null;
  closing_odds: string | null;
  clv: string | null;
  evaluated_at: string | null;
};

export type BacktestRun = {
  id: string;
  model_version: string;
  started_at: string;
  finished_at: string;
  sample_size: number;
  brier_score: string;
  calibration_error: string;
  roi_if_flat_bet: string;
  summary: string;
  buckets: {
    bucket: string;
    predictions: number;
    average_probability: string;
    actual_win_rate: string;
    calibration_error: string;
  }[];
};

export type AssessmentRead = {
  prediction_id: string;
  value_assessment_id: string;
  grade: string;
  score: number;
  expected_value: string;
  edge: string;
  recommended_stake: string;
  warnings: string[];
};

export type ImportRow = {
  id: string;
  import_id: string;
  row_number: number;
  status: string;
  sport: string | null;
  league: string | null;
  event: string | null;
  home_team: string | null;
  away_team: string | null;
  starts_at: string | null;
  market_type: string | null;
  selection: string | null;
  line: string | null;
  odds: string | null;
  odds_format: string | null;
  sportsbook: string | null;
  captured_at: string | null;
  error_message: string | null;
  created_event_id: string | null;
  created_market_id: string | null;
  created_odds_snapshot_id: string | null;
};
