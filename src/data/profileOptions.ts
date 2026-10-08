import type {
  CareerPriority,
  EducationLevel,
  Interest,
  Skill,
  WorkPreference,
} from "../types";

export const educationLevels: { value: EducationLevel; label: string }[] = [
  { value: "high_school", label: "High school" },
  { value: "undergraduate", label: "Undergraduate" },
  { value: "graduate", label: "Graduate" },
  { value: "postgraduate", label: "Postgraduate" },
  { value: "other", label: "Other / still deciding" },
];

export const interests: { value: Interest; label: string }[] = [
  { value: "analytics", label: "Finding patterns & solving problems" },
  { value: "business_strategy", label: "Business & strategy" },
  { value: "technology", label: "Technology & how things work" },
  { value: "design_creativity", label: "Design & creative ideas" },
  { value: "helping_people", label: "Helping people" },
  { value: "communication", label: "Communication & storytelling" },
  { value: "leadership", label: "Leading & bringing people together" },
  { value: "research", label: "Research & asking questions" },
];

export const skills: { value: Skill; label: string }[] = [
  { value: "problem_solving", label: "Problem-solving" },
  { value: "communication", label: "Communication" },
  { value: "spreadsheets", label: "Spreadsheets" },
  { value: "data_analysis", label: "Data analysis" },
  { value: "coding", label: "Coding" },
  { value: "design", label: "Design" },
  { value: "writing", label: "Writing" },
  { value: "research", label: "Research" },
  { value: "organization", label: "Organization" },
  { value: "teamwork", label: "Teamwork" },
  { value: "visual_design", label: "Visual design" },
  { value: "statistics", label: "Statistics" },
];

export const workPreferences: { value: WorkPreference; label: string }[] = [
  { value: "collaborative", label: "Working with a team" },
  { value: "independent", label: "Independent focus time" },
  { value: "structured", label: "Clear plans & structure" },
  { value: "flexible", label: "Variety & flexibility" },
  { value: "remote_ready", label: "Remote-friendly work" },
];

export const careerPriorities: { value: CareerPriority; label: string }[] = [
  { value: "growth", label: "Career growth" },
  { value: "work_life_balance", label: "Work-life balance" },
  { value: "salary", label: "Earning potential" },
  { value: "stability", label: "Stability" },
  { value: "remote_work", label: "Remote-work options" },
  { value: "impact", label: "Meaningful impact" },
  { value: "international_opportunities", label: "International opportunities" },
  { value: "creativity", label: "Creative work" },
];
