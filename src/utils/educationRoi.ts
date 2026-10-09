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

type SalaryBand = "low" | "mid" | "high";

function yearValue(career: CareerSimulation | undefined, year: number, band: SalaryBand): number {
  if (!career?.years.length) return 0;
  const point = career.years.find((item) => item.year === year) ?? career.years[career.years.length - 1];
  return point[`salary_${band}`];
}

function educationSalary({
  currentSalary,
  targetCareer,
  year,
  startAfter,
  duration,
  path,
  adjustment,
  band,
}: {
  currentSalary: number;
  targetCareer?: CareerSimulation;
  year: number;
  startAfter: number;
  duration: number;
  path: EducationPath;
  adjustment: number;
  band: SalaryBand;
}): number {
  if (year <= startAfter) return currentSalary;
  if (year <= startAfter + duration) return path === "part_time_mba" ? currentSalary : 0;

  const targetYear = year - startAfter - duration;
  return yearValue(targetCareer, targetYear, band) * adjustment;
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
    const adjustment = 1 + postAdjustment / 100;
    const educationLow = educationSalary({ currentSalary: workLow, targetCareer, year, startAfter, duration, path, adjustment, band: "low" });
    const education = educationSalary({ currentSalary: work, targetCareer, year, startAfter, duration, path, adjustment, band: "mid" });
    const educationHigh = educationSalary({ currentSalary: workHigh, targetCareer, year, startAfter, duration, path, adjustment, band: "high" });
    const studyYear = year > startAfter && year <= startAfter + duration;
    const afterStudy = year > startAfter + duration;
    const targetElapsed = afterStudy ? year - startAfter - duration : 0;
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
