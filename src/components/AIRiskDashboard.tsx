import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Check,
  Shield,
  Sparkles,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { analyzeAiRisk, getAiRiskCatalog } from "../api";
import type {
  AIRiskAnalysis,
  AIRiskCatalog,
  AIRiskCatalogCareer,
  AIRiskTask,
  CareerTwin,
  SimulationMarketCode,
  WhatIfComparison,
  WhatIfCondition,
  WhatIfScenario,
} from "../types";
import { useJourneyState } from "../state/journeySession";

const CONDITION_CONTROLS: {
  key: WhatIfCondition;
  label: string;
  hint: string;
}[] = [
  { key: "avoid_coding", label: "I want to avoid coding", hint: "Career-fit scores use the same condition in the What-If Simulator." },
  { key: "learn_technical_skills", label: "I am willing to learn technical skills", hint: "Models future learning separately from your saved skills." },
  { key: "increase_ai_adoption", label: "AI adoption increases", hint: "Raises the illustrative AI/task-exposure scenario." },
  { key: "decrease_ai_adoption", label: "AI adoption decreases", hint: "Lowers the illustrative AI/task-exposure scenario." },
  { key: "emerging_skills_important", label: "Emerging skills become more important", hint: "Reprioritizes learning recommendations using the shared What-If setting." },
];

const CATEGORY_INFO = [
  { id: "highly_automatable", title: "Highly automatable / assistable", color: "#c28c51", description: "Higher modeled exposure with lower human-judgment requirements." },
  { id: "ai_augmented", title: "AI-augmented", color: "#728a72", description: "AI may assist, while substantial human judgment remains part of the task." },
  { id: "human_centric", title: "Human-centric", color: "#658398", description: "Lower modeled exposure and a strong need for context, judgment, or communication." },
  { id: "lower_priority", title: "Lower modeled exposure", color: "#a49a83", description: "Tasks with lower modeled exposure and/or lower judgment requirements." },
] as const;

const COMPARE_COLORS = {
  ai_impact_score: "#c28c51",
  automation_exposure: "#a26b75",
  ai_resilience_score: "#55775a",
  skill_change_score: "#6e88a2",
};

function formatDate(value: string, locale: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Unavailable"
    : date.toLocaleDateString(locale, { year: "numeric", month: "long", day: "numeric" });
}

function confidenceLabel(value: number): string {
  if (value >= 0.8) return "High";
  if (value >= 0.55) return "Medium";
  return "Low";
}

