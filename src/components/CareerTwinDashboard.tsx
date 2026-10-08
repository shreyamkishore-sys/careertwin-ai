import { lazy, Suspense, useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  ArrowLeftRight,
  BookOpen,
  ChevronRight,
  GitCompare,
  Globe2,
  GraduationCap,
  LayoutDashboard,
  Menu,
  Scale,
  Shield,
  SlidersHorizontal,
  Target,
  TrendingUp,
  UserRound,
  Wallet,
  X,
  Compass,
  Heart,
  Sparkles,
} from "lucide-react";
import { Brand } from "./Brand";
import { careerPriorities, skills } from "../data/profileOptions";
import { LaborMarketIntelligence } from "./LaborMarketIntelligence";
import { SkillDevelopmentPlan } from "./SkillDevelopmentPlan";
import { createDefaultWhatIfScenario } from "../data/whatIfScenario";
import { preferenceFields, priorityFields, skillFields } from "../data/profileRatings";
import { useJourneyState } from "../state/journeySession";
import type {
  CareerTwin,
  FitFactorContribution,
  MarketRefreshResult,
  WhatIfComparison,
} from "../types";

const CareerSimulation = lazy(() =>
  import("./CareerSimulation").then((module) => ({ default: module.CareerSimulation })),
);
const WhatIfSimulator = lazy(() =>
  import("./WhatIfSimulator").then((module) => ({ default: module.WhatIfSimulator })),
);
const CareerSwitchSimulator = lazy(() =>
  import("./CareerSwitchSimulator").then((module) => ({ default: module.CareerSwitchSimulator })),
);
const AIRiskDashboard = lazy(() =>
  import("./AIRiskDashboard").then((module) => ({ default: module.AIRiskDashboard })),
);
const DecisionTradeoffs = lazy(() =>
  import("./DecisionTradeoffs").then((module) => ({ default: module.DecisionTradeoffs })),
);
const EducationROISimulator = lazy(() =>
  import("./EducationROISimulator").then((module) => ({ default: module.EducationROISimulator })),
);

interface CareerTwinDashboardProps {
  careerTwin: CareerTwin;
  marketCode: "IN" | "US";
  marketRefreshing: boolean;
  marketError?: string | null;
  onMarketChange: (market: "IN" | "US") => void;
  onDemoMarketUpdate: (market: "IN" | "US", careerId: string, action?: "apply" | "reset") => Promise<MarketRefreshResult | null>;
  onEditProfile: () => void;
  onStartOver: () => void;
  onLogout: () => void;
  accountName: string;
  accountEmail: string;
}

type DashboardView = "overview" | "career-fit" | "compare" | "what-if" | "simulation" | "salary" | "skills" | "development-plan" | "switching" | "ai-risk" | "market" | "trade-offs" | "education-roi";

const viewMeta: Record<DashboardView, { title: string; description: string }> = {
  overview: { title: "Overview", description: "A clear view of your career journey and the paths that fit your priorities." },
  "career-fit": { title: "Career Fit", description: "See how your profile connects with possible career paths." },
  compare: { title: "Career Comparison", description: "Compare the fit, market signals, skills, and starting roles for paths you’re considering." },
  "what-if": { title: "What-If Simulator", description: "Explore how different priorities and market assumptions change the picture." },
  simulation: { title: "10-Year Simulation", description: "Explore possible role and skill milestones across a decade." },
  salary: { title: "Salary Trajectory", description: "Compare illustrative salary ranges across possible career paths." },
  skills: { title: "Skill Gap", description: "Compare your current proficiency with the configured requirements for a career." },
  "development-plan": { title: "Development Plan", description: "Review a practical sequence based on your current skill gaps." },
  switching: { title: "Career Switching", description: "Explore transitions and the experience or learning they may involve." },
  "ai-risk": { title: "AI Risk", description: "Review modeled task exposure, skill change, and resilience signals." },
  market: { title: "Market Intelligence", description: "Explore the market signals available for your selected country." },
  "trade-offs": { title: "Decision Trade-Off", description: "Compare career options against the priorities that matter to you." },
  "education-roi": { title: "Education / MBA ROI", description: "Explore the costs and possible salary scenarios for further study." },
};

