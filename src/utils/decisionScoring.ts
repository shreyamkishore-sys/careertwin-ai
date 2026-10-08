import type { Career, CareerSimulation, StudentProfile } from "../types";

export type DecisionPriorityKey =
  | "salary"
  | "growth"
  | "workLifeBalance"
  | "jobSecurity"
  | "remote"
  | "international"
  | "lowCoding"
  | "management"
  | "creativity";

export type DecisionPriorities = Record<DecisionPriorityKey, number>;

export const DECISION_SCORE_WEIGHTS = {
  careerFit: 0.2,
  skillAlignment: 0.2,
  preferenceAlignment: 0.15,
  priorityAlignment: 0.2,
  marketOpportunity: 0.15,
  aiResilience: 0.1,
} as const;

const clamp = (value: number) => Math.max(0, Math.min(100, value));
const rating = (value: number | undefined) => Number.isInteger(value) && value! >= 1 && value! <= 5 ? value! : 3;

export const PRIORITY_FACTORS: {
  key: DecisionPriorityKey;
  label: string;
  profileKey: keyof StudentProfile["priority_ratings"];
}[] = [
  { key: "salary", label: "Salary", profileKey: "salary" },
  { key: "growth", label: "Career growth", profileKey: "career_growth" },
  { key: "workLifeBalance", label: "Work-life balance", profileKey: "work_life_balance" },
  { key: "jobSecurity", label: "Job security", profileKey: "job_security" },
  { key: "remote", label: "Remote work", profileKey: "remote_work" },
  { key: "international", label: "International opportunities", profileKey: "international_opportunities" },
  { key: "lowCoding", label: "Low coding", profileKey: "low_coding" },
  { key: "management", label: "Management potential", profileKey: "management_potential" },
  { key: "creativity", label: "Creativity", profileKey: "creativity" },
];

export interface DecisionScoreBreakdown {
  careerFit: number;
  skillAlignment: number;
  preferenceAlignment: number;
  priorityAlignment: number;
  marketOpportunity: number;
  aiResilience: number;
  overall: number;
  salaryScore: number;
  growthScore: number;
  demandScore: number;
  codingIntensity: number;
  skillMatches: string[];
  skillGaps: string[];
  preferenceMatches: string[];
  preferenceConflicts: string[];
  priorityMatches: string[];
  priorityConflicts: string[];
}

function preferenceTargets(career: Career): { key: keyof StudentProfile["preference_ratings"]; target: number; label: string }[] {
  const styles = new Set(career.work_styles);
  const skills = new Set(career.relevant_skills);
  const interests = new Set(career.related_interests);
  const priorities = new Set(career.priorities);
  const targets: { key: keyof StudentProfile["preference_ratings"]; target: number; label: string }[] = [];
  const hasPeopleSignal = styles.has("collaborative") || interests.has("communication") || interests.has("helping_people");
  if (hasPeopleSignal) {
    targets.push({ key: "people_interaction", target: 100, label: "people interaction" });
  }
  if (interests.has("analytics") || interests.has("research") || skills.has("data_analysis") || skills.has("statistics")) {
    targets.push({ key: "analytical_work", target: 100, label: "analytical work" });
  }
  if (skills.has("coding")) targets.push({ key: "coding", target: 100, label: "coding" });
  else if (skills.has("data_analysis")) targets.push({ key: "coding", target: 50, label: "coding" });
  else targets.push({ key: "coding", target: 0, label: "coding" });
  if (interests.has("design_creativity") || skills.has("design") || skills.has("visual_design") || priorities.has("creativity")) {
    targets.push({ key: "creativity", target: 100, label: "creative work" });
  }
  if (interests.has("leadership") || priorities.has("growth")) {
    targets.push({ key: "management", target: 100, label: "management" });
  }
  if (styles.has("remote_ready")) targets.push({ key: "remote_work", target: 100, label: "remote work" });
  if (styles.has("structured") || styles.has("flexible")) {
    targets.push({ key: "structured_work", target: styles.has("structured") && styles.has("flexible") ? 50 : styles.has("structured") ? 100 : 0, label: "structured work" });
  }
  if (skills.has("problem_solving")) targets.push({ key: "problem_solving", target: 100, label: "problem solving" });
  if (interests.has("business_strategy")) targets.push({ key: "strategic_thinking", target: 100, label: "strategic thinking" });
  return targets;
}

