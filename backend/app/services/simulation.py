from app.data.career_simulations import CAREER_SIMULATION_DATA, SIMULATION_MARKETS
from app.models import Career
from app.schemas import (
    CareerSimulationRead,
    CareerSimulationStage,
    CareerSimulationYear,
    SimulationMarket,
)


def _interpolate_salary(
    milestones: list[dict],
    year: int,
    key: str,
    precision: int,
) -> float:
    for left, right in zip(milestones, milestones[1:]):
        if left["year"] <= year <= right["year"]:
            progress = (year - left["year"]) / (right["year"] - left["year"])
            value = left[key] + (right[key] - left[key]) * progress
            return round(value, precision)
    return float(milestones[-1][key])


def _active_stage(stages: list[dict], year: int) -> dict:
    active = stages[0]
    for stage in stages:
        if stage["year"] > year:
            break
        active = stage
    return active


def build_career_simulations(
    careers: list[Career],
    market_code: str,
) -> tuple[SimulationMarket, list[CareerSimulationRead]]:
    market_data = SIMULATION_MARKETS[market_code]
    market = SimulationMarket(code=market_code, **market_data)
    missing_trajectories = [
        career.id for career in careers if career.id not in CAREER_SIMULATION_DATA
    ]
    if missing_trajectories:
        raise RuntimeError(
            "Illustrative salary trajectories are not configured for: "
            + ", ".join(sorted(missing_trajectories))
        )
    simulations = []

    for career in careers:
        trajectory = CAREER_SIMULATION_DATA.get(career.id)
        if trajectory is None:
            raise RuntimeError(f"Missing salary trajectory for career '{career.id}'.")

        milestones = trajectory["salary"][market_code]
        precision = 1 if market_code == "IN" else 0
        stages = trajectory["stages"]
        years = []
        for year in range(11):
            low = _interpolate_salary(milestones, year, "low", precision)
            high = _interpolate_salary(milestones, year, "high", precision)
            stage = _active_stage(stages, year)
            years.append(
                CareerSimulationYear(
                    year=year,
                    role=stage["role"],
                    salary_low=low,
                    salary_mid=round((low + high) / 2, precision),
                    salary_high=high,
                )
            )

        simulations.append(
            CareerSimulationRead(
                career_id=career.id,
                career_title=career.title,
                category=career.category,
                years=years,
                stages=[
                    CareerSimulationStage(**stage)
                    for stage in stages
                ],
            )
        )

    return market, simulations
