import type { CareerTwin } from "../types";

export function SkillDevelopmentPlan({ careerTwin, selectedCareerId, onCareerChange, view = "all" }: {
  careerTwin: CareerTwin;
  selectedCareerId: string;
  onCareerChange: (careerId: string) => void;
  view?: "all" | "gaps" | "plan";
}) {
  const career = careerTwin.career_options.find((item) => item.id === selectedCareerId) ?? careerTwin.recommended_careers[0];
  if (!career) return null;

  const requirements = career.skill_requirements ?? [];
  const plan = career.development_plan;
  const topItem = plan.items[0];
  const showGaps = view !== "plan";
  const showPlan = view !== "gaps";

  return (
    <section className="development-plan-section" id="skill-development">
      <div className="dashboard-section-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> {view === "gaps" ? "SKILL GAP ANALYSIS" : view === "plan" ? "PERSONALIZED DEVELOPMENT PLAN" : "SKILL GAP & DEVELOPMENT PLAN"}</div>
          <h2>{view === "gaps" ? <>See where your skills <span className="serif-accent">stand today.</span></> : view === "plan" ? <>Build your next steps <span className="serif-accent">with purpose.</span></> : <>What should you <span className="serif-accent">learn first?</span></>}</h2>
        </div>
        <p>{view === "gaps" ? "Compare your self-reported proficiency with this career’s configured skill requirements." : view === "plan" ? "Work through a practical sequence based on your configured career skill requirements." : "Compare your self-reported proficiency with this career’s configured skill requirements, then work through a prioritized practice plan."}</p>
      </div>

      <div className="development-plan-panel">
        <label className="development-career-select">
          <span className="detail-label">TARGET CAREER</span>
          <select value={career.id} onChange={(event) => onCareerChange(event.target.value)} aria-label="Target career for skill development plan">
            {careerTwin.career_options.map((option) => <option key={option.id} value={option.id}>{option.title}</option>)}
          </select>
        </label>

        <div className="development-fit-context">
          <span className="detail-label">CURRENT CAREERTWIN FIT</span>
          <strong>{Math.round(plan.career_fit_score)}/100</strong>
          <p>This is the existing profile-and-market fit score. The plan does not estimate how much learning would change it.</p>
        </div>

        {showGaps && <div className="development-requirements">
          <div className="development-plan-heading">
            <div><span className="detail-label">CURRENT SKILL GAP</span><p>Ratings use your profile and the same configured requirements used by CareerTwin.</p></div>
            <span>{requirements.length} configured skills</span>
          </div>
          {requirements.length ? <div className="development-requirement-list">
            {requirements.map((requirement) => {
              const gap = Math.max(0, requirement.required_rating - requirement.current_rating);
              const item = plan.items.find((planned) => planned.skill_key === requirement.skill_key);
              return <div className="development-requirement-row" key={requirement.skill_key}>
                <strong>{requirement.skill}</strong>
                <span>{requirement.current_rating}/5 current</span>
                <span>{requirement.required_rating}/5 required</span>
                <span>{gap ? `Gap ${gap}` : "Meets target"}</span>
                {item && <b className={`development-priority development-priority-${item.priority}`}>{item.priority} priority</b>}
              </div>;
            })}
          </div> : <p className="development-plan-empty">No configured skill requirements are available for this career.</p>}
        </div>}

        {showPlan && <div className="development-top-priority">
          <span className="detail-label">YOUR TOP DEVELOPMENT PRIORITY</span>
          {topItem ? <>
            <div className="development-top-title"><h3>1. {topItem.skill}</h3><b className={`development-priority development-priority-${topItem.priority}`}>{topItem.priority} priority</b></div>
            <p>Current {topItem.current_rating}/5 · required {topItem.required_rating}/5 · gap {topItem.gap}</p>
            <p><strong>Why it matters:</strong> {topItem.why_it_matters}</p>
            <p><strong>Next step:</strong> {topItem.suggested_action}</p>
            <small>{topItem.priority_reason}</small>
          </> : <p>{requirements.length ? `Your current profile already aligns strongly with the configured core skill requirements for ${career.title}. Keep these skills active and use them in the applied practice phase below.` : `No configured skill requirements are available for ${career.title}, so a proficiency-based development plan cannot be calculated.`}</p>}
        </div>}

        {showPlan && plan.items.length > 0 && <div className="development-items">
          <div className="development-plan-heading"><div><span className="detail-label">PRIORITIZED DEVELOPMENT ITEMS</span><p>Ordered by gap size and required proficiency.</p></div></div>
          {plan.items.map((item, index) => <article className="development-item" key={item.skill_key}>
            <div className="development-item-title"><h3>{index + 1}. {item.skill}</h3><b className={`development-priority development-priority-${item.priority}`}>{item.priority}</b></div>
            <p className="development-item-ratings">Current {item.current_rating}/5 · required {item.required_rating}/5 · gap {item.gap}</p>
            <p><strong>Why it matters:</strong> {item.why_it_matters}</p>
            <p><strong>Suggested action:</strong> {item.suggested_action}</p>
            <ol>{item.learning_sequence.map((step) => <li key={step}>{step}</li>)}</ol>
          </article>)}
        </div>}

        {showPlan && <div className="development-phases">
          <div className="development-plan-heading"><div><span className="detail-label">SUGGESTED LEARNING SEQUENCE</span><p>Phases use only this career’s configured required skills.</p></div></div>
          <div className="development-phase-grid">{plan.phases.map((phase) => <article key={phase.number}>
            <span className="detail-label">PHASE {phase.number}</span>
            <h3>{phase.title}</h3>
            <p>{phase.description}</p>
            <div>{phase.skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
          </article>)}</div>
        </div>}

        {showPlan && <p className="development-plan-disclaimer">Priority formula: gap size × required proficiency (maximum 20); High ≥12, Medium 6–11, Low 1–5. This plan uses CareerTwin’s configured career requirements and your self-reported skill levels. It is decision-support guidance, not a guarantee of employment or job readiness. No learning-time estimate is shown because the project has no validated effort model.</p>}
      </div>
    </section>
  );
}
