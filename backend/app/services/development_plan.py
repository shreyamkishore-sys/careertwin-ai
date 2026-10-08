from typing import Literal

from pydantic import BaseModel, Field


class DevelopmentPlanItem(BaseModel):
    skill_key: str
    skill: str
    current_rating: int = Field(ge=1, le=5)
    required_rating: int = Field(ge=1, le=5)
    gap: int = Field(ge=1, le=4)
    priority_score: int = Field(ge=1, le=20)
    priority: Literal["high", "medium", "low"]
    priority_reason: str
    why_it_matters: str
    suggested_action: str
    learning_sequence: list[str]
    phase: Literal["foundation", "core"]


class DevelopmentPlanPhase(BaseModel):
    number: int = Field(ge=1, le=3)
    title: str
    description: str
    skills: list[str]


class CareerDevelopmentPlan(BaseModel):
    career_fit_score: float = Field(ge=0, le=100)
    items: list[DevelopmentPlanItem]
    phases: list[DevelopmentPlanPhase]


# Skill descriptions and practice suggestions are generic guidance, not course or
# labor-market claims. Only skills present in the selected career's requirements
# are included in the resulting plan.
SKILL_GUIDANCE: dict[str, tuple[str, str, list[str]]] = {
    "excel": ("Supports organizing, checking, and summarizing structured information.", "Practice spreadsheet analysis using clean, labeled datasets.", ["Review formulas and data types", "Practice lookups, filtering, and pivot summaries", "Create a concise analysis sheet and explain its assumptions"]),
    "sql": ("Supports retrieving and combining structured data for analysis.", "Practice writing queries against sample relational data.", ["Learn SELECT, filtering, sorting, and aggregation", "Practice joins and grouped comparisons", "Answer a small set of business questions with documented queries"]),
    "python": ("Supports repeatable analysis and small task automation.", "Build small scripts that transform and inspect data.", ["Practice core syntax, collections, and functions", "Read and transform tabular data", "Complete a small reproducible analysis and document the steps"]),
    "statistics": ("Supports interpreting variation, comparisons, and uncertainty in data.", "Work through practical examples of descriptive and inferential reasoning.", ["Review distributions and summary measures", "Practice sampling, comparison, and uncertainty concepts", "Write a short interpretation that states assumptions and limits"]),
    "communication": ("Supports explaining work and coordinating with other people.", "Practice concise written and spoken explanations of analytical work.", ["Summarize a finding in plain language", "Practice asking clarifying questions and adapting detail", "Present a recommendation with evidence and limitations"]),
    "business_knowledge": ("Supports connecting role tasks to organizational goals and constraints.", "Study how a selected business problem relates to users, operations, and outcomes.", ["Define a business problem and its stakeholders", "Map relevant processes and measures", "Write a brief analysis linking evidence to a business decision"]),
    "presentation": ("Supports communicating structured findings to an audience.", "Practice turning evidence into a clear, audience-focused presentation.", ["Organize a short narrative", "Choose clear tables or visuals", "Present conclusions and caveats in a short briefing"]),
    "leadership": ("Supports coordinating work, decisions, and shared responsibilities.", "Practice planning and reflecting on a small collaborative task.", ["Clarify goals and responsibilities", "Practice feedback and decision documentation", "Lead a small project exercise and reflect on outcomes"]),
    "problem_solving": ("Supports breaking ambiguous tasks into testable steps.", "Practice framing a problem, evaluating options, and explaining a solution.", ["State the problem and constraints", "Compare possible approaches using evidence", "Document a solution and what would change your conclusion"]),
    "data_analysis": ("Supports turning raw information into interpretable findings.", "Practice moving from a question to a checked, communicated analysis.", ["Inspect and clean a dataset", "Summarize patterns and check assumptions", "Produce a short analysis with a clear conclusion"]),
    "ai_literacy": ("Supports evaluating AI-enabled tools, their limits, and responsible use.", "Practice reviewing AI outputs and documenting quality and risk considerations.", ["Identify an appropriate task and its constraints", "Check generated output against reliable evidence", "Document limitations, privacy considerations, and human review"]),
    "product_thinking": ("Supports understanding user needs and evaluating product choices.", "Practice connecting user problems, product behavior, and measurable outcomes.", ["Describe a user problem and context", "Compare possible product responses", "Propose a small test and define what evidence would be useful"]),
}


def build_development_plan(
    career_fit_score: float,
    skill_requirements: list[dict],
) -> CareerDevelopmentPlan:
    gaps = []
    for requirement in skill_requirements:
        current = int(requirement["current_rating"])
        required = int(requirement["required_rating"])
        gap = required - current
        if gap <= 0:
            continue
        skill_key = str(requirement["skill_key"])
        label = str(requirement.get("skill", skill_key.replace("_", " ").title()))
        why, action, sequence = SKILL_GUIDANCE.get(
            skill_key,
            ("This skill is listed in the selected career's configured requirements.", f"Practice {label} on a small role-related task.", [f"Review the foundations of {label}", f"Practice {label} on a small role-related task", "Apply the skill in a documented example"]),
        )
        priority_score = gap * required
        priority: Literal["high", "medium", "low"] = (
            "high" if priority_score >= 12 else "medium" if priority_score >= 6 else "low"
        )
        phase: Literal["foundation", "core"] = "foundation" if current <= 2 or gap >= 3 else "core"
        gaps.append(DevelopmentPlanItem(
            skill_key=skill_key,
            skill=label,
            current_rating=current,
            required_rating=required,
            gap=gap,
            priority_score=priority_score,
            priority=priority,
            priority_reason=f"Priority uses gap size × required proficiency ({gap} × {required}); higher required levels and larger gaps come first.",
            why_it_matters=why,
            suggested_action=action,
            learning_sequence=sequence,
            phase=phase,
        ))
    gaps.sort(key=lambda item: (-item.priority_score, item.skill))
    foundation = [item.skill for item in gaps if item.phase == "foundation"]
    core = [item.skill for item in gaps if item.phase == "core"]
    required_skills = [str(item.get("skill", item["skill_key"])) for item in skill_requirements]
    phases = []
    if foundation:
        phases.append(DevelopmentPlanPhase(number=len(phases) + 1, title="Build foundations", description="Start with the largest gaps or skills rated at 1–2/5.", skills=foundation))
    if core:
        phases.append(DevelopmentPlanPhase(number=len(phases) + 1, title="Strengthen core career skills", description="Work through remaining below-target skills in priority order.", skills=core))
    if required_skills and gaps:
        phases.append(DevelopmentPlanPhase(number=len(phases) + 1, title="Apply skills together", description="Use the selected career's configured skill set in a small, documented role-related project.", skills=required_skills))
    if not skill_requirements:
        phases = []
    elif not gaps:
        phases.append(DevelopmentPlanPhase(number=1, title="Maintain and apply your core skills", description="Your current ratings meet the configured requirements; practice applying these skills together in a small role-related task.", skills=required_skills))
    return CareerDevelopmentPlan(career_fit_score=round(career_fit_score, 1), items=gaps, phases=phases)
