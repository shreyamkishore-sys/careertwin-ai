import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";
import { AlertCircle, ArrowUpRight, Check, LoaderCircle, TrendingUp } from "lucide-react";
import { getCareerSimulations } from "../api";
import { useJourneyState } from "../state/journeySession";
import type {
  CareerSimulation as CareerSimulationPath,
  CareerTwin,
  SimulationMarket,
  SimulationMarketCode,
  WhatIfComparison,
  WhatIfScenario,
} from "../types";

const CAREER_COLORS = [
  "#55775a",
  "#c28c51",
  "#6e88a2",
  "#a26b75",
  "#8672a0",
  "#558e8a",
  "#a17c55",
];

type ChartRow = { year: number } & Record<string, number>;

interface SalaryTooltipProps extends TooltipContentProps {
  market: SimulationMarket;
  careers: CareerSimulationPath[];
  scenarioCareers: CareerSimulationPath[];
  selectedCareerIds: string[];
  formatSalary: (salary: number) => string;
}

function SalaryTooltip({
  active,
  label,
  market,
  careers,
  scenarioCareers,
  selectedCareerIds,
  formatSalary,
}: SalaryTooltipProps) {
  if (!active || label === undefined) return null;
  const year = Number(label);
  return (
    <div className="salary-tooltip">
      <span className="detail-label">YEAR {year}</span>
      {selectedCareerIds.map((careerId) => {
        const career = careers.find((item) => item.career_id === careerId);
        const scenarioCareer = scenarioCareers.find((item) => item.career_id === careerId);
        const point = career?.years.find((item) => item.year === year);
        const scenarioPoint = scenarioCareer?.years.find((item) => item.year === year);
        if (!career || !point) return null;
        const color = CAREER_COLORS[careers.indexOf(career) % CAREER_COLORS.length];
        return (
          <div className="salary-tooltip-career" key={careerId}>
            <span className="salary-tooltip-dot" style={{ background: color }} />
            <div>
              <strong>{career.career_title}</strong>
              <span>Baseline · {point.role}</span>
              <small>{formatSalary(point.salary_low)}–{formatSalary(point.salary_high)} · midpoint {formatSalary(point.salary_mid)}</small>
              {scenarioPoint && <>
                <span>Current scenario · {scenarioPoint.role}</span>
                <small>{formatSalary(scenarioPoint.salary_low)}–{formatSalary(scenarioPoint.salary_high)} · midpoint {formatSalary(scenarioPoint.salary_mid)}</small>
              </>}
            </div>
          </div>
        );
      })}
      <span className="salary-tooltip-unit">{market.unit}</span>
    </div>
  );
}

function chartData(careers: CareerSimulationPath[], scenarioCareers: CareerSimulationPath[], selectedCareerIds: string[]): ChartRow[] {
  return Array.from({ length: 11 }, (_, year) => {
    const row: ChartRow = { year };
    for (const careerId of selectedCareerIds) {
      const path = careers.find((item) => item.career_id === careerId);
      const point = path?.years.find((item) => item.year === year);
      if (!point) continue;
      row[`${careerId}_low`] = point.salary_low;
      row[`${careerId}_range`] = point.salary_high - point.salary_low;
      row[`${careerId}_mid`] = point.salary_mid;
      const scenarioPath = scenarioCareers.find((item) => item.career_id === careerId);
      const scenarioPoint = scenarioPath?.years.find((item) => item.year === year);
      if (scenarioPoint) row[`${careerId}_scenario_mid`] = scenarioPoint.salary_mid;
    }
    return row;
  });
}

