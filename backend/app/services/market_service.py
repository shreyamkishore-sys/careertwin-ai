from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.market_data import CAREER_MARKET_SEED_DATA, ai_label, demand_label
from app.data.markets import MARKET_CATALOG, MARKET_DATA_STATUS
from app.models import Career, CareerMarketData
from app.schemas import (
    CareerMarketSignalRead,
    CareerSimulationRead,
    MarketCatalogEntry,
    MarketFitBreakdown,
    MarketIntelligenceRead,
)
from app.services.profile_ratings import SKILL_KEYS, SKILL_TAG_TO_RATING, normalize_ratings

PROFILE_SCORE_WEIGHT = 0.85
MARKET_SCORE_WEIGHT = 0.15
TREND_SCORE = {"rising": 100.0, "stable": 50.0, "declining": 0.0}


class MarketDataProvider(Protocol):
    name: str

    def get_for_market(self, session: Session, market_code: str) -> list[CareerMarketData]: ...

    def get_for_career(
        self, session: Session, market_code: str, career_id: str
    ) -> CareerMarketData | None: ...

    def last_updated(self, records: list[CareerMarketData]) -> datetime: ...

    def provenance(self, record: CareerMarketData) -> tuple[str, float, str]: ...

    def update_record(self, session: Session, record: CareerMarketData) -> CareerMarketData: ...

    def refresh_market(
        self, session: Session, market_code: str, records: list[CareerMarketData]
    ) -> list[CareerMarketData]: ...


class LocalMarketDataProvider:
    name = "local_illustrative_dataset"

    def get_for_market(self, session: Session, market_code: str) -> list[CareerMarketData]:
        return list(
            session.scalars(
                select(CareerMarketData)
                .where(CareerMarketData.market_code == market_code)
                .order_by(CareerMarketData.career_id)
            )
        )

    def get_for_career(
        self, session: Session, market_code: str, career_id: str
    ) -> CareerMarketData | None:
        return session.scalar(
            select(CareerMarketData).where(
                CareerMarketData.market_code == market_code,
                CareerMarketData.career_id == career_id,
            )
        )

    def last_updated(self, records: list[CareerMarketData]) -> datetime:
        return latest_market_update(records)

    def provenance(self, record: CareerMarketData) -> tuple[str, float, str]:
        return record.data_source, record.data_confidence, record.data_status

    def update_record(self, session: Session, record: CareerMarketData) -> CareerMarketData:
        session.add(record)
        session.flush()
        return record

    def refresh_market(
        self, session: Session, market_code: str, records: list[CareerMarketData]
    ) -> list[CareerMarketData]:
        if any(record.market_code != market_code for record in records):
            raise ValueError(f"All refreshed records must belong to market '{market_code}'.")
        career_ids = [record.career_id for record in records]
        if len(career_ids) != len(set(career_ids)):
            raise ValueError("A market refresh cannot contain duplicate career records.")
        current_records = {
            record.career_id: record for record in self.get_for_market(session, market_code)
        }
        refreshed_at = datetime.now(timezone.utc)
        for updated in records:
            updated.last_updated = refreshed_at
            existing = current_records.get(updated.career_id)
            if existing is None:
                session.add(updated)
                continue
            for column in CareerMarketData.__table__.columns:
                if column.primary_key or column.name in {"career_id", "market_code"}:
                    continue
                setattr(existing, column.name, getattr(updated, column.name))
        session.flush()
        return self.get_for_market(session, market_code)


_provider: MarketDataProvider = LocalMarketDataProvider()


def latest_market_update(records: list[CareerMarketData]) -> datetime:
    return max(
        (
            record.last_updated.replace(tzinfo=timezone.utc)
            if record.last_updated.tzinfo is None
            else record.last_updated.astimezone(timezone.utc)
            for record in records
        )
    )


def set_market_data_provider(provider: MarketDataProvider) -> None:
    global _provider
    _provider = provider


def market_catalog() -> list[MarketCatalogEntry]:
    return [MarketCatalogEntry(**entry) for entry in MARKET_CATALOG]


def market_entry(market_code: str) -> MarketCatalogEntry:
    entry = next((item for item in MARKET_CATALOG if item["code"] == market_code), None)
    if entry is None:
        raise ValueError(f"Unknown market '{market_code}'.")
    result = MarketCatalogEntry(**entry)
    if not result.available:
        raise ValueError(
            f"{result.label} is not configured yet. Add a reviewed local market dataset first."
        )
    return result


def market_records(
    session: Session,
    market_code: str,
) -> dict[str, CareerMarketData]:
    market_entry(market_code)
    rows = _provider.get_for_market(session, market_code)
    if not rows:
        raise RuntimeError(f"No market data is configured for '{market_code}'.")
    return {row.career_id: row for row in rows}