function clamp(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function toggleScenarioCondition(
  scenario: WhatIfScenario,
  condition: WhatIfCondition,
): WhatIfScenario {
  const opposites: Partial<Record<WhatIfCondition, WhatIfCondition>> = {
    increase_ai_adoption: "decrease_ai_adoption",
    decrease_ai_adoption: "increase_ai_adoption",
  };
  const enabled = !scenario[condition];
  const opposite = opposites[condition];
  return {
    ...scenario,
    [condition]: enabled,
    ...(enabled && opposite ? { [opposite]: false } : {}),
  };
}

function MetricCard({
  label,
  value,
  description,
  tone,
  delta,
}: {
  label: string;
  value: string;
  description: string;
  tone: string;
  delta?: number;
}) {
  return (
    <article className={`ai-risk-metric ai-risk-metric-${tone}`}>
      <span className="detail-label">{label}</span>
      <strong>{value}</strong>
      <p>{description}</p>
      {delta !== undefined && delta !== 0 && (
        <small className={delta > 0 ? "ai-risk-positive" : "ai-risk-negative"}>
          {delta > 0 ? <ArrowUpRight size={12} /> : <ArrowDown size={12} />}
          {delta > 0 ? "+" : ""}{delta} scenario pts
        </small>
      )}
    </article>
  );
}

function ExposureBar({ task }: { task: AIRiskTask }) {
  return (
    <div className="ai-risk-task-row">
      <div className="ai-risk-task-top">
        <strong>{task.name}</strong>
        <span>{Math.round(task.automation_exposure)}% exposure</span>
      </div>
      <div
        className="ai-risk-progress"
        role="progressbar"
        aria-label={`${task.name} illustrative task exposure`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={task.automation_exposure}
      >
        <span style={{ width: `${clamp(task.automation_exposure)}%` }} />
      </div>
      <div className="ai-risk-task-meta">
        <span>AI assistance {Math.round(task.ai_assistance_potential)}%</span>
        <span>Human judgment {Math.round(task.human_judgment)}%</span>
      </div>
    </div>
  );
}

function CareerCompareChart({ careers }: { careers: AIRiskCatalogCareer[] }) {
  const rows = careers.map((career) => ({
    career: career.career_title,
    ai_impact_score: career.ai_impact_score,
    automation_exposure: career.automation_exposure,
    ai_resilience_score: career.ai_resilience_score,
    skill_change_score: career.skill_change_score,
  }));
  return (
    <div className="ai-risk-compare-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ top: 5, right: 12, bottom: 5, left: 8 }}>
          <CartesianGrid stroke="#eceee8" strokeDasharray="3 4" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} tick={{ fill: "#858a7f", fontSize: 10 }} />
          <YAxis type="category" dataKey="career" width={132} tick={{ fill: "#535a52", fontSize: 10 }} />
          <Tooltip formatter={(value) => [`${value}/100`, "Scenario score"]} />
          <Legend wrapperStyle={{ fontSize: 10 }} />
          <Bar dataKey="ai_impact_score" name="AI impact" fill={COMPARE_COLORS.ai_impact_score} radius={[0, 3, 3, 0]} />
          <Bar dataKey="automation_exposure" name="Task exposure" fill={COMPARE_COLORS.automation_exposure} radius={[0, 3, 3, 0]} />
          <Bar dataKey="ai_resilience_score" name="AI resilience" fill={COMPARE_COLORS.ai_resilience_score} radius={[0, 3, 3, 0]} />
          <Bar dataKey="skill_change_score" name="Skill change" fill={COMPARE_COLORS.skill_change_score} radius={[0, 3, 3, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function AIRiskDashboard({
  careerTwin,
  marketCode,
  dataVersion,
  scenario,
  onScenarioChange,
  whatIfComparison,
}: {
  careerTwin: CareerTwin;
  marketCode: SimulationMarketCode;
  dataVersion: string;
  scenario: WhatIfScenario;
  onScenarioChange: (scenario: WhatIfScenario | ((current: WhatIfScenario) => WhatIfScenario)) => void;
  whatIfComparison: WhatIfComparison | null;
}) {
  const [catalog, setCatalog] = useState<AIRiskCatalog | null>(null);
  const [analysis, setAnalysis] = useState<AIRiskAnalysis | null>(null);
  const [careerId, setCareerId] = useJourneyState("aiRiskCareerId",
    careerTwin.career_options.find((career) => career.id === "product-analyst")?.id
      ?? careerTwin.career_options[0]?.id
      ?? "",
  );
  const [compareIds, setCompareIds] = useJourneyState("aiRiskCompareIds", ["product-analyst", "data-analyst", "business-analyst"]);
  const [selectedTaskName, setSelectedTaskName] = useJourneyState("aiRiskTaskName", "");
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (careerTwin.career_options.length && !careerTwin.career_options.some((career) => career.id === careerId)) {
      setCareerId(careerTwin.career_options.find((career) => career.is_recommended)?.id ?? careerTwin.career_options[0].id);
    }
  }, [careerTwin.career_options, careerId, setCareerId]);

  useEffect(() => {
    let active = true;
    setCatalogLoading(true);
    getAiRiskCatalog(marketCode)
      .then((result) => {
        if (active) setCatalog(result);
      })
      .catch((requestError: unknown) => {
        if (active) setError(requestError instanceof Error ? requestError.message : "We couldn't load AI risk profiles.");
      })
      .finally(() => {
        if (active) setCatalogLoading(false);
      });
    return () => { active = false; };
  }, [marketCode, dataVersion]);

  useEffect(() => {
    if (!careerId) return;
    let active = true;
    setAnalysisLoading(true);
    setAnalysis(null);
    setError(null);
    const timeout = window.setTimeout(() => {
      analyzeAiRisk(careerId, careerTwin.profile.id, marketCode, scenario)
        .then((result) => {
          if (!active) return;
          setAnalysis(result);
          setSelectedTaskName((current) => result.tasks.some((task) => task.name === current)
            ? current
            : result.tasks[0]?.name ?? "");
        })
        .catch((requestError: unknown) => {
          if (active) setError(requestError instanceof Error ? requestError.message : "We couldn't analyze this career's AI risk.");
        })
        .finally(() => {
          if (active) setAnalysisLoading(false);
        });
    }, 120);
    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [careerId, careerTwin.profile.id, marketCode, scenario, dataVersion]);

  const compareCareers = useMemo(
    () => (catalog?.careers ?? []).filter((career) => compareIds.includes(career.career_id)).slice(0, 3),
    [catalog, compareIds],
  );
  const selectedTask = analysis?.tasks.find((task) => task.name === selectedTaskName) ?? null;
  const selectedFit = whatIfComparison?.careers.find((career) => career.career_id === careerId) ?? null;
  const prototypeData = analysis?.scenario_market.data_status === "prototype_illustrative";
  const scenarioShift = analysis
    ? analysis.scenario.ai_impact_score - analysis.baseline.ai_impact_score
    : 0;

  function toggleCompare(career: AIRiskCatalogCareer) {
    setCompareIds((current) => {
      if (current.includes(career.career_id)) {
        return current.filter((id) => id !== career.career_id);
      }
      if (current.length >= 3) return current;
      return [...current, career.career_id];
    });
  }

  return (
    <section className="ai-risk-section" id="ai-risk">
      <div className="dashboard-section-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> AI RISK & SKILL EVOLUTION</div>
          <h2>See how AI could <span className="serif-accent">change the work.</span></h2>
        </div>
        <p>Explore task exposure, skills, opportunities, and resilience for careers in your CareerTwin—not a forecast of job loss.</p>
      </div>

      <div className="ai-risk-disclaimer" role="note">
        <Shield size={17} />
        <p><strong>Scenario-based prototype assessment — not a prediction of job loss or employment outcomes.</strong> {prototypeData && "Market signals are illustrative and are not live labor-market forecasts."}</p>
      </div>

      {catalogLoading && <div className="simulation-loading">Loading career AI-risk profiles…</div>}
      {error && <p className="simulation-error" role="alert"><AlertCircle size={15} /> {error}</p>}

      {catalog && (
        <>
          <div className="ai-risk-select-row">
            <label>
              <span>Career to explore</span>
              <select aria-label="AI risk career" value={careerId} onChange={(event) => setCareerId(event.target.value)}>
                {catalog.careers.map((career) => (
                  <option key={career.career_id} value={career.career_id}>{career.career_title}</option>
                ))}
              </select>
            </label>
            <div className="ai-risk-selected-market">
              <span className="detail-label">SELECTED MARKET</span>
              <strong>{catalog.market.label} · {catalog.market.currency}</strong>
              <small>{catalog.provider}</small>
            </div>
            {analysisLoading && <span className="ai-risk-loading"><span /> Updating scenario…</span>}
          </div>

          {analysis && (
            <div className="ai-risk-results">
              <div className="ai-risk-scenario-banner">
                <div><Sparkles size={15} /><span>Shared What-If conditions</span><small>These are also active in the Career Fit What-If Simulator below.</small></div>
                <div className="ai-risk-condition-controls">
                  {CONDITION_CONTROLS.map((condition) => (
                    <label key={condition.key} title={condition.hint} className={scenario[condition.key] ? "active" : ""}>
                      <input
                        type="checkbox"
                        checked={scenario[condition.key]}
                        onChange={() => onScenarioChange((current) => toggleScenarioCondition(current, condition.key))}
                      />
                      <span>{scenario[condition.key] && <Check size={12} />}</span>
                      {condition.label}
                    </label>
                  ))}
                </div>
              </div>

              <div className="ai-risk-metric-grid">
                <MetricCard
                  label="AI IMPACT"
                  value={`${analysis.scenario.ai_impact_score}/100`}
                  description={`${analysis.scenario.impact_level} modeled impact`}
                  tone="impact"
                  delta={scenarioShift}
                />
                <MetricCard
                  label="TASK EXPOSURE"
                  value={`${Math.round(analysis.scenario.automation_exposure)}%`}
                  description={`${analysis.tasks.length} representative tasks`}
                  tone="exposure"
                  delta={analysis.scenario.automation_exposure - analysis.baseline.automation_exposure}
                />
                <MetricCard
                  label="AI RESILIENCE"
                  value={`${analysis.scenario.ai_resilience_score}/100`}
                  description="Relative resilience to automation"
                  tone="resilience"
                  delta={analysis.scenario.ai_resilience_score - analysis.baseline.ai_resilience_score}
                />
                <MetricCard
                  label="SKILL CHANGE"
                  value={`${analysis.scenario.skill_change_score}/100`}
                  description="Modeled pace of skill evolution"
                  tone="skills"
                />
                <MetricCard
                  label="AI OPPORTUNITY"
                  value={`${analysis.scenario.opportunity_score}/100`}
                  description="Potential for AI-assisted work"
                  tone="opportunity"
                />
              </div>

              <div className="ai-risk-market-strip">
                <div><span className="detail-label">MARKET SIGNAL</span><strong>{analysis.scenario_market.job_demand} demand · {analysis.scenario_market.demand_trend}</strong></div>
                <div><span className="detail-label">SOURCE / STATUS</span><strong>{analysis.scenario_market.data_status === "prototype_illustrative" ? "Illustrative prototype" : analysis.scenario_market.data_status.replace("_", " ")}</strong><small>{analysis.scenario_market.data_source}</small></div>
                <div><span className="detail-label">CONFIDENCE</span><strong>{confidenceLabel(analysis.scenario_market.data_confidence)}</strong><small>{Math.round(analysis.scenario_market.data_confidence * 100)}% provider metadata</small></div>
                <div><span className="detail-label">LAST UPDATED</span><strong>{formatDate(analysis.scenario_market.last_updated, catalog.market.locale)}</strong></div>
              </div>

              {selectedFit && (
                <div className="ai-risk-fit-comparison">
                  <div><span className="detail-label">CAREER FIT · SAME WHAT-IF SCENARIO</span><strong>{selectedFit.career_title}</strong></div>
                  <span><small>BEFORE</small><b>{selectedFit.baseline_score}</b></span>
                  <ArrowRight size={15} />
                  <span><small>AFTER</small><b>{selectedFit.scenario_score}</b></span>
                  <p>{selectedFit.score_effects.length
                    ? selectedFit.score_effects.map((effect) => `${effect.label}: ${effect.points > 0 ? "+" : ""}${effect.points} pts`).join(" · ")
                    : "No Career Fit conditions are active."}</p>
                </div>
              )}

              <div className="ai-risk-section-heading">
                <div><span className="detail-label">TASK-LEVEL VIEW</span><h3>How AI may transform {analysis.career.title}</h3></div>
                <span>Tasks can change independently; a career is not simply “safe” or “unsafe.”</span>
              </div>

              <div className="ai-risk-task-grid">
                <article className="ai-risk-panel ai-risk-task-list">
                  <h4>Representative tasks</h4>
                  <div>{analysis.tasks.map((task) => <ExposureBar key={task.name} task={task} />)}</div>
                </article>
                <article className="ai-risk-panel ai-risk-matrix-panel">
                  <h4>AI risk matrix</h4>
                  <p>Bubble size reflects future task importance. Select a bubble or task to read its explanation.</p>
                  <div className="ai-risk-matrix">
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart margin={{ top: 12, right: 10, bottom: 23, left: 0 }}>
                        <CartesianGrid stroke="#eceee8" strokeDasharray="3 4" />
                        <XAxis type="number" dataKey="automation_exposure" domain={[0, 100]} tick={{ fill: "#858a7f", fontSize: 9 }} label={{ value: "Automation exposure", position: "insideBottom", offset: -15, fontSize: 10 }} />
                        <YAxis type="number" dataKey="human_judgment" domain={[0, 100]} tick={{ fill: "#858a7f", fontSize: 9 }} width={35} label={{ value: "Human judgment", angle: -90, position: "insideLeft", fontSize: 10 }} />
                        <ZAxis type="number" dataKey="future_importance" range={[70, 180]} />
                        <ReferenceLine x={60} stroke="#b9c1b6" strokeDasharray="4 4" />
                        <ReferenceLine y={60} stroke="#b9c1b6" strokeDasharray="4 4" />
                        <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                        <Scatter
                          data={analysis.tasks}
                          name="Career tasks"
                          onClick={(entry: { payload?: unknown }) => {
                            const point = entry.payload;
                            if (
                              point
                              && typeof point === "object"
                              && "name" in point
                              && typeof point.name === "string"
                            ) {
                              setSelectedTaskName(point.name);
                            }
                          }}
                        >
                          {analysis.tasks.map((task) => {
                            const category = CATEGORY_INFO.find((item) => item.id === task.category);
                            return <Cell key={task.name} fill={category?.color ?? "#55775a"} stroke={selectedTaskName === task.name ? "#20231f" : "#fff"} strokeWidth={selectedTaskName === task.name ? 2 : 1} />;
                          })}
                        </Scatter>
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="ai-risk-matrix-legend">
                    {CATEGORY_INFO.map((item) => <span key={item.id}><i style={{ background: item.color }} />{item.title}</span>)}
                  </div>
                  {selectedTask && <p className="ai-risk-task-explanation"><strong>{selectedTask.name}:</strong> {selectedTask.explanation}</p>}
                </article>
              </div>

              <div className="ai-risk-section-heading">
                <div><span className="detail-label">RESPONSIBILITY SHIFTS</span><h3>How the task mix could evolve</h3></div>
              </div>
              <div className="ai-risk-transformation-grid">
                {CATEGORY_INFO.map((category) => {
                  const tasks = analysis.tasks.filter((task) => task.category === category.id);
                  return (
                    <article className="ai-risk-panel" key={category.id}>
                      <span className="ai-risk-category-dot" style={{ background: category.color }} />
                      <h4>{category.title}</h4>
                      <p>{category.description}</p>
                      {tasks.length
                        ? <ul>{tasks.map((task) => <li key={task.name}>{task.name}</li>)}</ul>
                        : <small>No tasks currently fall in this illustrative group.</small>}
                    </article>
                  );
                })}
              </div>

              <div className="ai-risk-detail-grid">
                <article className="ai-risk-panel">
                  <div className="ai-risk-panel-title"><Sparkles size={15} /><h3>Skills becoming more important</h3></div>
                  <div className="ai-risk-chip-list">{analysis.future_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
                </article>
                <article className="ai-risk-panel">
                  <div className="ai-risk-panel-title"><Shield size={15} /><h3>Relatively resilient to automation</h3></div>
                  <p>These skill areas involve judgment, context, accountability, or human interaction; they are not “AI-proof.”</p>
                  <div className="ai-risk-chip-list">{analysis.resilient_skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
                </article>
              </div>

              <div className="ai-risk-detail-grid">
                <article className="ai-risk-panel ai-risk-positive-panel">
                  <h3>How AI could help this career</h3>
                  <ul>{analysis.opportunities.map((item) => <li key={item}>{item}</li>)}</ul>
                </article>
                <article className="ai-risk-panel ai-risk-caution-panel">
                  <h3>Potential AI-driven changes</h3>
                  <ul>{analysis.risks.map((item) => <li key={item}>{item}</li>)}</ul>
                  <p>These describe possible changes to tasks and expectations—not job elimination.</p>
                </article>
              </div>

              <div className="ai-risk-detail-grid">
                <article className="ai-risk-panel ai-risk-readiness-panel">
                  <div className="ai-risk-readiness-heading">
                    <div><span className="detail-label">PERSONALIZED TO {careerTwin.profile.name.toUpperCase()}</span><h3>Your AI readiness</h3></div>
                    <strong>{analysis.readiness.scenario_score}<small>/100</small></strong>
                  </div>
                  <div className="ai-risk-readiness-track"><span style={{ width: `${analysis.readiness.scenario_score}%` }} /></div>
                  <p>{analysis.readiness.explanation}</p>
                  {analysis.readiness.assumed_skills.length > 0 && (
                    <p className="ai-risk-assumption-note">Scenario-only learning assumptions: {analysis.readiness.assumed_skills.join(" · ")}.</p>
                  )}
                  <div className="ai-risk-readiness-columns">
                    <div><h4>Profile signals already reflected</h4>{analysis.readiness.strengths.length ? <ul>{analysis.readiness.strengths.map((item) => <li key={item}>{item}</li>)}</ul> : <small>No direct matches in the saved skill tags yet.</small>}</div>
                    <div><h4>Skills to explore</h4>{analysis.readiness.gaps.length ? <ul>{analysis.readiness.gaps.map((item) => { const evidence = analysis.readiness.skill_evidence.find(skill => skill.label === item); return <li key={item}>{item}{evidence && <> · {evidence.current_rating}/5 now, {evidence.required_rating}/5 target (gap {evidence.gap})</>}</li>; })}</ul> : <small>No configured future-skill gaps in this scenario.</small>}</div>
                  </div>
                </article>
                <article className="ai-risk-panel">
                  <h3>What you could learn next</h3>
                  <ol className="ai-risk-learning-list">
                    {analysis.readiness.learn_next.map((item, index) => <li key={item}><span>{index + 1}</span>{item}</li>)}
                  </ol>
                  <p className="ai-risk-score-explanation">{analysis.scenario.resilience_explanation}</p>
                </article>
              </div>

              <div className="ai-risk-compare-panel ai-risk-panel">
                <div className="ai-risk-section-heading">
                  <div><span className="detail-label">COMPARE OPTIONS · UP TO 3</span><h3>Different careers, different task mixes</h3></div>
                  <p>No universal winner—the trade-offs depend on what you value.</p>
                </div>
                <div className="ai-risk-compare-selectors">
                  {catalog.careers.map((career) => {
                    const checked = compareIds.includes(career.career_id);
                    return (
                      <label key={career.career_id} className={checked ? "selected" : ""}>
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={!checked && compareIds.length >= 3}
                          onChange={() => toggleCompare(career)}
                        />
                        <span>{checked && <Check size={11} />}</span>
                        {career.career_title}
                      </label>
                    );
                  })}
                </div>
                <CareerCompareChart careers={compareCareers} />
                {compareCareers.length >= 2 && (
                  <p className="ai-risk-compare-explanation">
                    {compareCareers[0].career_title} currently has {compareCareers[0].automation_exposure < compareCareers[1].automation_exposure ? "lower modeled task exposure" : "higher modeled task exposure"} than {compareCareers[1].career_title} in this illustrative dataset. Compare the skill and task details rather than treating one score as a universal recommendation.
                  </p>
                )}
              </div>

              <div className="ai-risk-assumptions">
                <span className="detail-label">SCENARIO NOTES</span>
                <ul>{analysis.scenario_effects.map((item) => <li key={item}>{item}</li>)}</ul>
                <details><summary>About this assessment</summary><ul>{analysis.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></details>
                <span>Market data: {analysis.scenario_market.data_status === "prototype_illustrative" ? "Prototype / illustrative" : analysis.scenario_market.data_status.replace("_", " ")} · Confidence: {confidenceLabel(analysis.scenario_market.data_confidence)} · Last updated: {formatDate(analysis.scenario_market.last_updated, catalog.market.locale)}</span>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
