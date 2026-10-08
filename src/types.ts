export type EducationLevel =
  | "high_school"
  | "undergraduate"
  | "graduate"
  | "postgraduate"
  | "other";

export type Interest =
  | "analytics"
  | "business_strategy"
  | "technology"
  | "design_creativity"
  | "helping_people"
  | "communication"
  | "leadership"
  | "research";

export type Skill =
  | "problem_solving"
  | "communication"
  | "spreadsheets"
  | "data_analysis"
  | "coding"
  | "design"
  | "writing"
  | "research"
  | "organization"
  | "teamwork"
  | "visual_design"
  | "statistics";

export type WorkPreference =
  | "collaborative"
  | "independent"
  | "structured"
  | "flexible"
  | "remote_ready";

export type CareerPriority =
  | "salary"
  | "work_life_balance"
  | "growth"
  | "remote_work"
  | "stability"
  | "impact"
  | "international_opportunities"
  | "creativity";

export interface StudentProfileInput {
  name: string;
  education_level: EducationLevel;
  field_of_study: string;
  skills: Skill[];
  skill_ratings: SkillRatings;
  interests: Interest[];
  work_preferences: WorkPreference[];
  preference_ratings: PreferenceRatings;
  career_priorities: CareerPriority[];
  priority_ratings: PriorityRatings;
}

export type Rating = 1 | 2 | 3 | 4 | 5;
export interface AuthUser {
  id: number;
  name: string;
  email: string;
  profile_id: number | null;
}

export interface SkillRatings {
  excel: Rating; sql: Rating; python: Rating; statistics: Rating; communication: Rating;
  business_knowledge: Rating; presentation: Rating; leadership: Rating; problem_solving: Rating;
  data_analysis: Rating; product_thinking: Rating; ai_literacy: Rating;
}
export interface PriorityRatings {
  salary: Rating; career_growth: Rating; work_life_balance: Rating; job_security: Rating;
  remote_work: Rating; international_opportunities: Rating; management_potential: Rating;
  creativity: Rating; low_coding: Rating;
}
export interface PreferenceRatings {
  coding: Rating; analytical_work: Rating; people_interaction: Rating; creativity: Rating;
  management: Rating; remote_work: Rating; travel: Rating; structured_work: Rating;
  problem_solving: Rating; strategic_thinking: Rating;
}

export interface StudentProfile extends StudentProfileInput {
  id: number;
  created_at: string;
}

export interface Career {
  id: string;
  title: string;
  category: string;
  summary: string;
  related_interests: Interest[];
  relevant_skills: Skill[];
  work_styles: WorkPreference[];
  priorities: CareerPriority[];
  starter_roles: string[];
  match_reasons: string[];
  is_recommended: boolean;
  fit_score: number;
  profile_fit_score: number;
  market_fit_score: number;
  market_fit_adjustment: number;
  market_explanation: string;
  market_skill_gap: string[];
  skill_requirements?: SkillProficiencyRequirement[];
  skill_gaps?: SkillProficiencyGap[];
  development_plan: CareerDevelopmentPlan;
  market_outlook: CareerMarketSignal;
  factor_contributions: FitFactorContribution[];
}

export interface FitFactorContribution {
  factor: "interests" | "skills" | "work_preferences" | "career_priorities";
  label: string;
  weight: number;
  points: number;
  matched_count: number;
  selected_count: number;
  matched_items: string[];
  unmatched_items: string[];
  explanation: string;
}

export type MarketCode = "IN" | "US" | "UK" | "CA" | "AU" | "DE";

export interface MarketCatalogEntry {
  code: MarketCode;
  label: string;
  flag: string;
  currency: string;
  currency_symbol: string;
  unit: string;
  locale: string;
  available: boolean;
  status_note: string;
}

export interface CareerMarketSignal {
  career_id: string;
  market_code: MarketCode;
  currency: string;
  job_demand: string;
  demand_index: number;
  demand_trend: "rising" | "stable" | "declining";
  salary_low: number;
  salary_high: number;
  salary_growth_rate: number;
  ai_impact: "low" | "medium" | "high";
  automation_exposure: number;
  emerging_skills: string[];
  emerging_skill_tags: string[];
  declining_skills: string[];
  hiring_trend: "rising" | "stable" | "declining";
  market_growth: number;
  geographic_demand: Record<string, string>;
  possible_transition: string;
  data_source: string;
  data_confidence: number;
  data_status: "prototype_illustrative" | "reviewed_dataset" | "live_verified";
  last_updated: string;
}

export interface MarketIntelligence {
  market: MarketCatalogEntry;
  data_status: "prototype_illustrative" | "reviewed_dataset" | "live_verified";
  provider: string;
  last_updated: string;
  description: string;
  careers: CareerMarketSignal[];
}

