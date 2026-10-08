import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertCircle, ArrowDown, ArrowRight, ArrowUp, Check, RotateCcw, Sparkles } from "lucide-react";
import { runWhatIf } from "../api";
import { useJourneyState } from "../state/journeySession";
import { createDefaultWhatIfScenario } from "../data/whatIfScenario";
import type {
  CareerTwin,
  SimulationMarketCode,
  WhatIfCareerResult,
  WhatIfComparison,
  WhatIfCondition,
  WhatIfScenario,
} from "../types";

const CONDITIONS: {
  key: WhatIfCondition;
  label: string;
  description: string;
  group: "preferences" | "commitments" | "market";
}[] = [
  { key: "avoid_coding", label: "I don't want coding", description: "Prefer paths that don't list coding as a relevant skill.", group: "preferences" },
  { key: "higher_salary", label: "I want higher salary", description: "Give more fit credit to paths tagged for earning potential.", group: "preferences" },
  { key: "work_life_balance", label: "Work-life balance matters most", description: "Favor paths tagged for work-life balance.", group: "preferences" },
  { key: "remote_work", label: "I want remote work", description: "Favor remote-ready paths in the local career data.", group: "preferences" },
  { key: "international_opportunities", label: "I want international opportunities", description: "Favor paths tagged for international opportunities.", group: "preferences" },
  { key: "willing_mba", label: "I'm willing to do an MBA", description: "Include a sample MBA-oriented management route where available.", group: "commitments" },
  { key: "learn_technical_skills", label: "I'm willing to learn technical skills", description: "Give more fit credit to paths with technical or analytical skill requirements.", group: "commitments" },
  { key: "faster_growth", label: "I want faster career growth", description: "Favor growth-tagged paths and model an illustrative one-year acceleration.", group: "commitments" },
  { key: "increase_demand", label: "Demand increases", description: "Raise the illustrative career demand index by 15 points.", group: "market" },
  { key: "decrease_demand", label: "Demand decreases", description: "Lower the illustrative career demand index by 15 points.", group: "market" },
  { key: "increase_ai_adoption", label: "AI adoption increases", description: "Raise the illustrative automation-exposure index by 15 points.", group: "market" },
  { key: "decrease_ai_adoption", label: "AI adoption decreases", description: "Lower the illustrative automation-exposure index by 15 points.", group: "market" },
  { key: "increase_salary_growth", label: "Salary growth increases", description: "Add 2 percentage points to the illustrative annual growth assumption.", group: "market" },
  { key: "decrease_salary_growth", label: "Salary growth decreases", description: "Subtract 2 percentage points from the illustrative annual growth assumption.", group: "market" },
  { key: "emerging_skills_important", label: "New skills become more important", description: "Increase the emerging-skill match weight from 10% to 25% of market alignment.", group: "market" },
];

const PATH_COLORS = ["#55775a", "#c28c51", "#6e88a2", "#a26b75", "#8672a0", "#558e8a", "#a17c55"];

function formatFit(score: number): string {
  return `${Math.round(score)}`;
}

function ScoreDelta({ change }: { change: number }) {
  if (change === 0) return <span className="whatif-delta whatif-delta-neutral">No change</span>;
  return (
    <span className={`whatif-delta ${change > 0 ? "whatif-delta-up" : "whatif-delta-down"}`}>
      {change > 0 ? <ArrowUp size={13} /> : <ArrowDown size={13} />}
      {change > 0 ? "+" : ""}{change} pts
    </span>
  );
}