def market_intelligence(
    session: Session,
    market_code: str,
) -> MarketIntelligenceRead:
    selected_market = market_entry(market_code)
    records = market_records(session, market_code)
    latest_record = max(
        records.values(),
        key=lambda record: (
            record.last_updated.replace(tzinfo=timezone.utc)
            if record.last_updated.tzinfo is None
            else record.last_updated.astimezone(timezone.utc)
        ),
    )
    _, _, status = _provider.provenance(latest_record)
    description = (
        "Illustrative prototype data: synthetic local demonstration values, not sourced from "
        "observed labor-market data. No live feed is connected."
        if status == "prototype_illustrative"
        else "Market information is labeled according to its source and confidence metadata."
    )
    return MarketIntelligenceRead(
        market=selected_market,
        data_status=status,
        provider=_provider.name,
        last_updated=_provider.last_updated(list(records.values())),
        description=description,
        careers=[
            CareerMarketSignalRead.model_validate(record)
            for record in records.values()
        ],
    )


def evaluate_market_fit(
    record: CareerMarketData,
    profile_skills: list[str],
    emerging_skills_important: bool = False,
    profile_skill_ratings: dict[str, int] | None = None,
) -> MarketFitBreakdown:
    tags = record.emerging_skill_tags
    if profile_skill_ratings:
        ratings = normalize_ratings(profile_skill_ratings, SKILL_KEYS)
        def rating_for(tag: str) -> int | None:
            key = tag if tag in ratings else SKILL_TAG_TO_RATING.get(tag)
            return ratings.get(key) if key else (4 if tag in profile_skills else None)
        skill_match_score = 100.0 * sum((rating_for(tag) or 0) / 5 for tag in tags) / len(tags) if tags else 50.0
        gaps = [skill for skill, tag in zip(record.emerging_skills, tags) if (rating_for(tag) or 0) < 4]
    else:
        skill_match_score = 100.0 * sum(tag in profile_skills for tag in tags) / len(tags) if tags else 50.0
        gaps = [skill for skill, tag in zip(record.emerging_skills, tags) if tag not in profile_skills]
    salary_growth_score = max(
        0.0,
        min(100.0, ((record.salary_growth_rate + 5.0) / 20.0) * 100.0),
    )
    components = {
        "job_demand": record.demand_index,
        "demand_trend": TREND_SCORE[record.demand_trend],
        "salary_growth": salary_growth_score,
        "hiring_trend": TREND_SCORE[record.hiring_trend],
        "ai_resilience": 100.0 - record.automation_exposure,
        "emerging_skill_match": skill_match_score,
    }
    weights = {
        "job_demand": 0.30,
        "demand_trend": 0.20,
        "salary_growth": 0.15,
        "hiring_trend": 0.15,
        "ai_resilience": 0.10,
        "emerging_skill_match": 0.10,
    }
    if emerging_skills_important:
        skill_weight = 0.25
        remaining_scale = (1.0 - skill_weight) / (1.0 - weights["emerging_skill_match"])
        weights = {
            key: (skill_weight if key == "emerging_skill_match" else weight * remaining_scale)
            for key, weight in weights.items()
        }

    market_score = round(
        sum(components[key] * weights[key] for key in components),
        1,
    )
    breakdown = ", ".join(
        f"{key.replace('_', ' ')} {components[key]:g} × {weights[key] * 100:g}%"
        for key in components
    )
    skill_note = (
        " Emerging skills receive 25% of the market score in this scenario."
        if emerging_skills_important
        else " Emerging skills receive 10% of the market score."
    )
    return MarketFitBreakdown(
        market_score=market_score,
        explanation=(
            f"Market alignment is a weighted 0–100 score from demand, demand trend, salary growth, "
            f"hiring, AI resilience, and emerging-skill match ({breakdown}).{skill_note}"
        ),
        components=components,
        skill_gap=gaps,
    )


def combined_career_score(profile_score: float, market_score: float) -> float:
    return round(
        profile_score * PROFILE_SCORE_WEIGHT + market_score * MARKET_SCORE_WEIGHT,
        1,
    )


