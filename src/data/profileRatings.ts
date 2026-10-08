import type { CareerPriority, PreferenceRatings, PriorityRatings, Rating, SkillRatings, StudentProfile } from "../types";

export const skillFields: { key: keyof SkillRatings; label: string }[] = [
  { key: "excel", label: "Excel" }, { key: "sql", label: "SQL" }, { key: "python", label: "Python" },
  { key: "statistics", label: "Statistics" }, { key: "communication", label: "Communication" },
  { key: "business_knowledge", label: "Business knowledge" }, { key: "presentation", label: "Presentation" },
  { key: "leadership", label: "Leadership" }, { key: "problem_solving", label: "Problem solving" },
  { key: "data_analysis", label: "Data analysis" }, { key: "product_thinking", label: "Product thinking" },
  { key: "ai_literacy", label: "AI literacy" },
];
export const priorityFields: { key: keyof PriorityRatings; label: string; legacy?: CareerPriority }[] = [
  { key: "salary", label: "Salary", legacy: "salary" }, { key: "career_growth", label: "Career growth", legacy: "growth" },
  { key: "work_life_balance", label: "Work-life balance", legacy: "work_life_balance" }, { key: "job_security", label: "Job security", legacy: "stability" },
  { key: "remote_work", label: "Remote work", legacy: "remote_work" }, { key: "international_opportunities", label: "International opportunities", legacy: "international_opportunities" },
  { key: "management_potential", label: "Management potential" }, { key: "creativity", label: "Creativity", legacy: "creativity" },
  { key: "low_coding", label: "Low coding" },
];
export const preferenceFields: { key: keyof PreferenceRatings; label: string; hint?: string; legacy?: string }[] = [
  { key: "coding", label: "Coding", hint: "1 = prefer low/no coding · 5 = enjoy technical work" },
  { key: "analytical_work", label: "Analytical work", legacy: "independent" },
  { key: "people_interaction", label: "People interaction", legacy: "collaborative" },
  { key: "creativity", label: "Creativity" }, { key: "management", label: "Management interest" },
  { key: "remote_work", label: "Remote work", legacy: "remote_ready" }, { key: "travel", label: "Travel" },
  { key: "structured_work", label: "Structured work", legacy: "structured" },
  { key: "problem_solving", label: "Problem solving" }, { key: "strategic_thinking", label: "Strategic thinking" },
];

export const DEFAULT_SKILL_RATINGS: SkillRatings = {
  excel: 3, sql: 3, python: 3, statistics: 3, communication: 3, business_knowledge: 3,
  presentation: 3, leadership: 3, problem_solving: 3, data_analysis: 3, product_thinking: 3, ai_literacy: 3,
};
export const DEFAULT_PREFERENCE_RATINGS: PreferenceRatings = {
  coding: 3, analytical_work: 3, people_interaction: 3, creativity: 3, management: 3,
  remote_work: 3, travel: 3, structured_work: 3, problem_solving: 3, strategic_thinking: 3,
};

export function normalizeRatingRecord<T extends { [Key in keyof T]: Rating }>(
  ratings: T,
  fields: readonly { key: keyof T }[],
): T {
  const normalized = { ...ratings };
  for (const field of fields) {
    Object.assign(normalized, { [field.key]: normalizeRating(normalized[field.key]) });
  }
  return normalized;
}

export function defaultsForPriorities(profile?: StudentProfile): PriorityRatings {
  const fallback = (key: keyof PriorityRatings, legacy?: CareerPriority): Rating => {
    const current = profile?.priority_ratings?.[key];
    if (current !== undefined) return normalizeRating(current);
    return legacy && profile?.career_priorities.includes(legacy) ? 4 : 3;
  };
  return {
    salary: fallback("salary", "salary"),
    career_growth: fallback("career_growth", "growth"),
    work_life_balance: fallback("work_life_balance", "work_life_balance"),
    job_security: fallback("job_security", "stability"),
    remote_work: fallback("remote_work", "remote_work"),
    international_opportunities: fallback("international_opportunities", "international_opportunities"),
    management_potential: fallback("management_potential"),
    creativity: fallback("creativity", "creativity"),
    low_coding: fallback("low_coding"),
  };
}
export function normalizeRating(value: unknown, fallback: Rating = 3): Rating {
  const rating = typeof value === "number" ? value : Number(value);
  return Number.isInteger(rating) && rating >= 1 && rating <= 5 ? rating as Rating : fallback;
}