function ScenarioCareerCard({
  result,
  color,
  expanded,
  onToggle,
}: {
  result: WhatIfCareerResult;
  color: string;
  expanded: boolean;
  onToggle: () => void;
}) {
  const baselineRoles = result.baseline_simulation.stages;
  const scenarioRoles = result.scenario_simulation.stages;
  return (
    <article className={`whatif-career-card ${expanded ? "whatif-career-card-expanded" : ""}`}>
      <button
        className="whatif-career-summary"
        type="button"
        aria-expanded={expanded}
        onClick={onToggle}
      >
        <span className="whatif-career-dot" style={{ background: color }} />
        <span className="whatif-career-name">
          <strong>{result.career_title}</strong>
          <small>{result.category}</small>
        </span>
        <span className="whatif-score-before">
          <small>BEFORE</small><strong>{formatFit(result.baseline_score)}</strong>
        </span>
        <ArrowRight size={14} className="whatif-score-arrow" />
        <span className="whatif-score-after">
          <small>AFTER</small><strong>{formatFit(result.scenario_score)}</strong>
        </span>
        <ScoreDelta change={result.score_change} />
      </button>
      <p className="whatif-trajectory-summary">{result.trajectory_explanation}</p>
      {expanded && (
        <div className="whatif-career-details">
          <div className="whatif-effects">
            <span className="detail-label">WHY THE SCORE CHANGED</span>
            {result.score_effects.length ? result.score_effects.map((effect) => (
              <div className="whatif-effect" key={effect.condition}>
                <strong>{effect.points > 0 ? "+" : ""}{effect.points} pts · {effect.label}</strong>
                <span>{effect.explanation}</span>
              </div>
            )) : (
              <p>No scenario conditions are active, so this career retains its baseline score.</p>
            )}
            <div className="whatif-score-basis">
              {(() => {
                const adjustment = result.score_effects.reduce((sum, effect) => sum + effect.points, 0);
                const rawScore = result.baseline_score + adjustment;
                return <>Before {result.baseline_score} + scenario adjustments {adjustment > 0 ? "+" : ""}{adjustment} = after {result.scenario_score}{rawScore !== result.scenario_score && " (bounded to 0–100)"}</>;
              })()}
            </div>
          </div>
          <div className="whatif-role-comparison">
            <span className="detail-label">MARKET SIGNALS · BEFORE VS AFTER</span>
            <div className="whatif-market-metrics">
              <div><span>Demand</span><strong>{result.baseline_market.job_demand} {result.baseline_market.demand_index} → {result.scenario_market.job_demand} {result.scenario_market.demand_index}</strong></div>
              <div><span>AI exposure</span><strong>{Math.round(result.baseline_market.automation_exposure)}% → {Math.round(result.scenario_market.automation_exposure)}%</strong></div>
              <div><span>Salary growth</span><strong>{result.baseline_market.salary_growth_rate}% → {result.scenario_market.salary_growth_rate}%</strong></div>
              <div><span>Market alignment</span><strong>{result.baseline_market_score} → {result.scenario_market_score} / 100</strong></div>
            </div>
            <div className="whatif-skill-gap">
              <strong>Emerging skill gap</strong>
              <span>{result.scenario_skill_gap.length ? result.scenario_skill_gap.join(" · ") : "No tagged emerging-skill gaps in the saved profile."}</span>
            </div>
            <span className="detail-label whatif-role-label">ROLE PATH · BEFORE VS AFTER</span>
            {baselineRoles.map((stage, index) => {
              const nextStage = scenarioRoles[index];
              return (
                <div className="whatif-role-row" key={`${stage.year}-${stage.role}`}>
                  <span>Stage {index + 1}</span>
                  <div>
                    <span>Before · Year {stage.year} · {stage.role}</span>
                    {nextStage && <strong>After · Year {nextStage.year} · {nextStage.role}</strong>}
                  </div>
                </div>
              );
            })}
            <p>{result.trajectory_explanation}</p>
          </div>
        </div>
      )}
    </article>
  );
}

type WhatIfChartPoint = {
  year: number;
  before: number;
  after: number;
  beforeLow: number;
  beforeHigh: number;
  afterLow: number;
  afterHigh: number;
  beforeRole: string;
  afterRole: string;
};

function WhatIfChartTooltip({
  active,
  label,
  payload,
  currency,
  marketCode,
}: {
  active?: boolean;
  label?: string | number;
  payload?: WhatIfChartPoint[];
  currency: string;
  marketCode: SimulationMarketCode;
}) {
  if (!active || !payload?.[0]) return null;
  const point = payload[0];
  const format = (value: number) => marketCode === "IN"
    ? `₹${value.toFixed(1)}L`
    : new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
  return (
    <div className="salary-tooltip">
      <span className="detail-label">YEAR {label}</span>
      <div className="whatif-chart-tooltip-line"><i className="whatif-before-swatch" /> Before · {point.beforeRole}</div>
      <div className="whatif-chart-tooltip-range">{format(point.beforeLow)}–{format(point.beforeHigh)} / year</div>
      <div className="whatif-chart-tooltip-line"><i className="whatif-after-swatch" /> After · {point.afterRole}</div>
      <div className="whatif-chart-tooltip-range">{format(point.afterLow)}–{format(point.afterHigh)} / year</div>
    </div>
  );
}

