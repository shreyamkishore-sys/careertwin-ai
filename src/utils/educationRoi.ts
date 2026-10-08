import type { CareerSimulation, CareerSwitchRequest } from "../types";

export type EducationPath = "full_time_mba" | "part_time_mba";

export interface EducationTrajectoryRow {
  year: number;
  workLow: number;
  work: number;
  workHigh: number;
  educationLow: number;
  education: number;
  educationHigh: number;
  cumulativeWork: number;
  cumulativeEducation: number;
  netEducation: number;
  role: string;
}

function yearValue(career: CareerSimulation | undefined, year: number, band: "low" | "mid" | "high"): number {
  if (!career?.years.length) return 0;
  const point = career.years.find((item) => item.year === year) ?? career.years[career.years.length - 1];
  return point[`salary_${band}`];
}

export function buildEducationTrajectory({
  currentCareer,
  targetCareer,
  duration,
  startAfter,
  directCost,
  postAdjustment,
  path,
}: {
  currentCareer?: CareerSimulation;
  targetCareer?: CareerSimulation;
  duration: number;
  startAfter: CareerSwitchRequest["years_before_switch"];
  directCost: number;
  postAdjustment: number;
  path: EducationPath;
}): EducationTrajectoryRow[] {
  const rows: EducationTrajectoryRow[] = [];
  let cumulativeWork = 0;
  let cumulativeEducation = 0;
  for (let year = 1; year <= 10; year++) {
    const workLow = yearValue(currentCareer, year, "low");
    const work = yearValue(currentCareer, year, "mid");
    const workHigh = yearValue(currentCareer, year, "high");
    const starts = year > startAfter;
    const studyYear = starts && year <= startAfter + duration;
    const afterStudy = starts && year > startAfter + duration;
    const targetElapsed = afterStudy ? year - startAfter - duration : 0;
    const adjustment = 1 + postAdjustment / 100;
    const educationLow = !starts ? workLow : afterStudy ? yearValue(targetCareer, targetElapsed, "low") * adjustment : path === "part_time_mba" ? workLow : 0;
    const education = !starts ? work : afterStudy ? yearValue(targetCareer, targetElapsed, "mid") * adjustment : path === "part_time_mba" ? work : 0;
    const educationHigh = !starts ? workHigh : afterStudy ? yearValue(targetCareer, targetElapsed, "high") * adjustment : path === "part_time_mba" ? workHigh : 0;
    cumulativeWork += work;
    cumulativeEducation += education;
    rows.push({
      year, workLow, work, workHigh, educationLow, education, educationHigh,
      cumulativeWork, cumulativeEducation, netEducation: cumulativeEducation - directCost,
      role: studyYear
        ? "MBA study"
        : afterStudy
          ? targetCareer?.years.find((item) => item.year === targetElapsed)?.role ?? targetCareer?.career_title ?? "Target career"
          : currentCareer?.years.find((item) => item.year === year)?.role ?? currentCareer?.career_title ?? "Work",
    });
  }
  return rows;
}
