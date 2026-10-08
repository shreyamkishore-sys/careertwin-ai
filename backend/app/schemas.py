from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.services.profile_ratings import (
    PREFERENCE_KEYS,
    PRIORITY_KEYS,
    SKILL_KEYS,
    normalize_ratings,
    PRIORITY_TAG_TO_RATING,
    WORK_STYLE_TO_PREFERENCE,
    SKILL_TAG_TO_RATING,
)

EducationLevel = Literal[
    "high_school",
    "undergraduate",
    "graduate",
    "postgraduate",
    "other",
]
Interest = Literal[
    "analytics",
    "business_strategy",
    "technology",
    "design_creativity",
    "helping_people",
    "communication",
    "leadership",
    "research",
]
Skill = Literal[
    "problem_solving",
    "communication",
    "spreadsheets",
    "data_analysis",
    "coding",
    "design",
    "writing",
    "research",
    "organization",
    "teamwork",
    "visual_design",
    "statistics",
]
WorkPreference = Literal[
    "collaborative",
    "independent",
    "structured",
    "flexible",
    "remote_ready",
]
CareerPriority = Literal[
    "salary",
    "work_life_balance",
    "growth",
    "remote_work",
    "stability",
    "impact",
    "international_opportunities",
    "creativity",
]
MarketCode = Literal["IN", "US", "UK", "CA", "AU", "DE"]
MarketDataStatus = Literal["prototype_illustrative", "reviewed_dataset", "live_verified"]