export interface AIRiskCatalogCareer {
  career_id: string;
  career_title: string;
  ai_impact_score: number;
  impact_level: "Low" | "Moderate" | "High" | "Very high";
  automation_exposure: number;
  ai_resilience_score: number;
  skill_change_score: number;
  opportunity_score: number;
  job_demand: string;
  demand_trend: string;
  data_status: "prototype_illustrative" | "reviewed_dataset" | "live_verified";
  data_source: string;
  data_confidence: number;
  last_updated: string;
}

export interface AIRiskCatalog {
  market: MarketCatalogEntry;
  provider: string;
  data_status: "prototype_illustrative" | "reviewed_dataset" | "live_verified";
  last_updated: string;
  careers: AIRiskCatalogCareer[];
}

export interface AIRiskScore {
  ai_impact_score: number;
  impact_level: "Low" | "Moderate" | "High" | "Very high";
  automation_exposure: number;
  ai_resilience_score: number;
  skill_change_score: number;
  opportunity_score: number;
  resilience_explanation: string;
}

export interface AIRiskTask {
  name: string;
  automation_exposure: number;
  ai_assistance_potential: number;
  human_judgment: number;
  future_importance: number;
  category: "highly_automatable" | "ai_augmented" | "human_centric" | "lower_priority";
  explanation: string;
}

export interface AIReadinessSkill {
  label: string;
  status: "ready" | "assumed" | "gap";
  weight: number;
  technical: boolean;
  current_rating: number;
  required_rating: number;
  gap: number;
}

export interface SkillProficiencyGap {
  skill: string;
  current_rating: number;
  required_rating: number;
  gap: number;
}

export interface SkillProficiencyRequirement {
  skill_key: keyof SkillRatings;
  skill: string;
  current_rating: Rating;
  required_rating: Rating;
}

export interface SkillDevelopmentPlanItem {
  skill_key: keyof SkillRatings;
  skill: string;
  current_rating: Rating;
  required_rating: Rating;
  gap: number;
  priority_score: number;
  priority: "high" | "medium" | "low";
  priority_reason: string;
  why_it_matters: string;
  suggested_action: string;
  learning_sequence: string[];
  phase: "foundation" | "core";
}

export interface SkillDevelopmentPhase {
  number: number;
  title: string;
  description: string;
  skills: string[];
}

export interface CareerDevelopmentPlan {
  career_fit_score: number;
  items: SkillDevelopmentPlanItem[];
  phases: SkillDevelopmentPhase[];
}

export interface AIReadiness {
  baseline_score: number;
  scenario_score: number;
  strengths: string[];
  gaps: string[];
  assumed_skills: string[];
  learn_next: string[];
  skill_evidence: AIReadinessSkill[];
  explanation: string;
}

export interface AIRiskMarket {
  market: MarketCatalogEntry;
  job_demand: string;
  demand_index: number;
  demand_trend: string;
  ai_impact: string;
  automation_exposure: number;
  hiring_trend: string;
  emerging_skills: string[];
  data_source: string;
  data_confidence: number;
  data_status: "prototype_illustrative" | "reviewed_dataset" | "live_verified";
  last_updated: string;
}

export interface AIRiskAnalysis {
  career: Pick<
    Career,
    "id" | "title" | "category" | "summary" | "related_interests" |
    "relevant_skills" | "work_styles" | "priorities" | "starter_roles"
  >;
  baseline: AIRiskScore;
  scenario: AIRiskScore;
  tasks: AIRiskTask[];
  future_skills: string[];
  resilient_skills: string[];
  opportunities: string[];
  risks: string[];
  readiness: AIReadiness;
  baseline_market: AIRiskMarket;
  scenario_market: AIRiskMarket;
  scenario_effects: string[];
  assumptions: string[];
}

export interface MarketRefreshResult {
  market: MarketCatalogEntry;
  action: "apply" | "reset";
  career_id: string;
  before_demand: string;
  after_demand: string;
  before_fit_score: number;
  after_fit_score: number;
  before_rank: number;
  after_rank: number;
  changed_factors: string[];
  explanation: string;
  updated_at: string;
  career_twin: CareerTwin;
}

export interface CareerTwin {
  id: number;
  generated_at: string;
  overview: string;
  profile: StudentProfile;
  market: MarketCatalogEntry;
  market_data_status: "prototype_illustrative";
  market_last_updated: string;
  score_basis: string;
  recommended_careers: Career[];
  career_options: Career[];
}

export type SimulationMarketCode = "IN" | "US";

export interface SimulationMarket {
  code: SimulationMarketCode;
  label: string;
  currency: string;
  unit: string;
  locale: string;
}

export interface CareerSimulationYear {
  year: number;
  role: string;
  salary_low: number;
  salary_mid: number;
  salary_high: number;
}

export interface CareerSimulationStage {
  year: number;
  role: string;
  skills: string[];
  job_demand: string;
  demand_trend: string;
  ai_impact: string;
  automation_exposure: number;
  salary_growth_rate: number;
  possible_promotion: string | null;
  possible_transition: string | null;
}

