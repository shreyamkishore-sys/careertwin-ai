import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Check,
  Compass,
  GraduationCap,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { runCareerSwitch } from "../api";
import type {
  Career,
  CareerSwitchAnalysis,
  CareerSwitchRequest,
  SimulationMarketCode,
  TransitionLearningOption,
} from "../types";
import { useJourneyState, type CareerSwitchSession } from "../state/journeySession";

const LEARNING_OPTIONS: { value: TransitionLearningOption; label: string }[] = [
  { value: "sql", label: "SQL" },
  { value: "python", label: "Python" },
  { value: "product_strategy", label: "Product strategy" },
  { value: "roadmapping", label: "Roadmapping" },
  { value: "stakeholder_management", label: "Stakeholder management" },
  { value: "user_research", label: "User research" },
  { value: "communication", label: "Communication" },
];

const SWITCH_YEARS: CareerSwitchRequest["years_before_switch"][] = [0, 1, 2, 3, 5];

function salary(value: number, currency: string, market: SimulationMarketCode): string {
  if (market === "IN") return `₹${value.toFixed(1)}L`;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 0,
  }).format(value);
}

function skillHeading(status: string): string {
  if (status === "ready") return "You already have";
  if (status === "assumed") return "Assumed for this scenario";
  if (status === "partially_transferable") return "Partially transferable";
  return "You need to develop";
}

function SkillList({ title, skills }: { title: string; skills: CareerSwitchAnalysis["transferable_skills"] }) {
  return (
    <section className="switch-skill-group">
      <h4>{title} <span>{skills.length}</span></h4>
      {skills.length ? (
        <ul>{skills.map((item) => (
          <li key={item.label}>
            <Check size={13} />
            <span><strong>{item.label}</strong>{item.evidence.length > 0 && <small>{item.evidence.join(" · ")}</small>}</span>
          </li>
        ))}</ul>
      ) : <p>No skill areas in this group for the selected profile and route.</p>}
    </section>
  );
}

function MarketCard({ title, market }: { title: string; market: CareerSwitchAnalysis["target_market"] }) {
  return (
    <article className="switch-market-card">
      <span className="detail-label">{title}</span>
      <strong>{market.job_demand} demand · {market.demand_trend}</strong>
      <span>AI impact: {market.ai_impact} · {Math.round(market.automation_exposure)}% exposure</span>
      <span>Salary growth: {market.salary_growth_rate}% scenario rate</span>
      <div>{market.emerging_skills.map((skill) => <small key={skill}>{skill}</small>)}</div>
    </article>
  );
}

