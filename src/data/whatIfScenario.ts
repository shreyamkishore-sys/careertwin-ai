import type { WhatIfScenario } from "../types";

export function createDefaultWhatIfScenario(): WhatIfScenario {
  return {
    avoid_coding: false,
    higher_salary: false,
    work_life_balance: false,
    remote_work: false,
    international_opportunities: false,
    willing_mba: false,
    learn_technical_skills: false,
    faster_growth: false,
    increase_demand: false,
    decrease_demand: false,
    increase_ai_adoption: false,
    decrease_ai_adoption: false,
    increase_salary_growth: false,
    decrease_salary_growth: false,
    emerging_skills_important: false,
  };
}
