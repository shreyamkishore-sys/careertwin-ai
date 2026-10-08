import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import { getAiRiskCatalog, getCareerSimulations, getMarketIntelligence, runCareerSwitch } from "../api";
import type { AIRiskCatalog, Career, CareerSimulation, CareerTwin, CareerSwitchAnalysis, CareerSwitchRequest, MarketIntelligence, SimulationMarketCode, WhatIfScenario } from "../types";
import { DECISION_SCORE_WEIGHTS, PRIORITY_FACTORS, scoreDecisionCareer, type DecisionPriorities, type DecisionPriorityKey } from "../utils/decisionScoring";
import { useJourneyState } from "../state/journeySession";

const intensity = (n: number) => n < 34 ? "Low" : n < 67 ? "Medium" : "High";

export function DecisionTradeoffs({ careerTwin, marketCode, scenario, onScenarioChange }: { careerTwin: CareerTwin; marketCode: SimulationMarketCode; scenario: WhatIfScenario; onScenarioChange: (scenario: WhatIfScenario) => void }) {
  const careers = careerTwin.career_options;
  const [selected, setSelected] = useJourneyState("decisionCareerIds", () => careers.filter(c => c.is_recommended).slice(0, 3).map(c => c.id));
  const [priorities, setPriorities] = useJourneyState("decisionPriorities", () => Object.fromEntries(PRIORITY_FACTORS.map(p => [p.key, careerTwin.profile.priority_ratings[p.profileKey] ?? 3])) as DecisionPriorities);
  const [market, setMarket] = useState<MarketIntelligence | null>(null);
  const [ai, setAi] = useState<AIRiskCatalog | null>(null);
  const [simulations, setSimulations] = useState<CareerSimulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [switchAnalysis, setSwitchAnalysis] = useState<CareerSwitchAnalysis | null>(null);
  const [switchPair, setSwitchPair] = useJourneyState("decisionSwitchPair", ["data-analyst", "product-manager"] as [string, string]);
  const [switchError, setSwitchError] = useState("");
  const switchRequestId = useRef(0);

  useEffect(() => {
    switchRequestId.current += 1;
    setSwitchAnalysis(null);
    setSwitchError("");
  }, [switchPair, marketCode, careerTwin.profile.id]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([getMarketIntelligence(marketCode), getAiRiskCatalog(marketCode), getCareerSimulations(marketCode)])
      .then(([m, a, s]) => { if (active) { setMarket(m); setAi(a); setSimulations(s.careers); } })
      .catch(() => { if (active) { setMarket(null); setAi(null); } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [marketCode, careerTwin.market_last_updated]);

  const selectedCareers = useMemo(() => selected.map(id => careers.find(c => c.id === id)).filter((c): c is Career => Boolean(c)), [selected, careers]);
  const rows = useMemo(() => {
    const maximumSalary = Math.max(1, ...selectedCareers.map(selectedCareer => {
      const points = simulations.find(item => item.career_id === selectedCareer.id)?.years;
      return points?.[points.length - 1]?.salary_mid ?? selectedCareer.market_outlook.salary_high;
    }));
    return selectedCareers.map(career => {
    const outlook = market?.careers.find(item => item.career_id === career.id) ?? career.market_outlook;
    const risk = ai?.careers.find(item => item.career_id === career.id);
    const simulation = simulations.find(item => item.career_id === career.id);
    const score = scoreDecisionCareer({
      career,
      profile: careerTwin.profile,
      simulation,
      maximumSalary,
      priorities,
      aiResilience: risk?.ai_resilience_score,
    });
    const communication = career.relevant_skills.includes("communication") || career.related_interests.includes("communication") ? 78 : 48;
    const analytical = career.related_interests.includes("analytics") || career.relevant_skills.includes("data_analysis") ? 80 : 45;
    const management = career.related_interests.includes("leadership") || career.priorities.includes("growth") ? 72 : 48;
    const gains: string[] = [];
    const sacrifices: string[] = [];
    if (score.careerFit >= 70) gains.push(`Strong CareerTwin profile fit (${Math.round(score.careerFit)}/100).`);
    if (score.skillMatches.length) gains.push(`Skills meeting the configured target: ${score.skillMatches.slice(0, 3).join(", ")}.`);
    if (score.preferenceMatches.length) gains.push(`Profile preferences align with ${score.preferenceMatches.slice(0, 3).join(", ")}.`);
    if (score.priorityMatches.length) gains.push(`Career signals align with your ${score.priorityMatches.slice(0, 3).join(", ").toLowerCase()} priorities.`);
    if (outlook.demand_index >= 65) gains.push(`${outlook.job_demand} illustrative demand signal (${Math.round(outlook.demand_index)}/100).`);
    if (priorities.salary >= 4) gains.push(`Illustrative salary range: ${market?.market.currency_symbol ?? ""}${outlook.salary_low}–${outlook.salary_high} ${market?.market.unit ?? ""}.`);
    if (!gains.length) gains.push("This path connects to some of your selected interests and career priorities.");
    if (score.skillGaps.length) sacrifices.push(`Skill proficiency below configured target: ${score.skillGaps.slice(0, 3).join(", ")}.`);
    if (score.preferenceConflicts.length) sacrifices.push(`Potential preference mismatch: ${score.preferenceConflicts.slice(0, 3).join(", ")}.`);
    if (score.priorityConflicts.length) sacrifices.push(`Limited alignment with your ${score.priorityConflicts.slice(0, 3).join(", ").toLowerCase()} priorities.`);
    if (risk && risk.skill_change_score >= 65) sacrifices.push(`Higher modeled AI-related skill change (${risk.skill_change_score}/100) means continued learning may matter.`);
    if (outlook.data_status === "prototype_illustrative") sacrifices.push("Market and salary values are illustrative prototype signals with low confidence.");
    if (!sacrifices.length) sacrifices.push("Trade-offs depend on employer, seniority, region, and the skills you develop over time.");
    return { career, outlook, risk, simulation, score, decisionScore: score.overall, entry: score.careerFit, salary: simulation?.years[simulation.years.length - 1]?.salary_mid ?? outlook.salary_high, coding: score.codingIntensity, analytical, communication, management, missingSkills: score.skillGaps, gains, sacrifices };
  });
  }, [selectedCareers, priorities, market, ai, simulations, careerTwin.profile]);

  const baselineScores = useMemo(() => rows.map(row => {
    const base = Object.fromEntries(PRIORITY_FACTORS.map(p => [p.key, careerTwin.profile.priority_ratings[p.profileKey] ?? 3])) as DecisionPriorities;
    const breakdown = scoreDecisionCareer({ career: row.career, profile: careerTwin.profile, simulation: row.simulation, maximumSalary: Math.max(1, ...rows.map(r => r.salary)), priorities: base, aiResilience: row.risk?.ai_resilience_score });
    return { id: row.career.id, value: breakdown.overall };
  }), [rows, careerTwin.profile]);
  function toggleCareer(id: string) {
    setSelected(current => current.includes(id) ? (current.length > 2 ? current.filter(item => item !== id) : current) : (current.length < 4 ? [...current, id] : current));
  }
  async function compareSwitch() {
    if (!careerTwin.profile.id || switchPair[0] === switchPair[1]) return;
    const requestId = ++switchRequestId.current;
    setSwitchError("");
    setSwitchAnalysis(null);
    try {
      const req: CareerSwitchRequest = { profile_id: careerTwin.profile.id, current_career_id: switchPair[0], target_career_id: switchPair[1], market: marketCode, years_before_switch: 0, willing_additional_education: false, learned_skills: [], what_if: { avoid_coding: false, higher_salary: false, work_life_balance: false, remote_work: false, international_opportunities: false, willing_mba: false, learn_technical_skills: false, faster_growth: false, increase_demand: false, decrease_demand: false, increase_ai_adoption: false, decrease_ai_adoption: false, increase_salary_growth: false, decrease_salary_growth: false, emerging_skills_important: false } };
      const result = await runCareerSwitch(req);
      if (requestId === switchRequestId.current) setSwitchAnalysis(result);
    } catch (error) {
      if (requestId === switchRequestId.current) setSwitchError(error instanceof Error ? error.message : "Could not load the career-switch comparison.");
    }
  }

  return <section className="decision-section" id="decision-tradeoffs">
    <div className="dashboard-section-heading"><div><div className="eyebrow"><span className="eyebrow-dot" /> DECISION TRADE-OFF ANALYSIS</div><h2>What do you gain — <span className="serif-accent">and what do you give up?</span></h2></div><p>Compare paths against your profile and priorities. This is decision support, not a universal ranking.</p></div>
    <div className="decision-panel"><div className="decision-panel-heading"><div><span className="detail-label">SELECT 2–4 CAREERS</span><p>Choose careers to compare side by side.</p></div><span>{selected.length} selected</span></div><div className="decision-career-select">{careers.map(c => <label key={c.id} className={selected.includes(c.id) ? "selected" : ""}><input type="checkbox" checked={selected.includes(c.id)} disabled={!selected.includes(c.id) && selected.length >= 4} onChange={() => toggleCareer(c.id)} />{c.title}</label>)}</div></div>
    <div className="decision-priorities"><div className="decision-panel-heading"><div><span className="detail-label">YOUR DECISION PRIORITIES</span><p>Sliders begin with your saved 1–5 ratings and update this comparison locally.</p></div><span>1 = lower · 5 = higher</span></div><div className="decision-slider-grid">{PRIORITY_FACTORS.map(p => <label key={p.key}><span>{p.label}<strong>{priorities[p.key]}</strong></span><input type="range" min="1" max="5" step="1" value={priorities[p.key]} onChange={e => { const value = Number(e.target.value); setPriorities(old => ({ ...old, [p.key]: value })); const keyMap: Partial<Record<DecisionPriorityKey, keyof WhatIfScenario>> = { salary: "higher_salary", growth: "faster_growth", workLifeBalance: "work_life_balance", remote: "remote_work", international: "international_opportunities", lowCoding: "avoid_coding" }; const scenarioKey = keyMap[p.key]; if (scenarioKey) onScenarioChange({ ...scenario, [scenarioKey]: value >= 4 }); }} /></label>)}</div><a className="text-link" href="#what-if">Continue in the What-If Simulator <ArrowRight size={13}/></a></div>
    {selected.length < 2 ? <p className="decision-empty">Select at least two careers to see the comparison.</p> : <>
      <div className="decision-score-grid">{rows.map(row => <article key={row.career.id}><span className="detail-label">PROFILE-DRIVEN TRADE-OFF SCORE</span><strong>{row.decisionScore}<small>/100</small></strong><h3>{row.career.title}</h3><div className="decision-score-breakdown">{([["CareerTwin fit", row.score.careerFit], ["Skill alignment", row.score.skillAlignment], ["Preference alignment", row.score.preferenceAlignment], ["Priority alignment", row.score.priorityAlignment], ["Market opportunity", row.score.marketOpportunity], ["AI resilience", row.score.aiResilience]] as [string, number][]).map(([label, value]) => <span key={label}>{label}<b>{Math.round(value)}</b></span>)}</div><p>Comparison aid based on your saved ratings, curated career characteristics, and illustrative market data.</p></article>)}</div>
      <div className="decision-panel"><div className="decision-panel-heading"><div><span className="detail-label">TRADE-OFF MATRIX</span><p>Salary potential × existing career fit · bubble size reflects demand; marker shade reflects AI resilience.</p></div></div><div className="decision-chart"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{ top: 12, right: 18, bottom: 22, left: 2 }}><CartesianGrid stroke="#e8ebe4" /><XAxis type="number" dataKey="salaryScore" name="Salary potential" domain={[0, 100]} tick={{ fontSize: 10 }} label={{ value: "Relative salary potential", position: "insideBottom", offset: -12, fontSize: 10 }} /><YAxis type="number" dataKey="fit" name="Career fit" domain={[0, 100]} tick={{ fontSize: 10 }} label={{ value: "Career fit", angle: -90, position: "insideLeft", fontSize: 10 }} /><ZAxis type="number" dataKey="demand" range={[100, 600]} name="Job demand" /><Tooltip cursor={{ strokeDasharray: "3 3" }} formatter={(value, name) => [`${Math.round(Number(value))}/100`, String(name)]} />{rows.map(row => <Scatter key={row.career.id} name={`${row.career.title} · resilience ${row.risk?.ai_resilience_score ?? "—"}`} data={[{ name: row.career.title, salaryScore: Math.round(row.salary / Math.max(1, ...rows.map(r => r.salary)) * 100), fit: row.entry, demand: row.outlook.demand_index, resilience: row.risk?.ai_resilience_score ?? 50 }]} fill={row.risk && row.risk.ai_resilience_score >= 70 ? "#476c4d" : row.risk && row.risk.ai_resilience_score < 45 ? "#c28c51" : "#81947c"} />)}</ScatterChart></ResponsiveContainer></div><div className="decision-legend">Each marker is a selected career. Green = higher modeled resilience; amber = lower modeled resilience.</div></div>
      <div className="decision-panel decision-table-wrap"><div className="decision-panel-heading"><div><span className="detail-label">TRADE-OFF SCORECARD</span><p>Intensity factors are descriptive; higher does not mean better.</p></div></div><div className="decision-table-scroll"><table className="decision-table"><thead><tr><th>Factor</th>{rows.map(r => <th key={r.career.id}>{r.career.title}</th>)}</tr></thead><tbody>
        {[...[{ label: "Overall trade-off score", value: (r: typeof rows[number]) => `${r.score.overall}/100` }, { label: "CareerTwin fit", value: (r: typeof rows[number]) => `${Math.round(r.score.careerFit)}/100` }, { label: "Skill alignment · rated vs required", value: (r: typeof rows[number]) => `${Math.round(r.score.skillAlignment)}/100` }, { label: "Preference alignment · curated characteristics", value: (r: typeof rows[number]) => `${Math.round(r.score.preferenceAlignment)}/100` }, { label: "Priority alignment · your 1–5 weights", value: (r: typeof rows[number]) => `${Math.round(r.score.priorityAlignment)}/100` }, { label: "Market opportunity · illustrative", value: (r: typeof rows[number]) => `${Math.round(r.score.marketOpportunity)}/100` }, { label: "AI resilience · modeled", value: (r: typeof rows[number]) => `${Math.round(r.score.aiResilience)}/100` }, { label: "Salary range · illustrative", value: (r: typeof rows[number]) => `${market?.market.currency_symbol ?? ""}${r.outlook.salary_low}–${r.outlook.salary_high}` }, { label: "Career growth signal", value: (r: typeof rows[number]) => `${r.outlook.salary_growth_rate}% salary growth · ${r.outlook.demand_trend} trend` }, { label: "Job demand", value: (r: typeof rows[number]) => `${r.outlook.job_demand} · ${r.outlook.demand_index}/100` }, { label: "AI impact", value: (r: typeof rows[number]) => r.risk ? `${r.risk.impact_level} · ${r.risk.ai_impact_score}/100` : r.outlook.ai_impact }, { label: "AI-related skill change", value: (r: typeof rows[number]) => `${r.risk?.skill_change_score ?? "—"}/100` }, { label: "Coding intensity · curated", value: (r: typeof rows[number]) => intensity(r.coding) }, { label: "Analytical intensity · curated", value: (r: typeof rows[number]) => intensity(r.analytical) }, { label: "Communication intensity · curated", value: (r: typeof rows[number]) => intensity(r.communication) }, { label: "Management potential · curated", value: (r: typeof rows[number]) => intensity(r.management) }, { label: "Skill gaps vs configured requirements", value: (r: typeof rows[number]) => r.missingSkills.length ? r.missingSkills.join(", ") : "No below-target rated skills" }].map(metric => <tr key={metric.label}><th>{metric.label}</th>{rows.map(r => <td key={r.career.id}>{metric.value(r)}</td>)}</tr>)]}
      </tbody></table></div><small>Education requirements, formal work-life balance, international opportunity, and skill proficiency levels are not represented consistently in the current career records.</small></div>
      <div className="decision-gain-grid">{rows.map(r => <article className="decision-panel" key={r.career.id}><span className="detail-label">{r.career.title}</span><h3>What you gain</h3><ul>{r.gains.map(item => <li key={item}>{item}</li>)}</ul><h3>What you may sacrifice</h3><ul>{r.sacrifices.map(item => <li key={item}>{item}</li>)}</ul><h3>This may be a strong fit if…</h3><p>{r.career.summary} You are comfortable with {intensity(r.coding).toLowerCase()} coding intensity and want {intensity(r.analytical).toLowerCase()} analytical work.</p><div className="decision-market-meta">{r.risk && <span>AI resilience {r.risk.ai_resilience_score} · impact {r.risk.impact_level} · skill change {r.risk.skill_change_score}</span>}<span>{r.outlook.data_status === "prototype_illustrative" ? "Prototype market data — illustrative · confidence low" : `Confidence ${Math.round(r.outlook.data_confidence * 100)}%`}</span><span>Source: {r.outlook.data_source} · updated {new Date(r.outlook.last_updated).toLocaleDateString()}</span>{r.outlook.emerging_skills.length > 0 && <span>Emerging skills: {r.outlook.emerging_skills.slice(0, 3).join(", ")}</span>}</div></article>)}</div>
      <div className="decision-panel"><div className="decision-panel-heading"><div><span className="detail-label">DECISION CHANGE</span><p>Before (profile priority defaults) → after (current sliders).</p></div></div><div className="decision-change-grid">{rows.map(r => { const before = baselineScores.find(s => s.id === r.career.id)?.value ?? r.decisionScore; return <div key={r.career.id}><strong>{r.career.title}</strong><span>{before} → {r.decisionScore}</span><small>{r.decisionScore > before ? "Moved up" : r.decisionScore < before ? "Moved down" : "Unchanged"} as priority weights changed.</small></div>; })}</div></div>
      <div className="decision-panel"><div className="decision-panel-heading"><div><span className="detail-label">CAREER SWITCH TRADE-OFF</span><p>Runs the existing Career Switching Simulator for this pair.</p></div></div><div className="decision-switch-controls"><select value={switchPair[0]} onChange={e => setSwitchPair([e.target.value, switchPair[1]])}>{careers.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}</select><ArrowRight size={16}/><select value={switchPair[1]} onChange={e => setSwitchPair([switchPair[0], e.target.value])}>{careers.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}</select><button className="button button-dark" disabled={switchPair[0] === switchPair[1]} onClick={() => void compareSwitch()}>Compare switch</button></div>{switchError && <p role="alert">{switchError}</p>}{switchAnalysis && <div className="decision-change-grid"><div><strong>Skill overlap</strong><span>{switchAnalysis.skill_overlap}%</span><small>{switchAnalysis.transition_difficulty} transition · {switchAnalysis.preparation_min_months}–{switchAnalysis.preparation_max_months} months modeled</small></div><div><strong>Potential gains</strong><small>{switchAnalysis.target_management_responsibility}</small></div><div><strong>Skills to develop</strong><small>{switchAnalysis.skills_to_develop.slice(0, 4).map(s => s.label).join(", ") || "See transition analysis"}</small></div></div>}</div>
      <div className="decision-summary"><div className="eyebrow"><span className="eyebrow-dot"/> YOUR DECISION SUMMARY</div><h3>Based on your current profile and selected priorities…</h3><p>{rows.slice().sort((a,b) => b.decisionScore-a.decisionScore).map(r => `${r.career.title} (${r.decisionScore})`).join(" · ")} show the strongest alignment under these weights. The score is a comparison aid, not a guaranteed recommendation.</p><div className="decision-summary-list">{rows.map(r => <p key={r.career.id}><strong>{r.career.title}</strong> · Advantage: {r.gains[0]} Trade-off: {r.sacrifices[0]}</p>)}</div></div>
    </>}
    <details className="decision-panel decision-explain"><summary>How is this calculated?</summary><p>The overall score is a transparent comparison aid: CareerTwin fit {DECISION_SCORE_WEIGHTS.careerFit * 100}%, skill alignment {DECISION_SCORE_WEIGHTS.skillAlignment * 100}%, preference alignment {DECISION_SCORE_WEIGHTS.preferenceAlignment * 100}%, priority alignment {DECISION_SCORE_WEIGHTS.priorityAlignment * 100}%, illustrative market opportunity {DECISION_SCORE_WEIGHTS.marketOpportunity * 100}%, and modeled AI resilience {DECISION_SCORE_WEIGHTS.aiResilience * 100}%. CareerTwin fit itself includes 15% market alignment, so market signals also contribute indirectly through that fit component. Skill alignment compares actual 1–5 ratings with backend-configured requirements; missing legacy ratings use the existing neutral default of 3. Preference signals use available career tags and are curated prototype characteristics. Priority weights start from your saved ratings; salary and market signals are relative/illustrative, not measured hiring or work-life outcomes. This score is not a validated prediction.</p><div className="decision-weight-grid">{PRIORITY_FACTORS.map(p => <span key={p.key}>{p.label}: weight {priorities[p.key]}/5</span>)}</div>{loading && <small>Loading existing market, AI risk, and salary scenario data…</small>}<p><Sparkles size={13}/> AI risk figures describe modeled task and skill change, not job-loss predictions. Market data: {market?.data_status === "prototype_illustrative" ? "synthetic prototype values; not live market data" : market?.provider ?? "unavailable"}.</p></details>
  </section>;
}