function CareerMilestones({
  career,
  color,
  formatSalary,
  profileFit,
  trajectoryExplanation,
}: {
  career: CareerSimulationPath;
  color: string;
  formatSalary: (salary: number) => string;
  profileFit?: number;
  trajectoryExplanation?: string;
}) {
  const snapshotYears = [0, 1, 3, 5, 7, 10];
  return (
    <article className="simulation-career-path">
      <div className="simulation-path-heading">
        <span className="simulation-path-dot" style={{ background: color }} />
        <h3>{career.career_title}</h3>
        <span>{profileFit === undefined ? "Baseline role and salary path" : `Scenario fit ${Math.round(profileFit)}/100`}</span>
      </div>
      {trajectoryExplanation && <p className="simulation-data-note">{trajectoryExplanation}</p>}
      <div className="simulation-milestones">
        {snapshotYears.map((year) => {
          const stage = career.stages.reduce((active, candidate) => (
            candidate.year <= year ? candidate : active
          ), career.stages[0]);
          const nextStage = career.stages.find((candidate) => candidate.year > year && candidate.role !== stage.role);
          const yearPoint = career.years.find((item) => item.year === year);
          if (!yearPoint) return null;
          return (
            <div className="simulation-milestone" key={`${career.career_id}-${year}`}>
              <span className="milestone-year">{year === 0 ? "YEAR 0" : `YEAR ${year}`}</span>
              <div className="milestone-main">
                <strong>{yearPoint.role}</strong>
                <span>{formatSalary(yearPoint.salary_low)}–{formatSalary(yearPoint.salary_high)} / year</span>
                <div className="simulation-market-outlook">
                  <span><b>Demand</b> {stage.job_demand} <em>{stage.demand_trend}</em></span>
                  <span><b>AI impact</b> {stage.ai_impact} · {Math.round(stage.automation_exposure)}% exposure</span>
                  <span><b>Salary growth</b> {stage.salary_growth_rate}% scenario rate</span>
                </div>
                <div className="milestone-skills">
                  {stage.skills.map((skill) => <span key={skill}>{skill}</span>)}
                </div>
                {nextStage && <span className="simulation-promotion">Possible promotion · {nextStage.role}</span>}
                {stage.possible_transition && <span className="simulation-transition">Possible transition · {stage.possible_transition}</span>}
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}

export function CareerSimulation({
  careerTwin,
  marketCode,
  onMarketCodeChange,
  dataVersion,
  scenario,
  whatIfComparison,
  mode = "full",
}: {
  careerTwin: CareerTwin;
  marketCode: SimulationMarketCode;
  onMarketCodeChange: (market: SimulationMarketCode) => void;
  dataVersion: string;
  scenario: WhatIfScenario;
  whatIfComparison: WhatIfComparison | null;
  mode?: "full" | "salary";
}) {
  const [simulationData, setSimulationData] = useState<{
    market: SimulationMarket;
    salary_basis: string;
    careers: CareerSimulationPath[];
  } | null>(null);
  const [selectedCareerIds, setSelectedCareerIds] = useJourneyState("simulationCareerIds", () =>
    careerTwin.recommended_careers.slice(0, 3).map((career) => career.id),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getCareerSimulations(marketCode)
      .then((data) => {
        if (!active) return;
        setSimulationData(data);
        setSelectedCareerIds((current) => {
          const compatible = current.filter((id) => data.careers.some((item) => item.career_id === id));
          if (compatible.length > 0) return compatible.slice(0, 3);
          return careerTwin.recommended_careers.slice(0, 3).map((career) => career.id);
        });
      })
      .catch((requestError: unknown) => {
        if (active) setError(requestError instanceof Error ? requestError.message : "We couldn't load the career simulations.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [careerTwin.recommended_careers, marketCode, dataVersion]);

  const careers = simulationData?.careers ?? [];
  const activeComparison = whatIfComparison
    && whatIfComparison.market.code === marketCode
    && JSON.stringify(whatIfComparison.scenario) === JSON.stringify(scenario)
    ? whatIfComparison
    : null;
  const scenarioResults = activeComparison?.careers ?? [];
  const scenarioCareers = scenarioResults.map((result) => result.scenario_simulation);
  const selectedCareers = careers.filter((career) => selectedCareerIds.includes(career.career_id));
  const selectedScenarioCareers = scenarioCareers.filter((career) => selectedCareerIds.includes(career.career_id));
  const displayedCareers = selectedCareers.map((career) =>
    scenarioCareers.find((scenarioCareer) => scenarioCareer.career_id === career.career_id) ?? career,
  );
  const market = simulationData?.market;
  const rows = useMemo(() => chartData(careers, scenarioCareers, selectedCareerIds), [careers, scenarioCareers, selectedCareerIds]);
  const salaryDomain = useMemo<[number, number]>(() => {
    const allPoints = [...selectedCareers, ...selectedScenarioCareers].flatMap((career) => career.years);
    if (allPoints.length === 0) return [0, 100];
    const minimum = Math.min(...allPoints.map((point) => point.salary_low));
    const maximum = Math.max(...allPoints.map((point) => point.salary_high));
    const padding = (maximum - minimum) * 0.12;
    return [Math.max(0, Math.floor(minimum - padding)), Math.ceil(maximum + padding)];
  }, [selectedCareerIds, simulationData, selectedScenarioCareers]);
  const formatter = useMemo(() => {
    const locale = market?.locale ?? (marketCode === "IN" ? "en-IN" : "en-US");
    const currency = market?.currency ?? (marketCode === "IN" ? "INR" : "USD");
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    });
  }, [market?.currency, market?.locale, marketCode]);
  const axisFormatter = useMemo(() => new Intl.NumberFormat(
    market?.locale ?? (marketCode === "IN" ? "en-IN" : "en-US"),
    {
      style: "currency",
      currency: market?.currency ?? (marketCode === "IN" ? "INR" : "USD"),
      notation: "compact",
      maximumFractionDigits: 0,
    },
  ), [market?.currency, market?.locale, marketCode]);
  const formatSalary = (salary: number) => marketCode === "IN"
    ? `₹${salary.toFixed(1)}L`
    : formatter.format(salary);
  const axisFormat = (salary: number) => marketCode === "IN"
    ? `₹${salary}L`
    : axisFormatter.format(salary);

  function toggleCareer(careerId: string) {
    setSelectedCareerIds((current) => {
      if (current.includes(careerId)) return current.filter((item) => item !== careerId);
      if (current.length >= 3) return current;
      return [...current, careerId];
    });
  }

  return (
    <section className="simulation-section" id={mode === "salary" ? "salary-trajectory" : "simulation"}>
      <div className="dashboard-section-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> {mode === "salary" ? "SALARY TRAJECTORY" : "TRY ON A POSSIBLE FUTURE"}</div>
          <h2>{mode === "salary" ? <>Explore the earning path, <span className="serif-accent">year by year.</span></> : <>Ten years, <span className="serif-accent">many possibilities.</span></>}</h2>
        </div>
        <p>{mode === "salary" ? "Compare illustrative salary ranges and scenario changes at Years 0, 1, 3, 5, 7, and 10. These are not forecasts." : "Explore illustrative role and salary ranges with current market signals at Years 0, 1, 3, 5, 7, and 10. These are scenario-based estimates, not forecasts."}</p>
      </div>

      <div className="simulation-toolbar">
        <label className="market-selector">
          <span>Salary market</span>
          <select
            aria-label="Salary market"
            value={marketCode}
            onChange={(event) => onMarketCodeChange(event.target.value as SimulationMarketCode)}
          >
            <option value="IN">India · INR</option>
            <option value="US">United States · USD</option>
          </select>
        </label>
        <div className="simulation-legend-note"><TrendingUp size={15} /> Solid line: baseline · dashed line: current What-If scenario</div>
      </div>

      <div className="career-selectors" aria-label="Choose careers to compare">
        {careers.map((career, index) => {
          const selected = selectedCareerIds.includes(career.career_id);
          const locked = !selected && selectedCareerIds.length >= 3;
          return (
            <button
              aria-pressed={selected}
              className={`career-selector ${selected ? "career-selector-selected" : ""}`}
              disabled={locked}
              key={career.career_id}
              onClick={() => toggleCareer(career.career_id)}
              type="button"
            >
              <span className="selector-dot" style={{ background: selected ? CAREER_COLORS[index % CAREER_COLORS.length] : undefined }}>
                {selected && <Check size={11} />}
              </span>
              {career.career_title}
            </button>
          );
        })}
      </div>
      {selectedCareerIds.length >= 3 && (
        <p className="selector-hint">Compare up to three paths at a time. Remove one to add another.</p>
      )}

      {error && <p className="simulation-error" role="alert"><AlertCircle size={15} /> {error}</p>}
      {!activeComparison && !loading && <p className="simulation-data-note">Showing baseline trajectories while the current profile and What-If scenario are being calculated.</p>}
      {loading && (
        <div className="simulation-loading"><LoaderCircle size={18} /> Loading illustrative salary data…</div>
      )}
      {!loading && !error && market && selectedCareers.length > 0 && (
        <>
          <div className="simulation-chart-card">
            <div className="chart-title-row">
              <div>
                <span className="detail-label">{market.label.toUpperCase()} · ANNUAL BASE SALARY RANGE</span>
                <h3>Illustrative salary trajectories</h3>
              </div>
              <span className="chart-unit">{market.unit}</span>
            </div>
            <div className="salary-chart" role="img" aria-label={`Interactive ten-year salary trajectory comparison for ${selectedCareers.map((career) => career.career_title).join(", ")} in ${market.label}`}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={rows} margin={{ top: 12, right: 15, left: 0, bottom: 4 }}>
                  <CartesianGrid stroke="#eceee8" strokeDasharray="3 5" vertical={false} />
                  <XAxis
                    axisLine={{ stroke: "#e1e5dd" }}
                    dataKey="year"
                    tick={{ fill: "#858b82", fontSize: 10 }}
                    tickLine={false}
                    tickFormatter={(year: number) => year === 0 ? "Start" : `Y${year}`}
                    interval={1}
                  />
                  <YAxis
                    axisLine={false}
                    domain={salaryDomain}
                    tick={{ fill: "#858b82", fontSize: 10 }}
                    tickFormatter={axisFormat}
                    tickLine={false}
                    width={marketCode === "IN" ? 45 : 60}
                  />
                  <Tooltip
                    content={(props) => (
                      <SalaryTooltip
                        {...props}
                        careers={careers}
                        scenarioCareers={scenarioCareers}
                        formatSalary={formatSalary}
                        market={market}
                        selectedCareerIds={selectedCareerIds}
                      />
                    )}
                    cursor={{ stroke: "#abb6a8", strokeDasharray: "3 3" }}
                  />
                  {selectedCareers.map((career) => {
                    return (
                      <Area
                        dataKey={`${career.career_id}_low`}
                        fill="transparent"
                        fillOpacity={0}
                        isAnimationActive={false}
                        key={`${career.career_id}-base`}
                        legendType="none"
                        name={`${career.career_title} range base`}
                        stackId={career.career_id}
                        stroke="transparent"
                        type="monotone"
                      />
                    );
                  })}
                  {selectedCareers.map((career) => {
                    const color = CAREER_COLORS[careers.indexOf(career) % CAREER_COLORS.length];
                    return (
                      <Area
                        dataKey={`${career.career_id}_range`}
                        fill={color}
                        fillOpacity={0.13}
                        isAnimationActive={false}
                        key={`${career.career_id}-range`}
                        legendType="none"
                        name={`${career.career_title} range`}
                        stackId={career.career_id}
                        stroke="transparent"
                        type="monotone"
                      />
                    );
                  })}
                  {activeComparison && selectedCareers.map((career) => {
                    const color = CAREER_COLORS[careers.indexOf(career) % CAREER_COLORS.length];
                    return (
                      <Line
                        dataKey={`${career.career_id}_scenario_mid`}
                        dot={false}
                        isAnimationActive={false}
                        key={`${career.career_id}-scenario`}
                        name={`${career.career_title} · current scenario`}
                        stroke={color}
                        strokeDasharray="5 4"
                        strokeWidth={2}
                        type="monotone"
                      />
                    );
                  })}
                  {selectedCareers.map((career) => {
                    const color = CAREER_COLORS[careers.indexOf(career) % CAREER_COLORS.length];
                    return (
                      <Line
                        activeDot={{ r: 4, strokeWidth: 2, fill: "#fff" }}
                        dataKey={`${career.career_id}_mid`}
                        dot={false}
                        isAnimationActive={false}
                        key={`${career.career_id}-mid`}
                        name={career.career_title}
                        stroke={color}
                        strokeWidth={2.5}
                        type="monotone"
                      />
                    );
                  })}
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-inline-legend">
              {selectedCareers.map((career) => (
                <span key={career.career_id}>
                  <i style={{ background: CAREER_COLORS[careers.indexOf(career) % CAREER_COLORS.length] }} />
                  {career.career_title} · baseline / scenario
                </span>
              ))}
              {activeComparison && <span><i style={{ background: "#788176" }} /> Profile-aware What-If scenario · dashed</span>}
            </div>
          </div>

          {mode === "full" && <><div className="simulation-stages-heading">
            <div>
              <span className="detail-label">HOW A PATH COULD UNFOLD</span>
              <h3>Possible role & skill milestones</h3>
            </div>
            <span>Milestones are examples, not guaranteed promotions.</span>
          </div>
          <div className="simulation-path-grid">
            {displayedCareers.map((career) => {
              const result = scenarioResults.find((item) => item.career_id === career.career_id);
              return (
              <CareerMilestones
                career={career}
                color={CAREER_COLORS[careers.indexOf(career) % CAREER_COLORS.length]}
                formatSalary={formatSalary}
                key={career.career_id}
                profileFit={result?.scenario_score}
                trajectoryExplanation={result?.trajectory_explanation}
              />
              );
            })}
          </div></>}
          <p className="simulation-data-note"><ArrowUpRight size={13} /> {activeComparison?.trajectory_basis ?? simulationData?.salary_basis} Profile fit comes from your current profile and What-If assumptions; it is not converted into a salary premium. Figures remain illustrative, not salary predictions or guarantees.</p>
        </>
      )}
      {!loading && !error && selectedCareerIds.length === 0 && (
        <div className="simulation-empty">Choose at least one career above to see its possible path.</div>
      )}
    </section>
  );
}