export interface CareerSimulation {
  career_id: string;
  career_title: string;
  category: string;
  years: CareerSimulationYear[];
  stages: CareerSimulationStage[];
  market_outlook?: CareerMarketSignal;
  salary_basis: string;
}

export interface CareerSimulations {
  market: SimulationMarket;
  salary_basis: string;
  careers: CareerSimulation[];
}

export type MarketWhatIfCondition =
  | "increase_demand"
  | "decrease_demand"
  | "increase_ai_adoption"
  | "decrease_ai_adoption"
  | "increase_salary_growth"
  | "decrease_salary_growth"
  | "emerging_skills_important";

export interface WhatIfScenario {
  avoid_coding: boolean;
  higher_salary: boolean;
  work_life_balance: boolean;
  remote_work: boolean;
  international_opportunities: boolean;
  willing_mba: boolean;
  learn_technical_skills: boolean;
  faster_growth: boolean;
  increase_demand: boolean;
  decrease_demand: boolean;
  increase_ai_adoption: boolean;
  decrease_ai_adoption: boolean;
  increase_salary_growth: boolean;
  decrease_salary_growth: boolean;
  emerging_skills_important: boolean;
}

export type TransitionLearningOption =
  | "sql"
  | "python"
  | "product_strategy"
  | "roadmapping"
  | "stakeholder_management"
  | "user_research"
  | "communication";

export interface CareerSwitchRequest {
  profile_id: number;
  current_career_id: string;
  target_career_id: string;
  market: SimulationMarketCode;
  years_before_switch: 0 | 1 | 2 | 3 | 5;
  willing_additional_education: boolean;
  learned_skills: TransitionLearningOption[];
  what_if: WhatIfScenario;
}

export interface TransitionSkill {
  label: string;
  status: "ready" | "assumed" | "partially_transferable" | "to_develop";
  evidence: string[];
  current_rating?: number | null;
  required_rating?: number | null;
  gap?: number | null;
}

export interface TransitionRoadmapStage {
  title: string;
  description: string;
  minimum_month: number;
  maximum_month: number;
}

export interface TransitionSalaryPoint {
  year: 0 | 3 | 5 | 7 | 10;
  role: string;
  salary_low: number;
  salary_mid: number;
  salary_high: number;
}

export interface TransitionMarket {
  job_demand: string;
  demand_index: number;
  demand_trend: string;
  ai_impact: string;
  automation_exposure: number;
  emerging_skills: string[];
  salary_growth_rate: number;
  data_status: "prototype_illustrative" | "reviewed_dataset" | "live_verified";
  data_source: string;
  data_confidence: number;
  last_updated: string;
}

export interface CareerSwitchAnalysis {
  current_career: Career;
  target_career: Career;
  market: SimulationMarket;
  data_status: TransitionMarket["data_status"];
  current_market: TransitionMarket;
  target_market: TransitionMarket;
  route: Career[];
  alternative_routes: Career[][];
  transition_difficulty: "Easy" | "Moderate" | "Difficult";
  difficulty_score: number;
  difficulty_factors: Record<string, number>;
  difficulty_explanation: string;
  experience_relevance: "High" | "Medium" | "Low";
  experience_relevance_score: number;
  skill_overlap: number;
  transferable_skills: TransitionSkill[];
  assumed_skills: TransitionSkill[];
  partially_transferable_skills: TransitionSkill[];
  skills_to_develop: TransitionSkill[];
  preparation_min_months: number;
  preparation_max_months: number;
  roadmap: TransitionRoadmapStage[];
  education_guidance: string;
  stayed_salary: TransitionSalaryPoint[];
  switched_salary: TransitionSalaryPoint[];
  current_responsibilities: string;
  target_responsibilities: string;
  current_work_style: string[];
  target_work_style: string[];
  current_management_responsibility: string;
  target_management_responsibility: string;
  explanation: string;
  assumptions: string[];
}

export type WhatIfCondition = keyof WhatIfScenario;

export interface ScenarioScoreEffect {
  condition: WhatIfCondition;
  label: string;
  points: number;
  explanation: string;
}

export interface WhatIfCareerResult {
  career_id: string;
  career_title: string;
  category: string;
  baseline_score: number;
  scenario_score: number;
  score_change: number;
  score_effects: ScenarioScoreEffect[];
  baseline_market_score: number;
  scenario_market_score: number;
  baseline_market: CareerMarketSignal;
  scenario_market: CareerMarketSignal;
  baseline_skill_gap: string[];
  scenario_skill_gap: string[];
  trajectory_changed: boolean;
  trajectory_explanation: string;
  baseline_simulation: CareerSimulation;
  scenario_simulation: CareerSimulation;
}

export interface WhatIfComparison {
  market: SimulationMarket;
  scenario: WhatIfScenario;
  careers: WhatIfCareerResult[];
  score_basis: string;
  trajectory_basis: string;
  data_status: "prototype_illustrative";
  market_last_updated: string;
}