export function scoreDecisionCareer({
  career,
  profile,
  simulation,
  maximumSalary,
  priorities,
  aiResilience,
}: {
  career: Career;
  profile: StudentProfile;
  simulation?: CareerSimulation;
  maximumSalary: number;
  priorities: DecisionPriorities;
  aiResilience?: number;
}): DecisionScoreBreakdown {
  const careerFit = clamp(career.fit_score);
  const requirements = career.skill_requirements ?? [];
  const skillValues = requirements.map((item) => {
    const currentRating = rating(profile.skill_ratings?.[item.skill_key] ?? item.current_rating);
    return {
      ...item,
      current_rating: currentRating,
      score: clamp((currentRating / Math.max(1, item.required_rating)) * 100),
    };
  });
  const skillAlignment = skillValues.length
    ? skillValues.reduce((sum, item) => sum + item.score, 0) / skillValues.length
    : 50;
  const skillMatches = skillValues.filter((item) => item.current_rating >= item.required_rating).map((item) => `${item.skill} (${item.current_rating}/5)`);
  const skillGaps = skillValues.filter((item) => item.current_rating < item.required_rating).map((item) => `${item.skill} ${item.current_rating}/5 vs ${item.required_rating}/5 required`);

  const targets = preferenceTargets(career);
  const preferenceResults = targets.map((item) => {
    const preference = rating(profile.preference_ratings?.[item.key]);
    const preferenceLevel = (preference - 1) * 25;
    return { ...item, score: 100 - Math.abs(preferenceLevel - item.target), preference };
  });
  const preferenceAlignment = preferenceResults.length
    ? preferenceResults.reduce((sum, item) => sum + item.score, 0) / preferenceResults.length
    : 50;
  const preferenceMatches = preferenceResults.filter((item) => item.score >= 75).map((item) => `${item.label} preference`);
  const preferenceConflicts = preferenceResults.filter((item) => item.score < 50).map((item) => `${item.label} preference`);
  const codingIntensity = targets.find((item) => item.key === "coding")?.target ?? 50;

  const salary = simulation?.years[simulation.years.length - 1]?.salary_mid ?? career.market_outlook.salary_high;
  const salaryScore = clamp((salary / Math.max(1, maximumSalary)) * 100);
  const growthScore = clamp(50 + career.market_outlook.salary_growth_rate * 5 + career.market_outlook.market_growth * 2);
  const demandScore = clamp(career.market_outlook.demand_index);
  const prioritySignals: Record<DecisionPriorityKey, number> = {
    salary: salaryScore,
    growth: growthScore,
    workLifeBalance: career.priorities.includes("work_life_balance") ? 100 : 50,
    jobSecurity: demandScore,
    remote: career.work_styles.includes("remote_ready") ? 100 : 50,
    international: career.priorities.includes("international_opportunities") ? 100 : 50,
    lowCoding: 100 - codingIntensity,
    management: career.related_interests.includes("leadership") || career.priorities.includes("growth") ? 100 : 50,
    creativity: career.priorities.includes("creativity") || career.related_interests.includes("design_creativity") ? 100 : 50,
  };
  const priorityWeight = PRIORITY_FACTORS.reduce((sum, factor) => sum + priorities[factor.key], 0) || 1;
  const priorityAlignment = PRIORITY_FACTORS.reduce(
    (sum, factor) => sum + prioritySignals[factor.key] * priorities[factor.key],
    0,
  ) / priorityWeight;
  const priorityMatches = PRIORITY_FACTORS.filter((factor) => priorities[factor.key] >= 4 && prioritySignals[factor.key] >= 75).map((factor) => factor.label);
  const priorityConflicts = PRIORITY_FACTORS.filter((factor) => priorities[factor.key] >= 4 && prioritySignals[factor.key] < 50).map((factor) => factor.label);
  const marketOpportunity = (salaryScore + growthScore + demandScore) / 3;
  const resilience = clamp(aiResilience ?? 50);
  const overall = Math.round(
    careerFit * DECISION_SCORE_WEIGHTS.careerFit
    + skillAlignment * DECISION_SCORE_WEIGHTS.skillAlignment
    + preferenceAlignment * DECISION_SCORE_WEIGHTS.preferenceAlignment
    + priorityAlignment * DECISION_SCORE_WEIGHTS.priorityAlignment
    + marketOpportunity * DECISION_SCORE_WEIGHTS.marketOpportunity
    + resilience * DECISION_SCORE_WEIGHTS.aiResilience,
  );

  return {
    careerFit,
    skillAlignment,
    preferenceAlignment,
    priorityAlignment,
    marketOpportunity,
    aiResilience: resilience,
    overall,
    salaryScore,
    growthScore,
    demandScore,
    codingIntensity,
    skillMatches,
    skillGaps,
    preferenceMatches,
    preferenceConflicts,
    priorityMatches,
    priorityConflicts,
  };
}