const dashboardNav = [
  { label: "Overview", view: "overview", icon: LayoutDashboard, group: "YOUR JOURNEY" },
  { label: "Career Fit", view: "career-fit", icon: Target, group: "YOUR JOURNEY" },
  { label: "Compare Careers", view: "compare", icon: GitCompare, group: "YOUR JOURNEY" },
  { label: "What-If Simulator", view: "what-if", icon: SlidersHorizontal, group: "EXPLORE OPTIONS" },
  { label: "10-Year Simulation", view: "simulation", icon: TrendingUp, group: "EXPLORE OPTIONS" },
  { label: "Salary Trajectory", view: "salary", icon: Wallet, group: "EXPLORE OPTIONS" },
  { label: "Skill Gap", view: "skills", icon: Target, group: "SKILLS & DEVELOPMENT" },
  { label: "Development Plan", view: "development-plan", icon: BookOpen, group: "SKILLS & DEVELOPMENT" },
  { label: "Career Switching", view: "switching", icon: ArrowLeftRight, group: "EXPLORE OPTIONS" },
  { label: "AI Risk", view: "ai-risk", icon: Shield, group: "INSIGHTS" },
  { label: "Market Intelligence", view: "market", icon: Globe2, group: "INSIGHTS" },
  { label: "Decision Trade-Off", view: "trade-offs", icon: Scale, group: "INSIGHTS" },
  { label: "Education / MBA ROI", view: "education-roi", icon: GraduationCap, group: "INSIGHTS" },
] as const;

const viewPaths: Record<DashboardView, string> = {
  overview: "/career-twin",
  "career-fit": "/career-twin/career-fit",
  compare: "/career-twin/comparison",
  "what-if": "/career-twin/what-if",
  simulation: "/career-twin/simulation",
  salary: "/career-twin/salary",
  skills: "/career-twin/skills",
  "development-plan": "/career-twin/development-plan",
  switching: "/career-twin/switching",
  "ai-risk": "/career-twin/ai-risk",
  market: "/career-twin/market",
  "trade-offs": "/career-twin/trade-offs",
  "education-roi": "/career-twin/education-roi",
};

function viewFromPath(pathname: string): DashboardView {
  const matched = (Object.entries(viewPaths) as [DashboardView, string][]).find(([, path]) => path === pathname.replace(/\/$/, ""));
  return matched?.[0] ?? "overview";
}

function CareerComparison({ careerTwin }: { careerTwin: CareerTwin }) {
  const [selectedIds, setSelectedIds] = useJourneyState("comparisonCareerIds", () => careerTwin.recommended_careers.slice(0, 3).map((career) => career.id));
  const selected = selectedIds.map((id) => careerTwin.career_options.find((career) => career.id === id)).filter((career): career is CareerTwin["career_options"][number] => Boolean(career));
  function toggleCareer(id: string) {
    setSelectedIds((current) => current.includes(id)
      ? current.filter((item) => item !== id)
      : current.length < 4 ? [...current, id] : current);
  }
  return <div className="career-compare-page">
    <div className="compare-picker-panel">
      <div><span className="detail-label">CHOOSE CAREER PATHS</span><p>Select up to four paths. Fit and market values come from your current CareerTwin.</p></div>
      <div className="compare-picker-list">{careerTwin.career_options.map((career) => <label key={career.id} className={selectedIds.includes(career.id) ? "selected" : ""}>
        <input type="checkbox" checked={selectedIds.includes(career.id)} disabled={!selectedIds.includes(career.id) && selectedIds.length >= 4} onChange={() => toggleCareer(career.id)} />
        <span>{career.title}</span>{career.is_recommended && <small>Suggested</small>}
      </label>)}</div>
    </div>
    {selected.length ? <div className="career-compare-table-wrap"><table className="career-compare-table"><thead><tr><th scope="col">Career details</th>{selected.map((career) => <th scope="col" key={career.id}><strong>{career.title}</strong>{career.is_recommended && <small>CareerTwin recommendation</small>}</th>)}</tr></thead>
      <tbody>
        <tr><th scope="row">Combined fit</th>{selected.map((career) => <td key={career.id}><strong className="compare-score">{Math.round(career.fit_score)}<small>/100</small></strong></td>)}</tr>
        <tr><th scope="row">Profile fit</th>{selected.map((career) => <td key={career.id}>{Math.round(career.profile_fit_score)}/100</td>)}</tr>
        <tr><th scope="row">Market outlook</th>{selected.map((career) => <td key={career.id}>{career.market_outlook.job_demand} demand · {career.market_outlook.demand_trend}</td>)}</tr>
        <tr><th scope="row">AI impact signal</th>{selected.map((career) => <td key={career.id}>{career.market_outlook.ai_impact} · {Math.round(career.market_outlook.automation_exposure)}% modeled exposure</td>)}</tr>
        <tr><th scope="row">Relevant skills</th>{selected.map((career) => <td key={career.id}><div className="compare-tags">{career.relevant_skills.map((skill) => <span key={skill}>{labelFor(skills, skill)}</span>)}</div></td>)}</tr>
        <tr><th scope="row">Possible first roles</th>{selected.map((career) => <td key={career.id}>{career.starter_roles.join(" · ")}</td>)}</tr>
      </tbody></table></div> : <div className="simulation-empty">Select a career path to begin comparing.</div>}
    <p className="compare-data-note">Scores and outlook are existing CareerTwin outputs based on your profile and the selected illustrative market. This comparison does not add a new score or prediction.</p>
  </div>;
}