function CareerTrajectoryChart({
  result,
  marketCode,
  currency,
}: {
  result: WhatIfCareerResult;
  marketCode: SimulationMarketCode;
  currency: string;
}) {
  const rows: WhatIfChartPoint[] = result.baseline_simulation.years.map((before) => {
    const after = result.scenario_simulation.years[before.year];
    return {
      year: before.year,
      before: before.salary_mid,
      after: after.salary_mid,
      beforeLow: before.salary_low,
      beforeHigh: before.salary_high,
      afterLow: after.salary_low,
      afterHigh: after.salary_high,
      beforeRole: before.role,
      afterRole: after.role,
    };
  });
  const formatter = (value: number) => marketCode === "IN"
    ? `₹${value}L`
    : new Intl.NumberFormat("en-US", { style: "currency", currency, notation: "compact", maximumFractionDigits: 0 }).format(value);
  return (
    <div className="whatif-chart-frame">
      <div className="whatif-chart-legend">
        <span><i className="whatif-before-swatch" /> Before</span>
        <span><i className="whatif-after-swatch" /> After</span>
        <small>Lines show salary midpoints; hover for ranges and roles.</small>
      </div>
      <div className="whatif-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
            <CartesianGrid stroke="#eceee8" strokeDasharray="3 5" vertical={false} />
            <XAxis
              dataKey="year"
              axisLine={{ stroke: "#e1e5dd" }}
              tick={{ fill: "#858b82", fontSize: 9 }}
              tickLine={false}
              tickFormatter={(year: number) => year === 0 ? "Start" : `Y${year}`}
            />
            <YAxis
              axisLine={false}
              domain={["auto", "auto"]}
              tick={{ fill: "#858b82", fontSize: 9 }}
              tickFormatter={formatter}
              tickLine={false}
              width={55}
            />
            <Tooltip
              content={(props) => (
                <WhatIfChartTooltip
                  active={props.active}
                  currency={currency}
                  label={props.label}
                  marketCode={marketCode}
                  payload={props.payload?.map((item) => item.payload as WhatIfChartPoint)}
                />
              )}
              cursor={{ stroke: "#abb6a8", strokeDasharray: "3 3" }}
            />
            <Line dataKey="before" name="Before" dot={false} isAnimationActive={false} stroke="#9aa197" strokeDasharray="5 4" strokeWidth={2} type="monotone" />
            <Line dataKey="after" name="After" dot={false} isAnimationActive={false} stroke="#4e7052" strokeWidth={2.7} type="monotone" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function WhatIfSimulator({
  careerTwin,
  marketCode,
  dataVersion,
  scenario,
  onScenarioChange,
  onComparisonChange,
}: {
  careerTwin: CareerTwin;
  marketCode: SimulationMarketCode;
  dataVersion: string;
  scenario: WhatIfScenario;
  onScenarioChange: (scenario: WhatIfScenario | ((current: WhatIfScenario) => WhatIfScenario)) => void;
  onComparisonChange: (comparison: WhatIfComparison | null) => void;
}) {
  const [comparison, setComparison] = useState<WhatIfComparison | null>(null);
  const [selectedCareerId, setSelectedCareerId] = useJourneyState("whatIfCareerId", careerTwin.recommended_careers[0]?.id ?? "");
  const [expandedCareerIds, setExpandedCareerIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!careerTwin.career_options.some((career) => career.id === selectedCareerId)) {
      setSelectedCareerId(careerTwin.recommended_careers[0]?.id ?? careerTwin.career_options[0]?.id ?? "");
    }
  }, [careerTwin.career_options, careerTwin.recommended_careers, selectedCareerId, setSelectedCareerId]);

  useEffect(() => {
    let active = true;
    setComparison(null);
    onComparisonChange(null);
    setLoading(true);
    setError(null);
    const timeout = window.setTimeout(() => {
      runWhatIf(careerTwin.profile.id, scenario, marketCode)
        .then((response) => {
          if (!active) return;
          setComparison(response);
          onComparisonChange(response);
        })
        .catch((requestError: unknown) => {
          if (active) setError(requestError instanceof Error ? requestError.message : "We couldn't calculate this scenario.");
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }, 180);
    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [careerTwin.profile.id, marketCode, scenario, dataVersion, onComparisonChange]);

  const selectedResult = comparison?.careers.find((career) => career.career_id === selectedCareerId) ?? null;
  const enabledCount = CONDITIONS.filter((condition) => scenario[condition.key]).length;
  const preferenceConditions = CONDITIONS.filter((condition) => condition.group === "preferences");
  const commitmentConditions = CONDITIONS.filter((condition) => condition.group === "commitments");
  const marketConditions = CONDITIONS.filter((condition) => condition.group === "market");
  const topMovers = useMemo(
    () => [...(comparison?.careers ?? [])]
      .filter((career) => career.score_change !== 0)
      .sort((left, right) => Math.abs(right.score_change) - Math.abs(left.score_change) || left.career_title.localeCompare(right.career_title))
      .slice(0, 3),
    [comparison],
  );

  function toggleCondition(condition: WhatIfCondition) {
    const opposites: Partial<Record<WhatIfCondition, WhatIfCondition>> = {
      increase_demand: "decrease_demand",
      decrease_demand: "increase_demand",
      increase_ai_adoption: "decrease_ai_adoption",
      decrease_ai_adoption: "increase_ai_adoption",
      increase_salary_growth: "decrease_salary_growth",
      decrease_salary_growth: "increase_salary_growth",
    };
    onScenarioChange((current) => {
      const turningOn = !current[condition];
      const opposite = opposites[condition];
      return {
        ...current,
        [condition]: turningOn,
        ...(turningOn && opposite ? { [opposite]: false } : {}),
      };
    });
  }

  function resetScenario() {
    onScenarioChange(createDefaultWhatIfScenario());
    setExpandedCareerIds([]);
  }

  function toggleExpanded(careerId: string) {
    setExpandedCareerIds((current) => current.includes(careerId)
      ? current.filter((id) => id !== careerId)
      : [...current, careerId]);
  }

  return (
    <section className="whatif-section" id="what-if">
      <div className="dashboard-section-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> CHANGE THE ASSUMPTIONS</div>
          <h2>What if your priorities <span className="serif-accent">changed?</span></h2>
        </div>
        <p>Try a different version of your future. Your saved profile stays untouched while the fit and sample paths recalculate.</p>
      </div>

      <div className="whatif-condition-panel">
        <div className="whatif-panel-heading">
          <div><span className="detail-label">YOUR WHAT-IF CONDITIONS</span><p>Select any conditions to explore together.</p></div>
          <button className="whatif-reset" type="button" onClick={resetScenario} disabled={enabledCount === 0}>
            <RotateCcw size={13} /> Reset
          </button>
        </div>
        <div className="whatif-condition-groups">
          {[{ title: "What you prioritize", conditions: preferenceConditions }, { title: "What you're open to", conditions: commitmentConditions }, { title: "What changes in the market", conditions: marketConditions }].map((group) => (
            <div className="whatif-condition-group" key={group.title}>
              <h3>{group.title}</h3>
              {group.conditions.map((condition) => (
                <label className={`whatif-condition ${scenario[condition.key] ? "whatif-condition-active" : ""}`} key={condition.key}>
                  <input
                    type="checkbox"
                    checked={scenario[condition.key]}
                    onChange={() => toggleCondition(condition.key)}
                  />
                  <span className="whatif-condition-check">{scenario[condition.key] && <Check size={12} />}</span>
                  <span className="whatif-condition-copy">
                    <strong>{condition.label}</strong>
                    <small>{condition.description}</small>
                  </span>
                </label>
              ))}
            </div>
          ))}
        </div>
        <div className="whatif-panel-footer">
          <span><Sparkles size={14} /> {enabledCount === 0 ? "Start with your saved profile as the baseline." : `${enabledCount} what-if condition${enabledCount === 1 ? "" : "s"} selected.`}</span>
          {loading && <span className="whatif-recalculating"><span /> Recalculating…</span>}
        </div>
      </div>

      {error && <p className="simulation-error" role="alert"><AlertCircle size={15} /> {error}</p>}

      {comparison && (
        <>
          <div className="whatif-results-heading">
            <div>
              <span className="detail-label">BEFORE VS AFTER · {comparison.market.label.toUpperCase()} MARKET</span>
              <h3>{enabledCount ? "Your scenario results" : "Your starting baseline"}</h3>
            </div>
            <span className="whatif-score-legend"><i /> Before <ArrowRight size={12} /> <b /> After</span>
          </div>

          {topMovers.some((career) => career.score_change !== 0) && <div className="whatif-mover-strip">
            {topMovers.map((career, index) => (
              <button
                className="whatif-mover"
                key={career.career_id}
                type="button"
                onClick={() => {
                  setSelectedCareerId(career.career_id);
                  document.getElementById("whatif-trajectory")?.scrollIntoView({ behavior: "smooth", block: "center" });
                }}
              >
                <span>{index === 0 ? (career.score_change > 0 ? "BIGGEST LIFT" : "BIGGEST DIP") : index === 1 ? "NEXT SHIFT" : "ALSO SHIFTS"}</span>
                <strong>{career.career_title}</strong>
                <ScoreDelta change={career.score_change} />
              </button>
            ))}
          </div>}

          <div className="whatif-career-list">
            {comparison.careers.map((career) => (
              <ScenarioCareerCard
                color={PATH_COLORS[comparison.careers.indexOf(career) % PATH_COLORS.length]}
                expanded={expandedCareerIds.includes(career.career_id)}
                key={career.career_id}
                onToggle={() => toggleExpanded(career.career_id)}
                result={career}
              />
            ))}
          </div>

          {selectedResult && (
            <div className="whatif-trajectory" id="whatif-trajectory">
              <div className="whatif-trajectory-heading">
                <div>
                  <span className="detail-label">TRAJECTORY COMPARISON</span>
                  <h3>Before vs after, year by year</h3>
                </div>
                <label>
                  <span className="sr-only">Career trajectory to view</span>
                  <select
                    aria-label="Career trajectory to view"
                    value={selectedCareerId}
                    onChange={(event) => setSelectedCareerId(event.target.value)}
                  >
                    {comparison.careers.map((career) => (
                      <option key={career.career_id} value={career.career_id}>{career.career_title}</option>
                    ))}
                  </select>
                </label>
              </div>
              <p className="whatif-trajectory-explanation">{selectedResult.trajectory_explanation}</p>
              <CareerTrajectoryChart
                currency={comparison.market.currency}
                marketCode={marketCode}
                result={selectedResult}
              />
              <div className="whatif-year-comparison">
                {selectedResult.baseline_simulation.years.filter((point) => point.year === 0 || point.year === 2 || point.year === 4 || point.year === 7 || point.year === 10).map((before) => {
                  const after = selectedResult.scenario_simulation.years[before.year];
                  return (
                    <article key={before.year}>
                      <span>YEAR {before.year}</span>
                      <strong>{before.role}</strong>
                      {before.role !== after.role && <b><ArrowRight size={11} /> {after.role}</b>}
                      <small>{marketCode === "IN" ? `₹${before.salary_low}–${before.salary_high}L` : `$${Math.round(before.salary_low).toLocaleString()}–$${Math.round(before.salary_high).toLocaleString()}`}</small>
                      {(before.salary_low !== after.salary_low || before.salary_high !== after.salary_high) && (
                        <small className="whatif-after-range">{marketCode === "IN" ? `After: ₹${after.salary_low}–${after.salary_high}L` : `After: $${Math.round(after.salary_low).toLocaleString()}–$${Math.round(after.salary_high).toLocaleString()}`}</small>
                      )}
                    </article>
                  );
                })}
              </div>
            </div>
          )}

          <div className="whatif-method-note">
            <AlertCircle size={15} />
            <div><strong>Read the model, not a promise.</strong><p>{comparison.score_basis} {comparison.trajectory_basis} Salary estimates remain illustrative local sample data, not guaranteed outcomes. The simulator does not edit your saved profile.</p></div>
          </div>
        </>
      )}
    </section>
  );
}