export function CareerSwitchSimulator({
  careers,
  profileId,
  marketCode,
  dataVersion,
}: {
  careers: Career[];
  profileId: number;
  marketCode: SimulationMarketCode;
  dataVersion: string;
}) {
  const selectableCareers = useMemo(() => [...careers].sort((left, right) => left.title.localeCompare(right.title)), [careers]);
  const defaultCurrent = selectableCareers.find((career) => career.id === "data-analyst")?.id ?? selectableCareers[0]?.id ?? "";
  const defaultTarget = selectableCareers.find((career) => career.id === "product-manager")?.id
    ?? selectableCareers.find((career) => career.id !== defaultCurrent)?.id ?? "";
  const [switchInputs, setSwitchInputs] = useJourneyState("careerSwitch", () => ({
    currentId: defaultCurrent, targetId: defaultTarget, switchYear: 0 as CareerSwitchRequest["years_before_switch"],
    learnedSkills: [] as TransitionLearningOption[], willingEducation: false, willingMba: false,
    demandChange: "none" as const, aiChange: "none" as const,
  }));
  const { currentId, targetId, switchYear, learnedSkills, willingEducation, willingMba, demandChange, aiChange } = switchInputs;
  const updateSwitchInputs = (patch: Partial<CareerSwitchSession>) => setSwitchInputs((current) => ({ ...current, ...patch }));
  const [analysis, setAnalysis] = useState<CareerSwitchAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const analysisRequestId = useRef(0);

  useEffect(() => {
    analysisRequestId.current += 1;
    setAnalysis(null);
    setError(null);
    setLoading(false);
  }, [currentId, targetId, switchYear, learnedSkills, willingEducation, willingMba, demandChange, aiChange, marketCode, profileId, dataVersion]);

  function toggleLearningSkill(skill: TransitionLearningOption) {
    updateSwitchInputs({ learnedSkills: learnedSkills.includes(skill)
      ? learnedSkills.filter((item) => item !== skill)
      : [...learnedSkills, skill] });
  }

  async function simulate() {
    const requestId = ++analysisRequestId.current;
    setLoading(true);
    setError(null);
    try {
      const result = await runCareerSwitch({
        profile_id: profileId,
        current_career_id: currentId,
        target_career_id: targetId,
        market: marketCode,
        years_before_switch: switchYear,
        willing_additional_education: willingEducation,
        learned_skills: learnedSkills,
        what_if: {
          avoid_coding: false,
          higher_salary: false,
          work_life_balance: false,
          remote_work: false,
          international_opportunities: false,
          willing_mba: willingMba,
          learn_technical_skills: false,
          faster_growth: false,
          increase_demand: demandChange === "up",
          decrease_demand: demandChange === "down",
          increase_ai_adoption: aiChange === "up",
          decrease_ai_adoption: aiChange === "down",
          increase_salary_growth: false,
          decrease_salary_growth: false,
          emerging_skills_important: false,
        },
      });
      if (requestId === analysisRequestId.current) setAnalysis(result);
    } catch (requestError) {
      if (requestId === analysisRequestId.current) {
        setError(requestError instanceof Error ? requestError.message : "We couldn't calculate this transition scenario.");
        setAnalysis(null);
      }
    } finally {
      if (requestId === analysisRequestId.current) setLoading(false);
    }
  }

  const chartData = useMemo(() => analysis?.stayed_salary.map((point, index) => ({
    year: point.year,
    stayed: point.salary_mid,
    switched: analysis.switched_salary[index]?.salary_mid ?? point.salary_mid,
  })) ?? [], [analysis]);

  return (
    <section className="career-switch-section" id="career-switch">
      <div className="dashboard-section-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> CAREER SWITCHING SIMULATOR</div>
          <h2>Explore how your career could <span className="serif-accent">evolve if you switch paths.</span></h2>
        </div>
        <p>Model a possible transition using your saved profile, configured routes, and the selected market. This is decision support—not a guarantee.</p>
      </div>

      <div className="career-switch-controls">
        <label>
          <span>Current career</span>
          <select value={currentId} onChange={(event) => updateSwitchInputs({ currentId: event.target.value })}>
            {selectableCareers.map((career) => <option key={career.id} value={career.id}>{career.title}</option>)}
          </select>
        </label>
        <ArrowDown className="switch-control-arrow" size={18} aria-hidden="true" />
        <label>
          <span>Target career</span>
          <select value={targetId} onChange={(event) => updateSwitchInputs({ targetId: event.target.value })}>
            {selectableCareers.map((career) => <option key={career.id} value={career.id}>{career.title}</option>)}
          </select>
        </label>
        <label>
          <span>When do you want to switch?</span>
          <select value={switchYear} onChange={(event) => updateSwitchInputs({ switchYear: Number(event.target.value) as CareerSwitchRequest["years_before_switch"] })}>
            {SWITCH_YEARS.map((year) => <option key={year} value={year}>{year === 0 ? "Immediately" : `After ${year} year${year === 1 ? "" : "s"}`}</option>)}
          </select>
        </label>
      </div>

      <div className="career-switch-assumptions">
        <div>
          <span className="detail-label">WHAT IF YOU BUILD THESE SKILLS?</span>
          <div className="switch-learning-options">
            {LEARNING_OPTIONS.map((item) => (
              <label key={item.value}>
                <input type="checkbox" checked={learnedSkills.includes(item.value)} onChange={() => toggleLearningSkill(item.value)} />
                <span>{item.label}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="switch-whatif-options">
          <label><input type="checkbox" checked={willingMba} onChange={(event) => updateSwitchInputs({ willingMba: event.target.checked })} /> Consider an MBA</label>
          <label><input type="checkbox" checked={willingEducation} onChange={(event) => updateSwitchInputs({ willingEducation: event.target.checked })} /> Open to additional education</label>
          <label>Target demand
            <select value={demandChange} onChange={(event) => updateSwitchInputs({ demandChange: event.target.value as typeof demandChange })}>
              <option value="none">No change</option><option value="up">Increases</option><option value="down">Decreases</option>
            </select>
          </label>
          <label>AI adoption
            <select value={aiChange} onChange={(event) => updateSwitchInputs({ aiChange: event.target.value as typeof aiChange })}>
              <option value="none">No change</option><option value="up">Increases</option><option value="down">Decreases</option>
            </select>
          </label>
        </div>
        <button type="button" className="button button-dark" onClick={() => void simulate()} disabled={loading || !currentId || !targetId || currentId === targetId}>
          {loading ? <><RefreshCw size={15} className="switch-spinner" /> Simulating…</> : <><Compass size={15} /> Simulate career switch</>}
        </button>
      </div>

      {error && <p className="simulation-error" role="alert"><AlertCircle size={15} /> {error}</p>}
      {!analysis && !loading && !error && (
        <div className="switch-empty-state">
          <Sparkles size={18} />
          <p>Choose a current and target career, adjust assumptions if you like, then simulate a possible route.</p>
        </div>
      )}
      {analysis && (
        <div className="career-switch-results" key={`${analysis.current_career.id}-${analysis.target_career.id}-${analysis.market.code}-${dataVersion}`}>
          <div className="switch-summary-grid">
            <article className="switch-path-card">
              <span className="detail-label">POSSIBLE CAREER PATH · {analysis.market.label}</span>
              <div className="switch-route-graph">
                {analysis.route.map((career, index) => (
                  <div className="switch-route-node" key={`${career.id}-${index}`}>
                    <span>{index === 0 ? "CURRENT" : index === analysis.route.length - 1 ? "TARGET" : "INTERMEDIATE ROLE"}</span>
                    <strong>{career.title}</strong>
                    {index < analysis.route.length - 1 && <ArrowDown size={15} aria-hidden="true" />}
                  </div>
                ))}
              </div>
              {analysis.alternative_routes.length > 0 && (
                <details className="switch-alternatives">
                  <summary>See {analysis.alternative_routes.length} alternative supported route{analysis.alternative_routes.length === 1 ? "" : "s"}</summary>
                  {analysis.alternative_routes.map((route, index) => <p key={index}>{route.map((career) => career.title).join(" → ")}</p>)}
                </details>
              )}
            </article>
            <article className={`switch-difficulty-card switch-difficulty-${analysis.transition_difficulty.toLowerCase()}`}>
              <span className="detail-label">TRANSITION DIFFICULTY</span>
              <strong>{analysis.transition_difficulty}</strong>
              <div className="switch-difficulty-meter" role="progressbar" aria-label="Illustrative transition difficulty" aria-valuemin={0} aria-valuemax={100} aria-valuenow={analysis.difficulty_score}><span style={{ width: `${analysis.difficulty_score}%` }} /></div>
              <span>{analysis.difficulty_score}/100 illustrative score · {analysis.experience_relevance.toLowerCase()} experience relevance</span>
              <p>{analysis.difficulty_explanation}</p>
              <details className="switch-difficulty-breakdown">
                <summary>How the score is built</summary>
                <div>
                  <span>Target skill gaps <b>{analysis.difficulty_factors.skill_gap}%</b></span>
                  <span>Skill overlap <b>{analysis.difficulty_factors.skill_overlap}%</b></span>
                  <span>Experience relevance <b>{analysis.difficulty_factors.experience_relevance}%</b></span>
                  <span>Target entry barrier <b>{analysis.difficulty_factors.target_entry_barrier}%</b></span>
                  <span>Market demand risk <b>{analysis.difficulty_factors.market_demand_risk}%</b></span>
                </div>
              </details>
              <small>Preparation: {analysis.preparation_min_months}–{analysis.preparation_max_months} months · illustrative estimate</small>
            </article>
          </div>

          <div className="switch-detail-grid">
            <article className="switch-panel">
              <div className="switch-panel-heading"><h3>Skill overlap</h3><strong>{analysis.skill_overlap}%</strong></div>
              <p>Deterministic overlap: 70% profile signals and explicitly assumed learning (direct matches count fully, related signals count partly) + 30% current-career skill coverage. Assumed learning is shown separately from skills already in your profile; profile lists do not store proficiency levels.</p>
              <div className="switch-skill-groups">
                <SkillList title={skillHeading("ready")} skills={analysis.transferable_skills} />
                <SkillList title={skillHeading("assumed")} skills={analysis.assumed_skills} />
                <SkillList title={skillHeading("partially_transferable")} skills={analysis.partially_transferable_skills} />
                <SkillList title={skillHeading("to_develop")} skills={analysis.skills_to_develop} />
              </div>
            </article>
            <article className="switch-panel">
              <div className="switch-panel-heading"><h3>Illustrative preparation timeline</h3><span>{analysis.preparation_min_months}–{analysis.preparation_max_months} months</span></div>
              <p>Timing depends on learning time, work opportunities, and prior experience. It is not guaranteed.</p>
              <ol className="switch-roadmap">
                {analysis.roadmap.map((stage, index) => (
                  <li key={stage.title}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <div><strong>{stage.title}</strong><small>Months {stage.minimum_month}–{stage.maximum_month}</small><p>{stage.description}</p></div>
                  </li>
                ))}
              </ol>
            </article>
          </div>

          <div className="switch-detail-grid">
            <article className="switch-panel switch-trajectory-panel">
              <div className="switch-panel-heading"><h3>Stay vs switch salary scenario</h3><span>{analysis.market.unit}</span></div>
              <p>Illustrative scenario-based estimate · salary ranges reuse CareerTwin’s existing career simulations.</p>
              <div className="switch-chart-legend"><span><i /> If you stay</span><span><i /> If you switch</span></div>
              <div className="switch-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 12, right: 12, left: 4, bottom: 0 }}>
                    <CartesianGrid stroke="#eceee8" strokeDasharray="3 4" vertical={false} />
                    <XAxis dataKey="year" tickFormatter={(year: number) => `Year ${year}`} tick={{ fill: "#858a7f", fontSize: 10 }} />
                    <YAxis tickFormatter={(value: number) => salary(value, analysis.market.currency, marketCode)} tick={{ fill: "#858a7f", fontSize: 9 }} width={68} />
                    <Tooltip labelFormatter={(year) => `Year ${year}`} formatter={(value, name) => [salary(Number(value), analysis.market.currency, marketCode), name === "stayed" ? "Stay" : "Switch"]} />
                    <Line type="monotone" dataKey="stayed" name="stayed" stroke="#6d8768" strokeWidth={2.5} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="switched" name="switched" stroke="#c08e57" strokeWidth={2.5} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="switch-salary-table">
                {analysis.stayed_salary.map((point, index) => {
                  const switched = analysis.switched_salary[index];
                  return <div key={point.year}>
                    <strong>Year {point.year}</strong><span>{point.role}<small>{salary(point.salary_low, analysis.market.currency, marketCode)}–{salary(point.salary_high, analysis.market.currency, marketCode)}</small></span>
                    <ArrowRight size={13} />
                    <span>{switched.role}<small>{salary(switched.salary_low, analysis.market.currency, marketCode)}–{salary(switched.salary_high, analysis.market.currency, marketCode)}</small></span>
                  </div>;
                })}
              </div>
            </article>
            <article className="switch-panel">
              <div className="switch-panel-heading"><h3>Market impact</h3><span>{analysis.market.label} · {analysis.market.currency}</span></div>
              <span className="switch-illustrative-badge">{analysis.data_status === "prototype_illustrative" ? "ILLUSTRATIVE PROTOTYPE MARKET DATA" : analysis.data_status.replace("_", " ").toUpperCase()}</span>
              <div className="switch-market-grid">
                <MarketCard title={`CURRENT · ${analysis.current_career.title}`} market={analysis.current_market} />
                <MarketCard title={`TARGET · ${analysis.target_career.title}`} market={analysis.target_market} />
              </div>
              <div className="switch-education-note"><GraduationCap size={17} /><p><strong>Education guidance</strong>{analysis.education_guidance}</p></div>
              <div className="switch-responsibilities"><strong>Role focus</strong><p><b>Current:</b> {analysis.current_responsibilities}</p><p><b>Target:</b> {analysis.target_responsibilities}</p><p><b>Management scope:</b> {analysis.target_management_responsibility}</p></div>
              <div className="switch-responsibilities"><strong>Work-style signals</strong><p><b>Current:</b> {analysis.current_work_style.join(" · ")}</p><p><b>Target:</b> {analysis.target_work_style.join(" · ")}</p></div>
            </article>
          </div>
          <div className="switch-assumptions-note"><ArrowUpRight size={14} /><p>{analysis.explanation}</p><ul>{analysis.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}</ul></div>
        </div>
      )}
    </section>
  );
}