class SignUpInput(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("name")
    @classmethod
    def name_is_not_whitespace(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Please enter your name.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_and_validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Please enter a valid email address.")
        return value


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_and_validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Please enter a valid email address.")
        return value


class AuthUserRead(BaseModel):
    id: int
    name: str
    email: str
    profile_id: int | None = None


class StudentProfileInput(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    education_level: EducationLevel
    field_of_study: str = Field(min_length=2, max_length=120)
    skills: list[Skill] = Field(default_factory=list, max_length=20)
    skill_ratings: dict[str, int] = Field(default_factory=dict)
    interests: list[Interest] = Field(min_length=1, max_length=8)
    work_preferences: list[WorkPreference] = Field(min_length=1, max_length=5)
    preference_ratings: dict[str, int] = Field(default_factory=dict)
    career_priorities: list[CareerPriority] = Field(min_length=1, max_length=8)
    priority_ratings: dict[str, int] = Field(default_factory=dict)

    @field_validator("skill_ratings", mode="before")
    @classmethod
    def valid_skill_ratings(cls, value):
        return normalize_ratings(value, SKILL_KEYS)

    @field_validator("priority_ratings", mode="before")
    @classmethod
    def valid_priority_ratings(cls, value):
        return normalize_ratings(value, PRIORITY_KEYS)

    @field_validator("preference_ratings", mode="before")
    @classmethod
    def valid_preference_ratings(cls, value):
        return normalize_ratings(value, PREFERENCE_KEYS)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_and_rating_fields(cls, value):
        if not isinstance(value, dict):
            fields = (
                "id", "created_at", "name", "education_level", "field_of_study", "skills", "interests",
                "work_preferences", "career_priorities", "skill_ratings", "preference_ratings", "priority_ratings",
            )
            if not all(hasattr(value, field) for field in ("name", "education_level", "field_of_study", "skills")):
                return value
            value = {field: getattr(value, field, None) for field in fields}
        data = dict(value)
        # Accept the nested example shape as well as the canonical *_ratings fields.
        if isinstance(data.get("skills"), dict):
            data["skill_ratings"] = data.pop("skills")
            data["skills"] = []
        legacy_preferences = data.pop("preferences", None)
        legacy_priorities = data.pop("priorities", None)
        if isinstance(legacy_preferences, dict) and "preference_ratings" not in data:
            data["preference_ratings"] = legacy_preferences
        elif isinstance(legacy_preferences, list):
            pref_aliases = {
                "analytical": ("independent", "analytical_work"), "remote": ("remote_ready", "remote_work"),
                "remote work": ("remote_ready", "remote_work"), "people interaction": ("collaborative", "people_interaction"),
                "collaborative": ("collaborative", "people_interaction"), "structured": ("structured", "structured_work"),
            }
            existing_styles = list(data.get("work_preferences") or [])
            legacy_ratings = {}
            for preference in legacy_preferences:
                label = str(preference).strip().lower()
                if label.startswith("coding") and ":" in label:
                    legacy_ratings["coding"] = label.split(":", 1)[1].strip()
                    continue
                mapped = pref_aliases.get(label)
                if mapped:
                    style, rating_key = mapped
                    if style not in existing_styles:
                        existing_styles.append(style)
                    legacy_ratings[rating_key] = 4
            if existing_styles:
                data["work_preferences"] = existing_styles
            if "preference_ratings" not in data and legacy_ratings:
                data["preference_ratings"] = legacy_ratings
        if isinstance(legacy_priorities, dict) and "priority_ratings" not in data:
            data["priority_ratings"] = legacy_priorities
        elif isinstance(legacy_priorities, list):
            priority_aliases = {
                "salary": ("salary", "salary"), "career growth": ("growth", "career_growth"),
                "growth": ("growth", "career_growth"), "work-life balance": ("work_life_balance", "work_life_balance"),
                "job security": ("stability", "job_security"), "stability": ("stability", "job_security"),
                "remote": ("remote_work", "remote_work"), "remote work": ("remote_work", "remote_work"),
                "international opportunities": ("international_opportunities", "international_opportunities"),
                "creativity": ("creativity", "creativity"),
            }
            existing_priorities = list(data.get("career_priorities") or [])
            legacy_ratings = {}
            for priority in legacy_priorities:
                mapped = priority_aliases.get(str(priority).strip().lower())
                if mapped:
                    tag, rating_key = mapped
                    if tag not in existing_priorities:
                        existing_priorities.append(tag)
                    legacy_ratings[rating_key] = 4
            if existing_priorities:
                data["career_priorities"] = existing_priorities
            if "priority_ratings" not in data and legacy_ratings:
                data["priority_ratings"] = legacy_ratings

        aliases = {
            "skill_ratings": {"businessKnowledge": "business_knowledge", "problemSolving": "problem_solving", "dataAnalysis": "data_analysis", "productThinking": "product_thinking", "aiLiteracy": "ai_literacy"},
            "preference_ratings": {"analytical": "analytical_work", "analyticalWork": "analytical_work", "peopleInteraction": "people_interaction", "managementInterest": "management", "remoteWork": "remote_work", "structuredWork": "structured_work", "problemSolving": "problem_solving", "strategicThinking": "strategic_thinking"},
            "priority_ratings": {"careerGrowth": "career_growth", "workLifeBalance": "work_life_balance", "jobSecurity": "job_security", "remoteWork": "remote_work", "internationalOpportunities": "international_opportunities", "managementPotential": "management_potential", "lowCoding": "low_coding"},
        }
        allowed = {"skill_ratings": SKILL_KEYS, "preference_ratings": PREFERENCE_KEYS, "priority_ratings": PRIORITY_KEYS}
        for field, keys in allowed.items():
            source = data.get(field)
            if source is not None:
                if not isinstance(source, dict):
                    raise ValueError(f"{field} must be an object of 1–5 ratings.")
                values = {aliases[field].get(key, key): item for key, item in source.items()}
                normalized = {}
                for key, item in values.items():
                    if key not in keys:
                        continue
                    if isinstance(item, str) and not item.strip().isdigit():
                        if item.strip().lower() not in {
                            "low", "beginner", "strongly prefer low/no coding", "somewhat low", "basic",
                            "prefer low coding", "medium", "moderate", "intermediate", "comfortable with some coding",
                            "high", "strong", "comfortable with technical work", "very high", "advanced",
                            "enjoy coding/technical work",
                        }:
                            raise ValueError(f"{field}.{key} must be an integer from 1 to 5.")
                        normalized[key] = normalize_ratings({key: item}, (key,))[key]
                    else:
                        try:
                            number = int(item)
                        except (TypeError, ValueError, OverflowError) as error:
                            raise ValueError(f"{field}.{key} must be an integer from 1 to 5.") from error
                        if isinstance(item, bool) or number < 1 or number > 5 or str(item).strip() != str(number):
                            raise ValueError(f"{field}.{key} must be an integer from 1 to 5.")
                        normalized[key] = number
                data[field] = normalized

        skills = data.get("skills") or []
        priorities = data.get("career_priorities") or []
        styles = data.get("work_preferences") or []
        for field, keys, defaults, mapping, tags in (
            ("skill_ratings", SKILL_KEYS, SKILL_TAG_TO_RATING, SKILL_TAG_TO_RATING, skills),
            ("priority_ratings", PRIORITY_KEYS, PRIORITY_TAG_TO_RATING, PRIORITY_TAG_TO_RATING, priorities),
            ("preference_ratings", PREFERENCE_KEYS, WORK_STYLE_TO_PREFERENCE, WORK_STYLE_TO_PREFERENCE, styles),
        ):
            supplied = data.get(field) or {}
            if field not in data or not supplied:
                base = {key: 3 for key in keys}
                for tag in tags:
                    key = mapping.get(tag)
                    if key in base:
                        base[key] = 4
                data[field] = base
            else:
                data[field] = normalize_ratings(supplied, keys)
        return data

    @field_validator("name", "field_of_study")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be blank.")
        return cleaned

    @field_validator("skills", "interests", "work_preferences", "career_priorities")
    @classmethod
    def require_unique_selections(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("Selections must not contain duplicates.")
        return values


class StudentProfileRead(StudentProfileInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class CareerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    summary: str
    related_interests: list[str]
    relevant_skills: list[str]
    work_styles: list[str]
    priorities: list[str]
    starter_roles: list[str]


class FitFactorContribution(BaseModel):
    factor: Literal["interests", "skills", "work_preferences", "career_priorities"]
    label: str
    weight: float
    points: float
    matched_count: int
    selected_count: int
    matched_items: list[str]
    unmatched_items: list[str]
    explanation: str


class SkillProficiencyGapRead(BaseModel):
    skill: str
    current_rating: int = Field(ge=1, le=5)
    required_rating: int = Field(ge=1, le=5)
    gap: int = Field(ge=0, le=4)


class SkillProficiencyRequirementRead(BaseModel):
    skill_key: str
    skill: str
    current_rating: int = Field(ge=1, le=5)
    required_rating: int = Field(ge=1, le=5)


class SkillDevelopmentPlanItemRead(BaseModel):
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


class SkillDevelopmentPhaseRead(BaseModel):
    number: int = Field(ge=1, le=3)
    title: str
    description: str
    skills: list[str]


class CareerDevelopmentPlanRead(BaseModel):
    career_fit_score: float = Field(ge=0, le=100)
    items: list[SkillDevelopmentPlanItemRead]
    phases: list[SkillDevelopmentPhaseRead]


class CareerMatchRead(CareerRead):
    match_reasons: list[str]
    is_recommended: bool
    fit_score: float
    profile_fit_score: float
    market_fit_score: float
    market_fit_adjustment: float
    market_explanation: str
    market_skill_gap: list[str]
    skill_requirements: list[SkillProficiencyRequirementRead] = Field(default_factory=list)
    skill_gaps: list[SkillProficiencyGapRead] = Field(default_factory=list)
    development_plan: CareerDevelopmentPlanRead
    market_outlook: "CareerMarketSignalRead"
    factor_contributions: list[FitFactorContribution]


class CareerTwinRead(BaseModel):
    id: int
    generated_at: datetime
    overview: str
    profile: StudentProfileRead
    market: "MarketCatalogEntry"
    market_data_status: str
    market_last_updated: datetime
    score_basis: str
    recommended_careers: list[CareerMatchRead]
    career_options: list[CareerMatchRead]


class MarketCatalogEntry(BaseModel):
    code: MarketCode
    label: str
    flag: str
    currency: str
    currency_symbol: str
    unit: str
    locale: str
    available: bool
    status_note: str


class CareerMarketSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    career_id: str
    market_code: MarketCode
    currency: str
    job_demand: str
    demand_index: float = Field(ge=0, le=100)
    demand_trend: Literal["rising", "stable", "declining"]
    salary_low: float = Field(ge=0)
    salary_high: float = Field(ge=0)
    salary_growth_rate: float
    ai_impact: Literal["low", "medium", "high"]
    automation_exposure: float = Field(ge=0, le=100)
    emerging_skills: list[str]
    emerging_skill_tags: list[str]
    declining_skills: list[str]
    hiring_trend: Literal["rising", "stable", "declining"]
    market_growth: float
    geographic_demand: dict[str, str]
    possible_transition: str
    data_source: str
    data_confidence: float = Field(ge=0, le=1)
    data_status: MarketDataStatus
    last_updated: datetime

    @model_validator(mode="after")
    def salary_range_is_ordered(self) -> "CareerMarketSignalRead":
        if self.salary_low > self.salary_high:
            raise ValueError("Salary range low must not exceed high.")
        return self


class MarketIntelligenceRead(BaseModel):
    market: MarketCatalogEntry
    data_status: MarketDataStatus
    provider: str
    last_updated: datetime
    description: str
    careers: list[CareerMarketSignalRead]


class MarketRefreshRead(BaseModel):
    market: MarketCatalogEntry
    action: Literal["apply", "reset"]
    career_id: str
    before_demand: str
    after_demand: str
    before_fit_score: float
    after_fit_score: float
    before_rank: int
    after_rank: int
    changed_factors: list[str]
    explanation: str
    updated_at: datetime
    career_twin: "CareerTwinRead"


class MarketCatalogRead(BaseModel):
    markets: list[MarketCatalogEntry]


class MarketFitBreakdown(BaseModel):
    market_score: float
    explanation: str
    components: dict[str, float]
    skill_gap: list[str]


CareerMatchRead.model_rebuild()
CareerTwinRead.model_rebuild()


class SimulationMarket(BaseModel):
    code: Literal["IN", "US"]
    label: str
    currency: str
    unit: str
    locale: str


class CareerSimulationYear(BaseModel):
    year: int = Field(ge=0, le=10)
    role: str
    salary_low: float = Field(ge=0)
    salary_mid: float = Field(ge=0)
    salary_high: float = Field(ge=0)

    @model_validator(mode="after")
    def salary_range_is_ordered(self) -> "CareerSimulationYear":
        if not self.salary_low <= self.salary_mid <= self.salary_high:
            raise ValueError("Salary estimates must satisfy low <= midpoint <= high.")
        return self


class CareerSimulationStage(BaseModel):
    year: int = Field(ge=0, le=10)
    role: str
    skills: list[str]
    job_demand: str = "Unknown"
    demand_trend: str = "stable"
    ai_impact: str = "Unknown"
    automation_exposure: float = 0.0
    salary_growth_rate: float = 0.0
    possible_promotion: str | None = None
    possible_transition: str | None = None


class CareerSimulationRead(BaseModel):
    career_id: str
    career_title: str
    category: str
    years: list[CareerSimulationYear] = Field(min_length=11, max_length=11)
    stages: list[CareerSimulationStage] = Field(min_length=1)
    market_outlook: CareerMarketSignalRead | None = None
    salary_basis: str = "Illustrative scenario-based estimate; not a prediction."


class CareerSimulationsRead(BaseModel):
    market: SimulationMarket
    salary_basis: str
    careers: list[CareerSimulationRead]


class WhatIfScenario(BaseModel):
    avoid_coding: bool = False
    higher_salary: bool = False
    work_life_balance: bool = False
    remote_work: bool = False
    international_opportunities: bool = False
    willing_mba: bool = False
    learn_technical_skills: bool = False
    faster_growth: bool = False
    increase_demand: bool = False
    decrease_demand: bool = False
    increase_ai_adoption: bool = False
    decrease_ai_adoption: bool = False
    increase_salary_growth: bool = False
    decrease_salary_growth: bool = False
    emerging_skills_important: bool = False

    @model_validator(mode="after")
    def market_directions_are_not_conflicting(self) -> "WhatIfScenario":
        conflicting_pairs = (
            ("increase_demand", "decrease_demand"),
            ("increase_ai_adoption", "decrease_ai_adoption"),
            ("increase_salary_growth", "decrease_salary_growth"),
        )
        for increase, decrease in conflicting_pairs:
            if getattr(self, increase) and getattr(self, decrease):
                raise ValueError(f"Choose either '{increase}' or '{decrease}', not both.")
        return self


class AIRiskAnalysisInput(BaseModel):
    profile_id: int = Field(ge=1)
    market: Literal["IN", "US"] = "IN"
    what_if: WhatIfScenario = Field(default_factory=WhatIfScenario)


class AIRiskScoreRead(BaseModel):
    ai_impact_score: int = Field(ge=0, le=100)
    impact_level: Literal["Low", "Moderate", "High", "Very high"]
    automation_exposure: float = Field(ge=0, le=100)
    ai_resilience_score: int = Field(ge=0, le=100)
    skill_change_score: int = Field(ge=0, le=100)
    opportunity_score: int = Field(ge=0, le=100)
    resilience_explanation: str


class AIRiskCatalogCareerRead(BaseModel):
    career_id: str
    career_title: str
    ai_impact_score: int = Field(ge=0, le=100)
    impact_level: Literal["Low", "Moderate", "High", "Very high"]
    automation_exposure: float = Field(ge=0, le=100)
    ai_resilience_score: int = Field(ge=0, le=100)
    skill_change_score: int = Field(ge=0, le=100)
    opportunity_score: int = Field(ge=0, le=100)
    job_demand: str
    demand_trend: str
    data_status: MarketDataStatus
    data_source: str
    data_confidence: float = Field(ge=0, le=1)
    last_updated: datetime


class AIRiskCatalogRead(BaseModel):
    market: MarketCatalogEntry
    provider: str
    data_status: MarketDataStatus
    last_updated: datetime
    careers: list[AIRiskCatalogCareerRead]


class AIRiskTaskRead(BaseModel):
    name: str
    automation_exposure: float = Field(ge=0, le=100)
    ai_assistance_potential: float = Field(ge=0, le=100)
    human_judgment: float = Field(ge=0, le=100)
    future_importance: float = Field(ge=0, le=100)
    category: Literal["highly_automatable", "ai_augmented", "human_centric", "lower_priority"]
    explanation: str


class AIReadinessSkillRead(BaseModel):
    label: str
    status: Literal["ready", "assumed", "gap"]
    weight: float = Field(gt=0)
    technical: bool
    current_rating: int = Field(default=3, ge=1, le=5)
    required_rating: int = Field(default=4, ge=1, le=5)
    gap: int = Field(default=1, ge=0, le=4)


class AIReadinessRead(BaseModel):
    baseline_score: int = Field(ge=0, le=100)
    scenario_score: int = Field(ge=0, le=100)
    strengths: list[str]
    gaps: list[str]
    assumed_skills: list[str]
    learn_next: list[str]
    skill_evidence: list[AIReadinessSkillRead]
    explanation: str


class AIRiskMarketRead(BaseModel):
    market: MarketCatalogEntry
    job_demand: str
    demand_index: float = Field(ge=0, le=100)
    demand_trend: str
    ai_impact: str
    automation_exposure: float = Field(ge=0, le=100)
    hiring_trend: str
    emerging_skills: list[str]
    data_source: str
    data_confidence: float = Field(ge=0, le=1)
    data_status: MarketDataStatus
    last_updated: datetime


class AIRiskAnalysisRead(BaseModel):
    career: CareerRead
    baseline: AIRiskScoreRead
    scenario: AIRiskScoreRead
    tasks: list[AIRiskTaskRead]
    future_skills: list[str]
    resilient_skills: list[str]
    opportunities: list[str]
    risks: list[str]
    readiness: AIReadinessRead
    baseline_market: AIRiskMarketRead
    scenario_market: AIRiskMarketRead
    scenario_effects: list[str]
    assumptions: list[str]


class CareerSwitchInput(BaseModel):
    profile_id: int = Field(ge=1)
    current_career_id: str = Field(min_length=1, max_length=64)
    target_career_id: str = Field(min_length=1, max_length=64)
    market: Literal["IN", "US"] = "IN"
    years_before_switch: Literal[0, 1, 2, 3, 5] = 0
    willing_additional_education: bool = False
    learned_skills: list[
        Literal[
            "sql",
            "python",
            "product_strategy",
            "roadmapping",
            "stakeholder_management",
            "user_research",
            "communication",
        ]
    ] = Field(default_factory=list, max_length=7)
    what_if: WhatIfScenario = Field(default_factory=WhatIfScenario)

    @model_validator(mode="after")
    def careers_must_differ(self) -> "CareerSwitchInput":
        if self.current_career_id == self.target_career_id:
            raise ValueError("Choose a different target career to simulate a switch.")
        if len(self.learned_skills) != len(set(self.learned_skills)):
            raise ValueError("Learned skills must not contain duplicates.")
        return self


class TransitionSkillRead(BaseModel):
    label: str
    status: Literal["ready", "assumed", "partially_transferable", "to_develop"]
    evidence: list[str]
    current_rating: int | None = Field(default=None, ge=1, le=5)
    required_rating: int | None = Field(default=None, ge=1, le=5)
    gap: int | None = Field(default=None, ge=0, le=4)


class TransitionRoadmapStageRead(BaseModel):
    title: str
    description: str
    minimum_month: int = Field(ge=1)
    maximum_month: int = Field(ge=1)

    @model_validator(mode="after")
    def month_range_is_ordered(self) -> "TransitionRoadmapStageRead":
        if self.minimum_month > self.maximum_month:
            raise ValueError("Roadmap stages must satisfy minimum_month <= maximum_month.")
        return self


class TransitionSalaryPointRead(BaseModel):
    year: Literal[0, 3, 5, 7, 10]
    role: str
    salary_low: float = Field(ge=0)
    salary_mid: float = Field(ge=0)
    salary_high: float = Field(ge=0)


class TransitionMarketRead(BaseModel):
    job_demand: str
    demand_index: float = Field(ge=0, le=100)
    demand_trend: str
    ai_impact: str
    automation_exposure: float = Field(ge=0, le=100)
    emerging_skills: list[str]
    salary_growth_rate: float
    data_status: MarketDataStatus
    data_source: str
    data_confidence: float = Field(ge=0, le=1)
    last_updated: datetime


class CareerSwitchRead(BaseModel):
    current_career: CareerRead
    target_career: CareerRead
    market: SimulationMarket
    data_status: MarketDataStatus
    current_market: TransitionMarketRead
    target_market: TransitionMarketRead
    route: list[CareerRead]
    alternative_routes: list[list[CareerRead]]
    transition_difficulty: Literal["Easy", "Moderate", "Difficult"]
    difficulty_score: float = Field(ge=0, le=100)
    difficulty_factors: dict[str, float]
    difficulty_explanation: str
    experience_relevance: Literal["High", "Medium", "Low"]
    experience_relevance_score: float = Field(ge=0, le=100)
    skill_overlap: float = Field(ge=0, le=100)
    transferable_skills: list[TransitionSkillRead]
    assumed_skills: list[TransitionSkillRead]
    partially_transferable_skills: list[TransitionSkillRead]
    skills_to_develop: list[TransitionSkillRead]
    preparation_min_months: int = Field(ge=0)
    preparation_max_months: int = Field(ge=0)
    roadmap: list[TransitionRoadmapStageRead]
    education_guidance: str
    stayed_salary: list[TransitionSalaryPointRead]
    switched_salary: list[TransitionSalaryPointRead]
    current_responsibilities: str
    target_responsibilities: str
    current_work_style: list[str]
    target_work_style: list[str]
    current_management_responsibility: str
    target_management_responsibility: str
    explanation: str
    assumptions: list[str]


class ScenarioScoreEffect(BaseModel):
    condition: str
    label: str
    points: float
    explanation: str


class WhatIfCareerResult(BaseModel):
    career_id: str
    career_title: str
    category: str
    baseline_score: float
    scenario_score: float
    score_change: float
    score_effects: list[ScenarioScoreEffect]
    baseline_market_score: float
    scenario_market_score: float
    baseline_market: CareerMarketSignalRead
    scenario_market: CareerMarketSignalRead
    baseline_skill_gap: list[str]
    scenario_skill_gap: list[str]
    trajectory_changed: bool
    trajectory_explanation: str
    baseline_simulation: CareerSimulationRead
    scenario_simulation: CareerSimulationRead


class WhatIfComparisonRead(BaseModel):
    market: SimulationMarket
    scenario: WhatIfScenario
    careers: list[WhatIfCareerResult]
    score_basis: str
    trajectory_basis: str
    data_status: Literal["prototype_illustrative"]
    market_last_updated: datetime
