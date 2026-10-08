import type { CareerPriority, Interest, PreferenceRatings, PriorityRatings, Skill, SkillRatings, WorkPreference } from "../types";

export const NYRA_DEMO = {
  name: "Nyra",
  education_level: "undergraduate" as const,
  field_of_study: "Business and Economics",
  interests: ["analytics", "business_strategy"] as Interest[],
  skills: ["spreadsheets", "statistics", "communication", "problem_solving", "data_analysis"] as Skill[],
  work_preferences: ["independent", "collaborative", "remote_ready", "structured"] as WorkPreference[],
  career_priorities: ["salary", "growth", "work_life_balance", "stability", "remote_work", "international_opportunities"] as CareerPriority[],
  skill_ratings: { excel: 4, sql: 3, python: 2, statistics: 3, communication: 4, business_knowledge: 4, presentation: 4, leadership: 3, problem_solving: 4, data_analysis: 3, product_thinking: 3, ai_literacy: 2 } as SkillRatings,
  preference_ratings: { coding: 1, analytical_work: 5, people_interaction: 3, creativity: 3, management: 4, remote_work: 5, travel: 2, structured_work: 3, problem_solving: 5, strategic_thinking: 4 } as PreferenceRatings,
  priority_ratings: { salary: 5, career_growth: 5, work_life_balance: 4, job_security: 4, remote_work: 4, international_opportunities: 4, management_potential: 4, creativity: 3, low_coding: 5 } as PriorityRatings,
};
