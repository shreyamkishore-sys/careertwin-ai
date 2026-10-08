import { useEffect, useState } from "react";
import { AlertCircle, ArrowDownRight, ArrowRight, ArrowUpRight, BarChart3, RefreshCw, ShieldAlert, TrendingUp } from "lucide-react";
import { getMarketIntelligence, getMarkets } from "../api";
import type { MarketCatalogEntry, MarketCode, MarketIntelligence, MarketRefreshResult } from "../types";

function formatSalary(
  value: number,
  market: MarketCatalogEntry,
): string {
  if (market.code === "IN") return `₹${value.toFixed(1)}L`;
  return new Intl.NumberFormat(market.locale, {
    style: "currency",
    currency: market.currency,
    notation: "compact",
    maximumFractionDigits: 0,
  }).format(value);
}

function displayDate(value: string, locale: string): string {
  const normalizedValue = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`;
  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(normalizedValue));
}

function Trend({ value }: { value: string }) {
  const isRising = value === "rising";
  const isFalling = value === "declining";
  return (
    <span className={`market-trend market-trend-${value}`}>
      {isRising ? <ArrowUpRight size={12} /> : isFalling ? <ArrowDownRight size={12} /> : <span className="market-trend-neutral" />}
      {value}
    </span>
  );
}

function statusLabel(status?: MarketIntelligence["data_status"]): string {
  if (status === "live_verified") return "LIVE / VERIFIED SOURCE";
  if (status === "reviewed_dataset") return "REVIEWED DATASET";
  return "ILLUSTRATIVE PROTOTYPE DATA";
}

export function LaborMarketIntelligence({
  marketCode,
  onMarketChange,
  marketRefreshing,
  onDemoMarketUpdate,
  dataVersion,
}: {
  marketCode: "IN" | "US";
  onMarketChange: (market: "IN" | "US") => void;
  marketRefreshing: boolean;
  onDemoMarketUpdate: (market: "IN" | "US", careerId: string, action?: "apply" | "reset") => Promise<MarketRefreshResult | null>;
  dataVersion: string;
}) {
  const [markets, setMarkets] = useState<MarketCatalogEntry[]>([]);
  const [intelligence, setIntelligence] = useState<MarketIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshResult, setRefreshResult] = useState<MarketRefreshResult | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setIntelligence(null);
    Promise.all([getMarkets(), getMarketIntelligence(marketCode)])
      .then(([catalog, data]) => {
        if (!active) return;
        setMarkets(catalog.markets);
        setIntelligence(data);
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : "We couldn't load labor-market signals.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [marketCode, dataVersion]);

  async function refreshDemoRecord(action: "apply" | "reset") {
    const result = await onDemoMarketUpdate(marketCode, "product-analyst", action);
    if (result) setRefreshResult(result);
  }

  const market = intelligence?.market;
  const careers = intelligence?.careers ?? [];
  return (
    <section className="market-intelligence-section" id="labor-market">
      <div className="dashboard-section-heading market-intelligence-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> DYNAMIC LABOR MARKET INTELLIGENCE</div>
          <h2>Read the market, <span className="serif-accent">not a crystal ball.</span></h2>
        </div>
        <p>CareerTwin is designed to use updated labor-market signals and scenario modeling to explore possible career trajectories—not to predict an exact future.</p>
      </div>

      <div className="market-status-panel">
        <div className="market-status-copy">
          <span className="market-status-badge"><ShieldAlert size={13} /> {statusLabel(intelligence?.data_status)}</span>
          <p>{intelligence?.description ?? "Demonstration data only. No job-posting feed, labor-market API, or automatic update is connected."}</p>
        </div>
        <div className="market-status-meta">
          <label className="market-selector">
            <span>Market / country</span>
            <select
              aria-label="Labor market country"
              value={marketCode}
              onChange={(event) => {
                const selected = event.target.value as MarketCode;
                if (selected === "IN" || selected === "US") onMarketChange(selected);
              }}
            >
              {markets.map((item) => (
                <option disabled={!item.available} key={item.code} value={item.code}>
                  {item.flag} {item.label} · {item.currency}{item.available ? "" : " · data not configured"}
                </option>
              ))}
            </select>
          </label>
          <div className="market-last-updated">
            <span className="detail-label">MARKET DATA LAST UPDATED</span>
            <strong>{market ? displayDate(intelligence?.last_updated ?? "", market.locale) : "—"}</strong>
          </div>
          {marketRefreshing && <span className="market-refreshing"><RefreshCw size={12} /> Recalculating fit…</span>}
          <button className="button button-outline market-refresh-button" type="button" onClick={() => void refreshDemoRecord("apply")} disabled={marketRefreshing || loading}>
            <RefreshCw size={14} /> Run demo market update
          </button>
          {careers.find((career) => career.career_id === "product-analyst")?.data_source.includes("local demo update") && (
            <button className="button button-outline market-refresh-button" type="button" onClick={() => void refreshDemoRecord("reset")} disabled={marketRefreshing || loading}>
              Reset demo data
            </button>
          )}
        </div>
      </div>

      <div className="market-provenance-legend" aria-label="Market data status definitions">
        <strong>Data-status guide:</strong> Illustrative prototype = synthetic local demo data (current); Reviewed dataset = source-reviewed data (not connected); Live/verified = live external source with provenance (not connected).
      </div>

      {refreshResult && refreshResult.market.code === marketCode && (
        <section className="market-update-result" aria-live="polite">
          <div className="eyebrow"><span className="eyebrow-dot" /> {refreshResult.action === "apply" ? "BEFORE VS AFTER MARKET UPDATE" : "DEMO DATA RESET"}</div>
          <h3>{refreshResult.career_id.replace(/-/g, " ")}</h3>
          <div className="market-update-comparison">
            <div><span>BEFORE MARKET UPDATE</span><strong>Demand: {refreshResult.before_demand}</strong><small>Career fit: {refreshResult.before_fit_score} · rank #{refreshResult.before_rank}</small></div>
            <ArrowRight size={18} aria-hidden="true" />
            <div><span>AFTER MARKET UPDATE</span><strong>Demand: {refreshResult.after_demand}</strong><small>Career fit: {refreshResult.after_fit_score} · rank #{refreshResult.after_rank}</small></div>
          </div>
          <h4>Why did it change?</h4>
          <p>{refreshResult.explanation}</p>
          <ul>{refreshResult.changed_factors.map((factor) => <li key={factor}>{factor}</li>)}</ul>
          <small>Local demonstration update · no external or real-time data source.</small>
        </section>
      )}

      {error && <p className="simulation-error" role="alert"><AlertCircle size={15} /> {error}</p>}
      {loading && <div className="simulation-loading"><RefreshCw size={16} /> Loading illustrative market signals…</div>}
      {!loading && !error && intelligence && market && (
        <>
          <div className="market-overview-strip">
            <div><span>MARKET GROWTH SIGNAL</span><strong>{careers.length ? (careers.reduce((sum, career) => sum + career.market_growth, 0) / careers.length).toFixed(1) : "—"}%</strong><small>sample average · illustrative</small></div>
            <div><span>CAREER PATHS</span><strong>{careers.length}</strong><small>local demonstration records</small></div>
            <div><span>DATA CONFIDENCE</span><strong>{careers.length ? `${Math.round(careers.reduce((sum, career) => sum + career.data_confidence, 0) / careers.length * 100)}%` : "—"}</strong><small>{intelligence.data_status === "prototype_illustrative" ? "synthetic prototype values · low confidence" : "reported by provider"}</small></div>
            <div><span>DATA PROVIDER</span><strong>{intelligence.provider}</strong><small>replaceable MarketDataProvider</small></div>
          </div>
          <div className="market-career-grid" aria-label={`${market.label} career demand index chart`}>
            {careers.map((career) => (
              <article className="market-career-card" key={career.career_id}>
                <div className="market-career-heading">
                  <div><span className="detail-label">{career.career_id.replace(/-/g, " ").toUpperCase()}</span><h3>{career.career_id.split("-").map((word) => word[0].toUpperCase() + word.slice(1)).join(" ")}</h3></div>
                  <span className={`market-demand-pill market-demand-${career.job_demand.toLowerCase()}`}>{career.job_demand} demand</span>
                </div>
                <div className="market-demand-chart">
                  <div className="market-demand-chart-label"><span><BarChart3 size={12} /> Demand index</span><strong>{Math.round(career.demand_index)} / 100</strong></div>
                  <div className="market-demand-track" role="progressbar" aria-label={`${career.career_id} illustrative demand index`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={career.demand_index}>
                    <span style={{ width: `${career.demand_index}%` }} />
                  </div>
                </div>
                <div className="market-career-metrics">
                  <div><span>DEMAND TREND</span><Trend value={career.demand_trend} /></div>
                  <div><span>STARTING SALARY RANGE</span><strong>{formatSalary(career.salary_low, market)}–{formatSalary(career.salary_high, market)} / yr</strong></div>
                  <div><span>SALARY GROWTH</span><strong><TrendingUp size={12} /> {career.salary_growth_rate}% scenario rate</strong></div>
                  <div><span>AI IMPACT</span><strong className={`ai-impact-${career.ai_impact}`}>{career.ai_impact} · {Math.round(career.automation_exposure)}% exposure</strong></div>
                  <div><span>HIRING TREND</span><Trend value={career.hiring_trend} /></div>
                  <div><span>MARKET GROWTH</span><strong>{career.market_growth}% scenario rate</strong></div>
                </div>
                <div className="market-skill-list">
                  <span>EMERGING SKILLS</span>
                  <div>{career.emerging_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
                </div>
                <div className="market-skill-list market-skill-list-declining">
                  <span>SKILLS IN TRANSITION</span>
                  <div>{career.declining_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
                </div>
                <details className="market-geography">
                  <summary>Geographic demand &amp; transition</summary>
                  <div>{Object.entries(career.geographic_demand).map(([place, level]) => <span key={place}>{place} · {level}</span>)}</div>
                  <p>Possible transition: {career.possible_transition}</p>
                </details>
                <footer className="market-career-data-foot">
                  <span>{career.currency} · {career.data_source} · confidence {Math.round(career.data_confidence * 100)}% · illustrative</span>
                  <span>Updated {displayDate(career.last_updated, market.locale)}</span>
                </footer>
              </article>
            ))}
          </div>
          <p className="market-intelligence-note"><AlertCircle size={14} />{intelligence.description} Salary figures use {market.unit} and are illustrative scenario-based estimates, not sourced facts or guaranteed outcomes.</p>
        </>
      )}
    </section>
  );
}