function labelFor<T extends string>(options: { value: T; label: string }[], value: T): string {
  return options.find((item) => item.value === value)?.label ?? value.replace(/_/g, " ");
}

function CareerCard({ career, index }: { career: CareerTwin["career_options"][number]; index: number }) {
  return (
    <article className={`career-card ${career.is_recommended ? "career-card-highlight" : ""}`}>
      <div className="career-card-topline">
        <span className="career-index">{String(index + 1).padStart(2, "0")}</span>
        <span className="career-category">{career.category}</span>
        {career.is_recommended && <span className="recommended-label"><Sparkles size={12} /> Suggested starting point</span>}
      </div>
      <div className="career-title-score">
        <h3>{career.title}</h3>
        <div className="fit-score" aria-label={`Combined career fit ${career.fit_score} out of 100`}>
          <strong>{career.fit_score}</strong><span>/ 100</span>
        </div>
      </div>
      <div
        className="fit-score-track"
        role="progressbar"
        aria-label={`${career.title} combined profile and market fit`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={career.fit_score}
      >
        <span style={{ width: `${career.fit_score}%` }} />
      </div>
      <span className="fit-score-caption">85% profile alignment + 15% illustrative market alignment</span>
      <p className="career-summary">{career.summary}</p>
      <div className="contribution-section">
        <span className="detail-label">HOW THIS SCORE ADDS UP</span>
        <div className="contribution-list">
          {career.factor_contributions.map((factor) => (
            <FactorContribution factor={factor} key={factor.factor} scale={0.85} />
          ))}
          <div className="factor-contribution market-fit-factor">
            <div className="factor-line">
              <span>Local market alignment</span>
              <strong>{(career.market_fit_score * 0.15).toFixed(1)}<span> / 15 pts</span></strong>
            </div>
            <div className="factor-track" aria-hidden="true">
              <span style={{ width: `${career.market_fit_score}%` }} />
            </div>
            <p>{career.market_explanation}</p>
            {career.market_skill_gap.length > 0 && (
              <details className="factor-gaps">
                <summary>{career.market_skill_gap.length} emerging skill{career.market_skill_gap.length === 1 ? "" : "s"} to explore</summary>
                <span>{career.market_skill_gap.join(" · ")}</span>
              </details>
            )}
          </div>
        </div>
      </div>
      <div className="starter-roles">
        <span className="detail-label">POSSIBLE FIRST ROLES</span>
        <div>{career.starter_roles.map((role) => <span className="role-tag" key={role}>{role}</span>)}</div>
      </div>
      <div className="career-reasons">
        <span className="detail-label">{career.match_reasons.length ? "WHY IT CONNECTS WITH YOU" : "WHAT YOU COULD EXPLORE"}</span>
        {career.match_reasons.length ? (
          <ul>{career.match_reasons.slice(0, 3).map((reason) => <li key={reason}>{reason}</li>)}</ul>
        ) : (
          <p className="no-match-reason">This could be a new direction to discover alongside your other matches.</p>
        )}
      </div>
      {!!career.skill_gaps?.length && <div className="career-skill-gap-ratings"><span className="detail-label">PROFICIENCY GAPS TO EXPLORE</span>{career.skill_gaps.slice(0, 4).map(gap => <span key={gap.skill}>{gap.skill}: {gap.current_rating}/5 → {gap.required_rating}/5 <small>(gap {gap.gap})</small></span>)}</div>}
      <div className="career-card-footer">
        <span><Compass size={14} /> Career starting point</span>
      </div>
    </article>
  );
}

function ProfileRatingSummary({ profile }: { profile: CareerTwin["profile"] }) {
  const skillGroups = [
    { title: "Strongest", skills: skillFields.filter(item => profile.skill_ratings[item.key] >= 4).sort((a, b) => profile.skill_ratings[b.key] - profile.skill_ratings[a.key]).slice(0, 4) },
    { title: "Developing", skills: skillFields.filter(item => profile.skill_ratings[item.key] === 3).slice(0, 4) },
    { title: "Needs improvement", skills: skillFields.filter(item => profile.skill_ratings[item.key] <= 2).sort((a, b) => profile.skill_ratings[a.key] - profile.skill_ratings[b.key]).slice(0, 4) },
  ];
  const summaryPriorityOrder = ["career_growth", "salary", "work_life_balance", "job_security", "remote_work", "international_opportunities", "management_potential", "creativity", "low_coding"];
  const priorities = [...priorityFields].sort((a, b) => profile.priority_ratings[b.key] - profile.priority_ratings[a.key] || summaryPriorityOrder.indexOf(a.key) - summaryPriorityOrder.indexOf(b.key)).slice(0, 5);
  const preferenceText = preferenceFields
    .filter(item => item.key !== "coding" && profile.preference_ratings[item.key] >= 4)
    .sort((a, b) => profile.preference_ratings[b.key] - profile.preference_ratings[a.key]).slice(0, 3).map(item => item.label.toLowerCase());
  const coding = profile.preference_ratings.coding;
  const codingText = coding <= 2 ? "Low coding" : coding === 3 ? "Some coding is comfortable" : "Enjoys technical work";
  return <section className="profile-rating-summary" aria-labelledby="profile-ratings-title">
    <div className="profile-rating-summary-heading"><div><span className="detail-label">YOUR CAREERTWIN</span><h2 id="profile-ratings-title">A snapshot of your strengths and priorities.</h2></div><span>Ratings update whenever you edit your profile.</span></div>
    <div className="profile-summary-grid"><article><h3>Skills</h3>{skillGroups.map(group => <div className="profile-summary-group" key={group.title}><strong>{group.title}</strong><span>{group.skills.length ? group.skills.map(item => `${item.label} (${profile.skill_ratings[item.key]}/5)`).join(" · ") : "No skills in this range yet"}</span></div>)}</article><article><h3>Work style</h3><p>{[codingText, ...preferenceText].join(" · ") || "Add preferences to describe your work style."}</p></article><article><h3>Top priorities</h3><ol>{priorities.map(item => <li key={item.key}>{item.label} <strong>{profile.priority_ratings[item.key]}/5</strong></li>)}</ol></article></div>
  </section>;
}

function FactorContribution({ factor, scale }: { factor: FitFactorContribution; scale: number }) {
  const contributionPercent = factor.weight === 0 ? 0 : (factor.points / factor.weight) * 100;
  const finalPoints = Number((factor.points * scale).toFixed(1));
  const finalWeight = Number((factor.weight * scale).toFixed(1));
  return (
    <div className="factor-contribution">
      <div className="factor-line">
        <span>{factor.label}</span>
        <strong>{finalPoints}<span> / {finalWeight} pts</span></strong>
      </div>
      <div className="factor-track" aria-hidden="true">
        <span style={{ width: `${contributionPercent}%` }} />
      </div>
      <p>{factor.explanation} After the 85% profile weighting, it contributes {finalPoints} of {finalWeight} final points.</p>
      {factor.matched_items.length > 0 && (
        <div className="factor-tags" aria-label={`Matching ${factor.label.toLowerCase()}`}>
          {factor.matched_items.map((item) => <span key={item}>{item}</span>)}
        </div>
      )}
      {factor.unmatched_items.length > 0 && (
        <details className="factor-gaps">
          <summary>{factor.unmatched_items.length} selected item{factor.unmatched_items.length === 1 ? "" : "s"} not reflected</summary>
          <span>{factor.unmatched_items.join(" · ")}</span>
        </details>
      )}
    </div>
  );
}

export function CareerTwinDashboard({
  careerTwin,
  marketCode,
  marketRefreshing,
  marketError,
  onMarketChange,
  onDemoMarketUpdate,
  onEditProfile,
  onStartOver,
  onLogout,
  accountName,
  accountEmail,
}: CareerTwinDashboardProps) {
  const location = useLocation();
  const routerNavigate = useNavigate();
  const { profile } = careerTwin;
  const activeView = viewFromPath(location.pathname);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [whatIfScenario, setWhatIfScenario] = useJourneyState("whatIfScenario", createDefaultWhatIfScenario);
  const [whatIfComparison, setWhatIfComparison] = useState<WhatIfComparison | null>(null);
  const [developmentCareerId, setDevelopmentCareerId] = useJourneyState("developmentCareerId", () => careerTwin.recommended_careers[0]?.id ?? "");

  useEffect(() => {
    if (!careerTwin.career_options.some((career) => career.id === developmentCareerId)) {
      setDevelopmentCareerId(careerTwin.recommended_careers[0]?.id ?? careerTwin.career_options[0]?.id ?? "");
    }
  }, [careerTwin.career_options, careerTwin.recommended_careers, developmentCareerId, setDevelopmentCareerId]);

  useEffect(() => { setMobileNavOpen(false); }, [location.pathname]);

  function navigateTo(view: DashboardView) {
    setMobileNavOpen(false);
    routerNavigate(viewPaths[view]);
    window.scrollTo(0, 0);
  }

  const focusCareer = careerTwin.recommended_careers[0];
  const market = careerTwin.market;

  function renderPage(view: DashboardView) {
    if (view === "overview") return <>
      <section className="overview-welcome">
        <div><div className="eyebrow"><span className="eyebrow-dot" /> YOUR CAREERTWIN</div><h2>Welcome back, <span className="serif-accent">{profile.name}.</span></h2><p>Here’s an overview of your career journey and the possibilities you’re exploring.</p></div>
        <div className="overview-market"><span>{market.flag} {market.label}</span><small>Current market</small></div>
      </section>
      <section className="overview-metrics" aria-label="Career journey summary">
        <article><span className="overview-metric-icon"><Target size={17} /></span><small>TOP CAREERTWIN FIT</small><strong>{focusCareer ? `${Math.round(focusCareer.fit_score)}/100` : "—"}</strong><p>Based on your profile and selected market</p></article>
        <article><span className="overview-metric-icon"><Compass size={17} /></span><small>RECOMMENDED CAREER</small><strong className="overview-metric-career">{focusCareer?.title ?? "No recommendation"}</strong><p>{focusCareer ? `${Math.round(focusCareer.profile_fit_score)} profile fit` : "Update your profile to explore paths"}</p></article>
        <article><span className="overview-metric-icon"><Shield size={17} /></span><small>MARKET AI SIGNAL</small><strong>{focusCareer?.market_outlook.ai_impact ?? "—"}</strong><p>{focusCareer ? `${Math.round(focusCareer.market_outlook.automation_exposure)}% modeled task exposure · market signal` : "No signal available"}</p></article>
        <article><span className="overview-metric-icon"><Globe2 size={17} /></span><small>MARKET OUTLOOK</small><strong>{focusCareer?.market_outlook.job_demand ?? "—"}</strong><p>{focusCareer ? `${focusCareer.market_outlook.demand_trend} demand trend · illustrative` : "No signal available"}</p></article>
      </section>
      {focusCareer && <section className="overview-recommended">
        <div className="overview-section-heading"><div><span className="detail-label">YOUR STRONGEST CURRENT MATCH</span><h3>Recommended career</h3></div><button type="button" className="text-link" onClick={() => navigateTo("career-fit")}>Explore career fit <ArrowRight size={14} /></button></div>
        <div className="overview-career-card"><div><span className="career-category">{focusCareer.category}</span><h4>{focusCareer.title}</h4><p>{focusCareer.summary}</p><div className="overview-reason-list">{focusCareer.match_reasons.slice(0, 3).map((reason) => <span key={reason}><span aria-hidden="true">✓</span>{reason}</span>)}</div></div><div className="overview-career-score"><strong>{Math.round(focusCareer.fit_score)}</strong><span>Career fit / 100</span><button type="button" className="button button-dark" onClick={() => navigateTo("career-fit")}>Explore career <ArrowRight size={14} /></button></div></div>
      </section>}
      <section className="overview-journey">
        <div className="overview-section-heading"><div><span className="detail-label">YOUR CAREER JOURNEY</span><h3>From profile to possibilities</h3></div><p>Your profile remains the starting point for every feature.</p></div>
        <div className="journey-steps">{[
          { title: "Profile", detail: "Your strengths & priorities", view: "career-fit" as DashboardView, icon: UserRound },
          { title: "Career Fit", detail: "Paths that connect", view: "career-fit" as DashboardView, icon: Target },
          { title: "Skills", detail: "Gaps to explore", view: "skills" as DashboardView, icon: BookOpen },
          { title: "Simulation", detail: "Possible next steps", view: "simulation" as DashboardView, icon: TrendingUp },
          { title: "Career Plan", detail: "Explore a path forward", view: "development-plan" as DashboardView, icon: ArrowRight },
        ].map(({ title, detail, view, icon: Icon }, index) => <button type="button" className="journey-step" key={title} onClick={() => navigateTo(view)}><span className="journey-step-icon"><Icon size={16} /></span><span className="journey-step-copy"><strong>{title}</strong><small>{detail}</small></span>{index < 4 && <ChevronRight className="journey-step-arrow" size={15} />}</button>)}</div>
      </section>
      <section className="overview-quick-actions"><div className="overview-section-heading"><div><span className="detail-label">PICK UP WHERE YOU WANT</span><h3>Quick actions</h3></div></div><div className="quick-action-grid">{[
        { label: "Compare careers", detail: "Weigh paths side by side", view: "compare" as DashboardView, icon: GitCompare },
        { label: "Run a What-If", detail: "Change the assumptions", view: "what-if" as DashboardView, icon: SlidersHorizontal },
        { label: "View 10-year simulation", detail: "Explore possible milestones", view: "simulation" as DashboardView, icon: TrendingUp },
        { label: "Check skill gaps", detail: "See skills to develop", view: "skills" as DashboardView, icon: Target },
        { label: "Explore career switching", detail: "Map a possible transition", view: "switching" as DashboardView, icon: ArrowLeftRight },
      ].map(({ label, detail, view, icon: Icon }) => <button type="button" className="quick-action-card" key={view} onClick={() => navigateTo(view)}><span><Icon size={17} /></span><strong>{label}</strong><small>{detail}</small><ArrowRight size={14} /></button>)}</div></section>
      <section className="overview-profile-note"><Heart size={17} /><div><span className="detail-label">YOUR STARTING POINT</span><p>{profile.education_level.replace(/_/g, " ")} · {profile.field_of_study} · {profile.career_priorities.map((priority) => labelFor(careerPriorities, priority).toLowerCase()).join(" · ")}</p></div><button type="button" className="text-link" onClick={onEditProfile}>Edit profile <ArrowUpRight size={14} /></button></section>
      <p className="dashboard-disclaimer"><Sparkles size={14} /> Career and market values are illustrative decision-support signals, not predictions or guarantees.</p>
    </>;

    if (view === "career-fit") return <>
      <section className="recommendations-section workspace-feature-section">
        <div className="dashboard-section-heading"><div><div className="eyebrow"><span className="eyebrow-dot" /> YOUR FIRST PLACES TO LOOK</div><h2>A few paths that <span className="serif-accent">connect with you.</span></h2></div><p>Each score blends profile alignment with the selected market’s illustrative signals. Expand a career card to understand its factors.</p></div>
        <div className="career-grid recommended-grid">{careerTwin.recommended_careers.map((career, index) => <CareerCard career={career} index={index} key={career.id} />)}</div>
        <div className="scoring-method-note"><Sparkles size={15} /><p><strong>How fit is calculated:</strong> 85% profile alignment (interests 40, skills 30, work preferences 15, priorities 15) + 15% market alignment. The market dataset is synthetic prototype data, not observed labor-market facts; scores are not probabilities or predictions.</p></div>
      </section>
      <section className="all-careers-section workspace-feature-section"><div className="dashboard-section-heading"><div><div className="eyebrow"><span className="eyebrow-dot" /> KEEP AN OPEN MIND</div><h2>More paths to <span className="serif-accent">keep in view.</span></h2></div><p>Explore options beyond your strongest matches.</p></div><div className="career-grid">{careerTwin.career_options.filter((career) => !career.is_recommended).map((career, index) => <CareerCard career={career} index={index} key={career.id} />)}</div></section>
      <section className="profile-rating-summary workspace-profile-summary"><ProfileRatingSummary profile={profile} /></section>
    </>;

    if (view === "compare") return <CareerComparison careerTwin={careerTwin} />;
    if (view === "skills" || view === "development-plan") return <>
      <div className="module-tabs" role="tablist" aria-label="Skills and development pages">
        <button type="button" role="tab" aria-selected={view === "skills"} className={view === "skills" ? "active" : ""} onClick={() => navigateTo("skills")}>Skill Gap</button>
        <button type="button" role="tab" aria-selected={view === "development-plan"} className={view === "development-plan" ? "active" : ""} onClick={() => navigateTo("development-plan")}>Development Plan</button>
      </div>
      <SkillDevelopmentPlan careerTwin={careerTwin} selectedCareerId={developmentCareerId} onCareerChange={setDevelopmentCareerId} view={view === "skills" ? "gaps" : "plan"} />
    </>;

    return <Suspense fallback={<div className="simulation-loading">Preparing {viewMeta[view].title.toLowerCase()}…</div>}>
      {view === "what-if" && <WhatIfSimulator careerTwin={careerTwin} marketCode={marketCode} dataVersion={careerTwin.market_last_updated} scenario={whatIfScenario} onScenarioChange={setWhatIfScenario} onComparisonChange={setWhatIfComparison} />}
      {(view === "simulation" || view === "salary") && <CareerSimulation careerTwin={careerTwin} marketCode={marketCode} onMarketCodeChange={onMarketChange} dataVersion={careerTwin.market_last_updated} scenario={whatIfScenario} whatIfComparison={whatIfComparison} mode={view === "salary" ? "salary" : "full"} />}
      {view === "switching" && <CareerSwitchSimulator careers={careerTwin.career_options} profileId={profile.id} marketCode={marketCode} dataVersion={careerTwin.market_last_updated} />}
      {view === "ai-risk" && <AIRiskDashboard careerTwin={careerTwin} marketCode={marketCode} dataVersion={careerTwin.market_last_updated} scenario={whatIfScenario} onScenarioChange={setWhatIfScenario} whatIfComparison={whatIfComparison} />}
      {view === "market" && <LaborMarketIntelligence marketCode={marketCode} marketRefreshing={marketRefreshing} onMarketChange={onMarketChange} onDemoMarketUpdate={onDemoMarketUpdate} dataVersion={careerTwin.market_last_updated} />}
      {view === "trade-offs" && <DecisionTradeoffs careerTwin={careerTwin} marketCode={marketCode} scenario={whatIfScenario} onScenarioChange={setWhatIfScenario} />}
      {view === "education-roi" && <EducationROISimulator careerTwin={careerTwin} marketCode={marketCode} scenario={whatIfScenario} onScenarioChange={setWhatIfScenario} />}
    </Suspense>;
  }

  return (
    <div className="dashboard-shell">
      <header className="workspace-topbar">
        <div className="workspace-topbar-brand"><button type="button" className="mobile-nav-toggle" aria-label={mobileNavOpen ? "Close dashboard navigation" : "Open dashboard navigation"} aria-expanded={mobileNavOpen} onClick={() => setMobileNavOpen((open) => !open)}>{mobileNavOpen ? <X size={20} /> : <Menu size={20} />}</button><Brand onClick={(event) => { event.preventDefault(); navigateTo("overview"); }} /></div>
        <div className="workspace-current-journey"><span className="detail-label">CURRENT TOP MATCH</span><strong>{focusCareer?.title ?? "Career exploration"}</strong><small>{focusCareer ? `${Math.round(focusCareer.fit_score)} fit` : "Profile ready"} · {market.label}</small></div>
        <div className="workspace-account"><button type="button" className="workspace-account-profile" onClick={onEditProfile}><span className="workspace-account-avatar">{accountName.trim().charAt(0).toUpperCase()}</span><span><strong>{accountName}</strong><small>{accountEmail}</small></span><ChevronRight size={14} /></button><button type="button" className="workspace-logout" onClick={onLogout} aria-label="Log out"><ArrowUpRight size={15} /><span>Log out</span></button></div>
      </header>
      {mobileNavOpen && <button type="button" className="workspace-nav-backdrop" aria-label="Close dashboard navigation" onClick={() => setMobileNavOpen(false)} />}
      <div className="workspace-layout">
        <aside className={`workspace-sidebar ${mobileNavOpen ? "workspace-sidebar-open" : ""}`} aria-label="CareerTwin dashboard">
          <div className="workspace-sidebar-intro"><span className="detail-label">CAREER WORKSPACE</span><strong>Explore your next step</strong></div>
          <nav className="workspace-sidebar-nav" aria-label="Dashboard pages">
            {(["YOUR JOURNEY", "EXPLORE OPTIONS", "SKILLS & DEVELOPMENT", "INSIGHTS"] as const).map((group) => <div className="workspace-nav-group" key={group}><span className="workspace-nav-group-label">{group}</span>{dashboardNav.filter((item) => item.group === group).map(({ label, view, icon: Icon }) => <NavLink to={viewPaths[view]} className={({ isActive }) => `workspace-nav-item ${isActive ? "workspace-nav-item-active" : ""}`} key={view} onClick={() => setMobileNavOpen(false)} end={view === "overview"}><Icon size={16} /><span>{label}</span>{activeView === view && <span className="workspace-nav-active-dot" aria-hidden="true" />}</NavLink>)}</div>)}
          </nav>
          <div className="workspace-sidebar-bottom"><div className="workspace-market-chip"><span>{market.flag}</span><div><small>MARKET</small><strong>{market.label}</strong></div></div><button type="button" className="workspace-start-over" onClick={() => { setMobileNavOpen(false); onStartOver(); }}><ArrowLeftRight size={15} /><span>Start a new journey</span></button></div>
        </aside>
        <main className="workspace-main">
          <div className="workspace-page-heading"><div><span className="workspace-breadcrumb">CareerTwin <ChevronRight size={13} /> Workspace</span><h1>{viewMeta[activeView].title}</h1><p>{viewMeta[activeView].description}</p></div><button type="button" className="button button-outline workspace-edit-profile" onClick={onEditProfile}><UserRound size={15} /> Edit profile</button></div>
          {marketError && <p className="simulation-error workspace-market-error" role="alert">{marketError}</p>}
      <div className={`workspace-content workspace-view-${activeView}`}><Routes>
        <Route path="/career-twin" element={renderPage("overview")} />
        <Route path="/career-twin/career-fit" element={renderPage("career-fit")} />
        <Route path="/career-twin/comparison" element={renderPage("compare")} />
        <Route path="/career-twin/what-if" element={renderPage("what-if")} />
        <Route path="/career-twin/simulation" element={renderPage("simulation")} />
        <Route path="/career-twin/salary" element={renderPage("salary")} />
        <Route path="/career-twin/skills" element={renderPage("skills")} />
        <Route path="/career-twin/development-plan" element={renderPage("development-plan")} />
        <Route path="/career-twin/switching" element={renderPage("switching")} />
        <Route path="/career-twin/ai-risk" element={renderPage("ai-risk")} />
        <Route path="/career-twin/market" element={renderPage("market")} />
        <Route path="/career-twin/trade-offs" element={renderPage("trade-offs")} />
        <Route path="/career-twin/education-roi" element={renderPage("education-roi")} />
        <Route path="*" element={<Navigate to="/career-twin" replace />} />
      </Routes></div>
          <footer className="workspace-footer"><Brand onClick={(event) => { event.preventDefault(); navigateTo("overview"); }} /><span>Career paths and outcomes are illustrative possibilities, not guarantees.</span><span>Updated {new Date(careerTwin.generated_at).toLocaleDateString()}</span></footer>
        </main>
      </div>
    </div>
  );
}