def market_scenario_record(
    record: CareerMarketData,
    *,
    demand_shift: float = 0.0,
    automation_shift: float = 0.0,
    salary_growth_shift: float = 0.0,
) -> CareerMarketData:
    demand_index = max(0.0, min(100.0, record.demand_index + demand_shift))
    automation_exposure = max(
        0.0,
        min(100.0, record.automation_exposure + automation_shift),
    )
    return CareerMarketData(
        id=record.id,
        career_id=record.career_id,
        market_code=record.market_code,
        currency=record.currency,
        job_demand=demand_label(demand_index),
        demand_index=demand_index,
        demand_trend=(
            "rising" if demand_shift > 0 else
            "declining" if demand_shift < 0 else
            record.demand_trend
        ),
        salary_low=record.salary_low,
        salary_high=record.salary_high,
        salary_growth_rate=round(record.salary_growth_rate + salary_growth_shift, 1),
        ai_impact=ai_label(automation_exposure),
        automation_exposure=automation_exposure,
        emerging_skills=record.emerging_skills,
        emerging_skill_tags=record.emerging_skill_tags,
        declining_skills=record.declining_skills,
        hiring_trend=record.hiring_trend,
        market_growth=record.market_growth,
        geographic_demand=record.geographic_demand,
        possible_transition=record.possible_transition,
        data_source=record.data_source,
        data_confidence=record.data_confidence,
        data_status=record.data_status,
        last_updated=record.last_updated,
    )


def enrich_simulations_with_market(
    simulations: list[CareerSimulationRead],
    records: dict[str, CareerMarketData],
) -> list[CareerSimulationRead]:
    enriched = []
    for simulation in simulations:
        record = records[simulation.career_id]
        outlook = CareerMarketSignalRead.model_validate(record)
        stages = []
        for index, stage in enumerate(simulation.stages):
            next_stage = simulation.stages[index + 1] if index + 1 < len(simulation.stages) else None
            stages.append(
                stage.model_copy(
                    update={
                        "job_demand": record.job_demand,
                        "demand_trend": record.demand_trend,
                        "ai_impact": record.ai_impact,
                        "automation_exposure": record.automation_exposure,
                        "salary_growth_rate": record.salary_growth_rate,
                        "possible_promotion": (
                            next_stage.role if next_stage is not None and next_stage.role != stage.role else None
                        ),
                        "possible_transition": record.possible_transition,
                    }
                )
            )
        enriched.append(
            simulation.model_copy(
                update={
                    "market_outlook": outlook,
                    "stages": stages,
                    "salary_basis": (
                        "Illustrative scenario-based estimate in nominal local currency; "
                        "not a prediction or guarantee."
                    ),
                }
            )
        )
    return enriched


def seed_market_data(session: Session) -> None:
    career_ids = set(session.scalars(select(Career.id)).all())
    existing = set(
        session.execute(
            select(CareerMarketData.career_id, CareerMarketData.market_code)
        ).all()
    )
    for data in CAREER_MARKET_SEED_DATA:
        key = (data["career_id"], data["market_code"])
        if data["career_id"] not in career_ids or key in existing:
            continue
        session.add(CareerMarketData(**data))
    session.commit()


def apply_demo_market_update(
    session: Session,
    market_code: str,
    career_id: str,
) -> tuple[CareerMarketData, CareerMarketData, datetime]:
    current = _provider.get_for_career(session, market_code, career_id)
    if current is None:
        raise ValueError(f"No market data is configured for career '{career_id}' in '{market_code}'.")

    before = _snapshot_market_record(current)
    current.demand_index = 50.0
    current.job_demand = demand_label(current.demand_index)
    current.demand_trend = "declining"
    current.hiring_trend = "declining"
    current.data_source = "CareerTwin local demo update (synthetic; no external source)"
    current.data_status = MARKET_DATA_STATUS
    updated_at = datetime.now(timezone.utc)
    current.last_updated = updated_at
    updated = _provider.update_record(session, current)
    return before, updated, updated_at


def reset_demo_market_update(
    session: Session,
    market_code: str,
    career_id: str,
) -> tuple[CareerMarketData, CareerMarketData, datetime]:
    current = _provider.get_for_career(session, market_code, career_id)
    seed = next(
        (
            item for item in CAREER_MARKET_SEED_DATA
            if item["market_code"] == market_code and item["career_id"] == career_id
        ),
        None,
    )
    if current is None or seed is None:
        raise ValueError(f"No prototype baseline is configured for career '{career_id}' in '{market_code}'.")

    before = _snapshot_market_record(current)
    updated_at = datetime.now(timezone.utc)
    for key, value in seed.items():
        if key not in {"career_id", "market_code", "last_updated"}:
            setattr(current, key, value)
    current.last_updated = updated_at
    updated = _provider.update_record(session, current)
    return before, updated, updated_at


def _snapshot_market_record(record: CareerMarketData) -> CareerMarketData:
    return CareerMarketData(**{
        column.name: getattr(record, column.name)
        for column in CareerMarketData.__table__.columns
        if column.name != "id"
    })
