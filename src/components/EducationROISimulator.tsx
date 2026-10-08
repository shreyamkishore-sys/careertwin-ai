import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowUpRight, GraduationCap, Sparkles } from "lucide-react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getAiRiskCatalog, getCareerSimulations, runCareerSwitch } from "../api";
import type { AIRiskCatalog, CareerSimulation, CareerTwin, CareerSwitchAnalysis, CareerSwitchRequest, SimulationMarketCode, WhatIfScenario } from "../types";
import { useJourneyState, type EducationSession } from "../state/journeySession";
import { buildEducationTrajectory, type EducationPath } from "../utils/educationRoi";

const YEARS_BEFORE: CareerSwitchRequest["years_before_switch"][] = [0, 1, 2, 3, 5];
const MBA_SKILLS = [
  { key: "leadership", label: "Leadership" }, { key: "business_knowledge", label: "Business knowledge" },
  { key: "presentation", label: "Presentation" }, { key: "problem_solving", label: "Problem solving" },
  { key: "communication", label: "Communication" },
] as const;
function money(value: number, market: SimulationMarketCode) {
  return market === "IN" ? `₹${value.toFixed(1)}L` : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 0 }).format(value);
}
export function EducationROISimulator({ careerTwin, marketCode, scenario, onScenarioChange }: { careerTwin: CareerTwin; marketCode: SimulationMarketCode; scenario: WhatIfScenario; onScenarioChange: (scenario: WhatIfScenario) => void }) {
  const [simulations, setSimulations] = useState<CareerSimulation[]>([]);
  const [aiCatalog, setAiCatalog] = useState<AIRiskCatalog | null>(null);
  const [simulationLoading, setSimulationLoading] = useState(true);
  const [error, setError] = useState("");
  const [educationInputs, setEducationInputs] = useJourneyState("education", () => ({
    path: "full_time_mba" as EducationPath, duration: 2, startAfter: 0 as CareerSwitchRequest["years_before_switch"],
    tuition: marketCode === "IN" ? 8 : 80000, living: marketCode === "IN" ? 3 : 30000,
    other: marketCode === "IN" ? 1 : 10000, postAdjustment: 0, currentId: "", targetId: "",
    experience: 0, graduationYear: new Date().getFullYear(),
  }));
  const { path, duration, startAfter, tuition, living, other, postAdjustment, currentId, targetId, experience, graduationYear } = educationInputs;
  const updateEducation = (patch: Partial<EducationSession>) => setEducationInputs((current) => ({ ...current, ...patch }));
  const previousMarket = useRef(marketCode);
  const [switchAnalysis, setSwitchAnalysis] = useState<CareerSwitchAnalysis | null>(null);
  const [switchError, setSwitchError] = useState("");
  const [switchLoading, setSwitchLoading] = useState(false);
  const switchRequestId = useRef(0);

  useEffect(() => {
    switchRequestId.current += 1;
    setSwitchAnalysis(null);
    setSwitchError("");
    setSwitchLoading(false);
  }, [currentId, targetId, startAfter, scenario, marketCode, careerTwin.profile.id]);

  useEffect(() => {
    let active = true;
    setSimulationLoading(true);
    setError("");
    Promise.allSettled([getCareerSimulations(marketCode), getAiRiskCatalog(marketCode)]).then(([simulationResult, riskResult]) => {
      if (!active) return;
      if (simulationResult.status === "fulfilled") {
        setSimulations(simulationResult.value.careers);
      } else {
        setSimulations([]);
        setError(simulationResult.reason instanceof Error ? simulationResult.reason.message : "Salary simulation data is unavailable.");
      }
      setAiCatalog(riskResult.status === "fulfilled" ? riskResult.value : null);
      setSimulationLoading(false);
    });
    return () => { active = false; };
  }, [marketCode]);

  const sorted = useMemo(() => [...careerTwin.career_options].sort((a, b) => a.title.localeCompare(b.title)), [careerTwin.career_options]);
  useEffect(() => {
    const current = sorted.find(c => c.id === currentId) ?? sorted.find(c => c.is_recommended) ?? sorted[0];
    const target = sorted.find(c => c.id === targetId) ?? sorted.find(c => c.id === "product-manager") ?? sorted.find(c => c.id !== current?.id) ?? current;
    if (current && current.id !== currentId) updateEducation({ currentId: current.id });
    if (target && target.id !== targetId) updateEducation({ targetId: target.id });
  }, [sorted, currentId, targetId]);
  useEffect(() => {
    if (previousMarket.current !== marketCode) {
      updateEducation({ tuition: marketCode === "IN" ? 8 : 80000, living: marketCode === "IN" ? 3 : 30000, other: marketCode === "IN" ? 1 : 10000 });
      previousMarket.current = marketCode;
    }
  }, [marketCode]);

  const careerSimulation = (id: string) => simulations.find(item => item.career_id === id);
  const currentCareer = careerSimulation(currentId);
  const targetCareer = careerSimulation(targetId) ?? currentCareer;
  const directCost = tuition + living + other;
  const trajectory = useMemo(() => buildEducationTrajectory({ currentCareer, targetCareer, duration, startAfter, directCost, postAdjustment, path }), [currentCareer, targetCareer, duration, startAfter, directCost, postAdjustment, path]);
  const opportunityCost = path === "full_time_mba" ? trajectory.reduce((sum, item) => sum + ((item.year > startAfter && item.year <= startAfter + duration) ? item.work : 0), 0) : 0;
  const breakEven = trajectory.find(item => item.netEducation >= item.cumulativeWork)?.year;
  const last = trajectory[trajectory.length - 1];
  const marketCareers = careerTwin.career_options;
  const currentOption = marketCareers.find(item => item.id === currentId);
  const targetOption = marketCareers.find(item => item.id === targetId);
  const risk = aiCatalog?.careers.find(item => item.career_id === targetId);
  const profile = careerTwin.profile;

  async function analyzeRoute() {
    const requestId = ++switchRequestId.current;
    setSwitchLoading(true); setSwitchError("");
    try {
      const result = await runCareerSwitch({ profile_id: profile.id, current_career_id: currentId, target_career_id: targetId, market: marketCode, years_before_switch: startAfter, willing_additional_education: true, learned_skills: ["product_strategy", "stakeholder_management", "communication"], what_if: { ...scenario, willing_mba: true } });
      if (requestId === switchRequestId.current) setSwitchAnalysis(result);
    } catch (e) {
      if (requestId === switchRequestId.current) { setSwitchError(e instanceof Error ? e.message : "Could not compare the routes."); setSwitchAnalysis(null); }
    } finally { if (requestId === switchRequestId.current) setSwitchLoading(false); }
  }

  const selectStyle = { padding: "10px", border: "1px solid #e3e7df", borderRadius: 4, background: "#fff", color: "#596255" };
  const currency = marketCode === "IN" ? "₹ lakh" : "USD";
  return <section className="education-roi-section" id="education-roi">
    <div className="dashboard-section-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> EDUCATION ROI SIMULATOR</div><h2>Should you work now or invest in <span className="serif-accent">further education?</span></h2></div><p>Compare configurable education costs and timing against CareerTwin’s existing illustrative career salary paths.</p></div>
    <div className="education-roi-container">
      <div className="education-roi-banner"><GraduationCap size={19}/><span>For {profile.name} · {profile.education_level.replace(/_/g, " ")} in {profile.field_of_study} · {marketCode === "IN" ? "India · INR (salary in lakh per year)" : "United States · USD per year"}</span><a href="#decision-tradeoffs">Decision trade-offs <ArrowUpRight size={14}/></a></div>
      {error && <p className="simulation-error" role="alert">{error}</p>}
      {simulationLoading && <p className="simulation-loading" role="status">Loading illustrative salary and market scenarios…</p>}
      <div className="education-roi-controls">
        <label><span>Current career path</span><select style={selectStyle} value={currentId} onChange={e => updateEducation({ currentId: e.target.value })}>{sorted.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
        <label><span>Target career after education</span><select style={selectStyle} value={targetId} onChange={e => updateEducation({ targetId: e.target.value })}>{sorted.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
        <label><span>Education option</span><select style={selectStyle} value={path} onChange={e => updateEducation({ path: e.target.value as EducationPath })}><option value="full_time_mba">Full-time MBA</option><option value="part_time_mba">Part-time MBA</option></select></label>
        <label><span>Duration</span><select style={selectStyle} value={duration} onChange={e => updateEducation({ duration: Number(e.target.value) })}>{[1,2,3].map(n => <option key={n} value={n}>{n} {n === 1 ? "year" : "years"}</option>)}</select></label>
        <label><span>Start education after</span><select style={selectStyle} value={startAfter} onChange={e => updateEducation({ startAfter: Number(e.target.value) as CareerSwitchRequest["years_before_switch"] })}>{YEARS_BEFORE.map(n => <option key={n} value={n}>{n === 0 ? "Immediately" : `${n} ${n === 1 ? "year" : "years"} of work`}</option>)}</select></label>
        <label><span>Experience now (years)</span><input type="number" min="0" max="40" value={experience} onChange={e => updateEducation({ experience: Math.max(0, Number(e.target.value)) })} /></label>
        <label><span>Graduation year</span><input type="number" min="1980" max="2100" value={graduationYear} onChange={e => updateEducation({ graduationYear: Number(e.target.value) })}/></label>
        <label><span>Post-education salary scenario adjustment: {postAdjustment}%</span><input type="range" min="-30" max="50" step="5" value={postAdjustment} onChange={e => updateEducation({ postAdjustment: Number(e.target.value) })}/></label>
      </div>
      <p className="education-roi-note">Current degree and skill ratings come from your profile. Duration, work experience and graduation year are editable assumptions. Post-education adjustment is a user-set scenario, not an MBA premium claim.</p>
      <div className="education-roi-cost-grid">
        {([ ["Tuition", "tuition", tuition], ["Living expenses", "living", living], ["Other costs", "other", other] ] as const).map(([label, field, value]) => <label key={label}><span>{label} ({currency})</span><input type="number" min="0" step="0.5" value={value} onChange={e => updateEducation({ [field]: Math.max(0, Number(e.target.value)) })}/></label>)}
        <article><span>Total direct cost</span><strong>{money(directCost, marketCode)}</strong></article><article><span>Foregone salary (simplified)</span><strong>{money(opportunityCost, marketCode)}</strong></article><article className="education-total-investment"><span>Total economic investment</span><strong>{money(directCost + opportunityCost, marketCode)}</strong><small>Direct cost + foregone salary while studying</small></article>
      </div>
      <div className="education-roi-metrics"><article><span>10-year cumulative, work now</span><strong>{money(last?.cumulativeWork ?? 0, marketCode)}</strong></article><article><span>10-year cumulative, education path</span><strong>{money(last?.cumulativeEducation ?? 0, marketCode)}</strong></article><article><span>Economic difference after direct costs</span><strong>{money((last?.cumulativeEducation ?? 0) - directCost - (last?.cumulativeWork ?? 0), marketCode)}</strong><small>Includes the salary gap in the trajectories; foregone salary is not deducted twice.</small></article><article><span>Scenario break-even</span><strong>{breakEven ? `Year ${breakEven}` : "Not reached"}</strong><small>Within this 10-year scenario.</small></article></div>
      <div className="education-roi-chart-grid"><article className="education-roi-panel"><div><span className="detail-label">ANNUAL SALARY TRAJECTORY</span><h3>Work now vs education path</h3></div><div className="education-roi-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={trajectory}><CartesianGrid stroke="#e9ede5" strokeDasharray="3 3"/><XAxis dataKey="year" tickFormatter={v=>`Year ${v}`}/><YAxis/><Tooltip formatter={(v)=>money(Number(v),marketCode)} labelFormatter={v=>`Year ${v}`}/><Legend/><Line name="Work now · typical" dataKey="work" stroke="#536d54" strokeWidth={2}/><Line name="Education path · typical" dataKey="education" stroke="#bd8755" strokeWidth={2}/><Line name="Work now · conservative" dataKey="workLow" stroke="#9ab09b" strokeDasharray="4 3" dot={false}/><Line name="Work now · high-growth" dataKey="workHigh" stroke="#78977a" strokeDasharray="2 3" dot={false}/><Line name="Education · conservative" dataKey="educationLow" stroke="#d1a782" strokeDasharray="4 3" dot={false}/><Line name="Education · high-growth" dataKey="educationHigh" stroke="#bd8755" strokeDasharray="2 3" dot={false}/></LineChart></ResponsiveContainer></div></article>
      <article className="education-roi-panel"><div><span className="detail-label">CUMULATIVE EARNINGS</span><h3>Gross earnings and net education scenario</h3></div><div className="education-roi-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={trajectory}><CartesianGrid stroke="#e9ede5" strokeDasharray="3 3"/><XAxis dataKey="year" tickFormatter={v=>`Year ${v}`}/><YAxis/><Tooltip formatter={(v)=>money(Number(v),marketCode)} labelFormatter={v=>`Year ${v}`}/><Legend/><Line name="Work now cumulative" dataKey="cumulativeWork" stroke="#536d54" strokeWidth={2}/><Line name="Education cumulative" dataKey="cumulativeEducation" stroke="#bd8755" strokeWidth={2}/><Line name="Education after direct costs" dataKey="netEducation" stroke="#7798a1" strokeDasharray="5 4"/></LineChart></ResponsiveContainer></div></article></div>
      <div className="education-roi-timeline"><article><span className="detail-label">PATH A · START WORKING NOW</span><p>{profile.field_of_study} → {currentCareer?.years.find(point => point.year === 0)?.role ?? currentOption?.title ?? "Career entry"} → {currentCareer?.years.find(point => point.year === 4)?.role ?? "Career progression"}</p><small>Potential first roles: {currentOption?.starter_roles.slice(0,3).join(" · ") || "See selected career"}</small></article><article><span className="detail-label">PATH B · {path === "full_time_mba" ? "FULL-TIME" : "PART-TIME"} MBA</span><p>{startAfter ? `Work ${startAfter} ${startAfter === 1 ? "year" : "years"}` : "Graduate"} → {path === "full_time_mba" ? `${duration} years education` : `${duration} years part-time study`} → {targetCareer?.career_title ?? targetOption?.title ?? "Target career"}</p><small>Potential first roles: {targetCareer?.years.find(point => point.year === 0)?.role ?? targetOption?.starter_roles.slice(0,3).join(" · ") ?? "Selected target career"} · Illustrative pathway</small></article></div>
      <div className="education-roi-lower-grid"><article className="education-roi-panel"><span className="detail-label">ILLUSTRATIVE SKILL DEVELOPMENT</span><h3>What education could help you develop</h3><p className="education-roi-note">Assumed learning contribution only; attending a program does not guarantee proficiency gains.</p>{MBA_SKILLS.map(skill => { const current = profile.skill_ratings[skill.key]; const assumed = skill.key === "leadership" || skill.key === "business_knowledge" ? Math.min(5,current+1) : current; return <div className="education-skill-row" key={skill.key}><span>{skill.label}</span><strong>{current}/5 → {assumed}/5</strong><small>{current < 4 ? `${Math.max(0,4-assumed)} point(s) to illustrative 4/5 target` : "Already rated strong"}</small></div>; })}<p>Existing Career Fit for {targetOption?.title ?? "target career"}: <strong>{targetOption?.fit_score ?? "—"}/100</strong>. Hypothetical skill ratings are not passed into or rescored by the Career Fit engine.</p><p>Current MBA-relevant strengths: {MBA_SKILLS.filter(skill => profile.skill_ratings[skill.key] >= 4).map(skill=>skill.label).join(", ") || "Continue developing business and communication skills"}.</p></article>
        <article className="education-roi-panel"><span className="detail-label">CAREER, AI & MARKET CONTEXT</span><h3>{targetOption?.title ?? "Target career"}</h3><p>{targetOption?.market_outlook?.job_demand ?? "Market demand unavailable"} demand · {targetOption?.market_outlook?.demand_trend ?? "—"} trend · salary range {targetOption ? `${money(targetOption.market_outlook.salary_low, marketCode)}–${money(targetOption.market_outlook.salary_high,marketCode)}` : "—"}</p><p>Emerging skills: {targetOption?.market_outlook?.emerging_skills.slice(0,5).join(" · ") ?? "—"}</p><p>AI impact: {risk?.impact_level ?? targetOption?.market_outlook?.ai_impact ?? "—"} · AI resilience {risk ? `${risk.ai_resilience_score}/100` : "not available"}. MBA study does not remove AI risk; keep developing AI literacy and role-specific skills.</p><small>Market source: {targetOption?.market_outlook?.data_source ?? "CareerTwin prototype"} · confidence {targetOption ? `${Math.round(targetOption.market_outlook.data_confidence)}%` : "—"} · updated {targetOption?.market_outlook?.last_updated ?? careerTwin.market_last_updated}. Prototype market data is illustrative, not live.</small></article></div>
      <div className="education-roi-routes education-roi-panel"><div><span className="detail-label">CAREER SWITCHING INTEGRATION</span><h3>{currentOption?.title ?? "Current role"} → MBA option → {targetOption?.title ?? "Target role"}</h3><p>Compare with a work-first transition using the existing Career Switching Simulator. MBA is one possible route, not a universal requirement.</p></div><button className="button button-outline" type="button" onClick={analyzeRoute} disabled={switchLoading || !currentId || !targetId || currentId === targetId}>{switchLoading ? "Comparing…" : "Analyze this route"}</button>{switchError && <p role="alert">{switchError}</p>}{switchAnalysis && <div className="education-route-results"><span>Skill overlap: <strong>{switchAnalysis.skill_overlap}%</strong></span><span>Transition difficulty: <strong>{switchAnalysis.transition_difficulty}</strong></span><span>Preparation time: <strong>{`${switchAnalysis.preparation_min_months}–${switchAnalysis.preparation_max_months}`} months</strong></span><span>Education context: <strong>{switchAnalysis.education_guidance}</strong></span><a href="#career-switch">Open Career Switching Simulator <ArrowUpRight size={13}/></a></div>}</div>
      <div className="education-roi-lower-grid"><article className="education-roi-panel"><span className="detail-label">DECISION TRADE-OFFS</span><h3>What you gain and what you invest</h3><p><strong>Education may add:</strong> structured business learning, leadership practice, peer networks and a possible career-switch pathway, depending on program and role.</p><p><strong>You invest:</strong> {money(directCost,marketCode)} direct costs, {duration} study years, and {path === "full_time_mba" ? `${money(opportunityCost,marketCode)} illustrative foregone salary` : "continued salary alongside part-time study"}.</p><p><strong>Work now offers:</strong> immediate experience and salary, with career development through work and self-directed learning.</p><a href="#decision-tradeoffs">Review the existing Decision Trade-Off Analysis <ArrowUpRight size={13}/></a></article><article className="education-roi-panel"><span className="detail-label">EXISTING WHAT-IF</span><h3>Try the MBA assumption alongside your scenarios</h3><label className="education-toggle"><input type="checkbox" checked={scenario.willing_mba} onChange={e=>onScenarioChange({...scenario,willing_mba:e.target.checked})}/> Include willingness to pursue an MBA in the shared CareerTwin What-If and career-switch scenario</label><p>Duration, costs, timing and salary adjustment above are calculated against the existing salary trajectories as configurable education assumptions; they do not replace CareerTwin’s What-If engine.</p><a href="#what-if">Open What-If simulator <ArrowUpRight size={13}/></a></article></div>
      <div className="education-roi-summary"><span className="detail-label">YOUR EDUCATION DECISION · SCENARIO SUMMARY</span><h3>{(last?.cumulativeEducation ?? 0) - directCost >= (last?.cumulativeWork ?? 0) ? "This education scenario closes the modeled earnings gap within ten years." : "Working now has higher modeled cumulative earnings in this scenario."}</h3><p>With your selected {duration}-year {path === "full_time_mba" ? "full-time" : "part-time"} MBA assumptions, {startAfter ? `starting after ${startAfter} year(s) of work, ` : ""}the modeled 10-year gross earnings are {money(last?.cumulativeEducation ?? 0,marketCode)} on the education path and {money(last?.cumulativeWork ?? 0,marketCode)} if working now. After direct education costs, the economic difference is {money((last?.cumulativeEducation ?? 0)-directCost-(last?.cumulativeWork ?? 0),marketCode)}. This is sensitive to salary path and cost assumptions; no universal recommendation is implied.</p><div className="education-roi-advice-grid"><p><strong>Work now may suit you if</strong> immediate income, experience or lower cost is a priority, or your chosen target career does not require further education.</p><p><strong>Education may suit you if</strong> the target career benefits from formal business learning, you want to explore a transition, and the cost and time investment fits your circumstances.</p></div></div>
      <details className="education-roi-assumptions"><summary>Assumptions used</summary><ul><li>Career salary trajectories are reused from CareerTwin’s existing 10-year scenario service for the selected market.</li><li>During full-time study, salary is modeled as zero; part-time study retains the current-career salary.</li><li>After completion, target-career trajectory starts at its first annual simulation point and is scaled by your editable salary scenario adjustment.</li><li>Opportunity cost sums current-career typical annual salary during full-time study years. Total economic investment = direct cost + foregone wages.</li><li>Economic difference = education-path cumulative gross salary − work-now cumulative gross salary − direct costs. Foregone wages are already reflected in salary trajectories, so they are not subtracted twice.</li><li>Break-even is the first simulated year where education cumulative earnings less direct cost equal or exceed work-now cumulative earnings; none is reported if not reached.</li><li>Salary progression and market context remain illustrative scenario estimates; program admission, outcomes, taxes, financing and discounting are not modeled.</li><li>Current experience: {experience} years · graduation year assumption: {graduationYear}.</li></ul></details>
      <p className="education-roi-disclaimer"><Sparkles size={15}/> Education costs, salary paths, career progression and break-even calculations are illustrative scenarios based on configurable assumptions. They are not guarantees, predictions, or financial advice. {aiCatalog?.data_status === "prototype_illustrative" && "Market signals shown in this prototype are illustrative and not live forecasts."}</p>
    </div>
  </section>;
}
