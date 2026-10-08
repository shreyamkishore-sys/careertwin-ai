from datetime import datetime, timezone

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Career, StudentProfile, User
from app.services.auth import current_user_dependency
from app.schemas import (
    CareerRead,
    CareerSimulationsRead,
    CareerTwinRead,
    CareerSwitchInput,
    CareerSwitchRead,
    AIRiskAnalysisInput,
    AIRiskAnalysisRead,
    AIRiskCatalogRead,
    MarketCatalogRead,
    MarketCode,
    MarketIntelligenceRead,
    MarketRefreshRead,
    StudentProfileInput,
    StudentProfileRead,
    WhatIfComparisonRead,
    WhatIfScenario,
)
from app.services.career_twin import generate_career_twin
from app.services.career_switch import analyze_career_switch
from app.services.ai_risk import analyze_ai_risk, list_ai_risk_careers
from app.services.market_service import (
    apply_demo_market_update,
    enrich_simulations_with_market,
    market_catalog,
    market_intelligence,
    market_records,
    reset_demo_market_update,
)
from app.services.simulation import build_career_simulations
from app.services.what_if import compare_what_if

router = APIRouter(dependencies=[Depends(current_user_dependency)])


def _owned_profile(session: Session, profile_id: int, user: User) -> StudentProfile:
    profile = session.scalar(
        select(StudentProfile).where(
            StudentProfile.id == profile_id,
            StudentProfile.user_id == user.id,
        )
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    return profile


@router.get("/ai-risk", response_model=AIRiskCatalogRead, tags=["AI risk"])
def get_ai_risk_catalog(
    market: MarketCode = Query(default="IN"),
    session: Session = Depends(get_db),
) -> AIRiskCatalogRead:
    try:
        return list_ai_risk_careers(session, market)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post(
    "/ai-risk/{career_id}/analysis",
    response_model=AIRiskAnalysisRead,
    tags=["AI risk"],
)
def run_ai_risk_analysis(
    career_id: str,
    request: AIRiskAnalysisInput,
    session: Session = Depends(get_db),
    user: User = Depends(current_user_dependency),
) -> AIRiskAnalysisRead:
    profile = _owned_profile(session, request.profile_id, user)
    try:
        return analyze_ai_risk(session, career_id, profile, request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post(
    "/career-switch",
    response_model=CareerSwitchRead,
    tags=["career switching"],
)
def run_career_switch(
    request: CareerSwitchInput,
    session: Session = Depends(get_db),
    user: User = Depends(current_user_dependency),
) -> CareerSwitchRead:
    profile = _owned_profile(session, request.profile_id, user)
    try:
        return analyze_career_switch(session, profile, request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "careertwin-ai"}


@router.get("/markets", response_model=MarketCatalogRead, tags=["labor-market intelligence"])
def list_markets() -> MarketCatalogRead:
    return MarketCatalogRead(markets=market_catalog())


@router.get(
    "/market-intelligence",
    response_model=MarketIntelligenceRead,
    tags=["labor-market intelligence"],
)
def get_market_intelligence(
    market: MarketCode = Query(default="IN"),
    session: Session = Depends(get_db),
) -> MarketIntelligenceRead:
    try:
        return market_intelligence(session, market)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post(
    "/profiles/{profile_id}/market-intelligence/{market}/demo-update",
    response_model=MarketRefreshRead,
    tags=["labor-market intelligence"],
)
def demo_market_update(
    profile_id: int,
    market: Literal["IN", "US"],
    career_id: str = Query(default="product-analyst"),
    action: Literal["apply", "reset"] = Query(default="apply"),
    session: Session = Depends(get_db),
    user: User = Depends(current_user_dependency),
) -> MarketRefreshRead:
    profile = _owned_profile(session, profile_id, user)
    try:
        before_twin = generate_career_twin(session, profile, market)
        before_career = next(
            (career for career in before_twin.career_options if career.id == career_id), None
        )
        if before_career is None:
            raise ValueError(f"Unknown career '{career_id}'.")
        before_rank = next(
            index for index, career in enumerate(before_twin.career_options, start=1)
            if career.id == career_id
        )
        before_fit = before_career.fit_score
        if action == "reset":
            before_snapshot, updated_record, updated_at = reset_demo_market_update(session, market, career_id)
        else:
            before_snapshot, updated_record, updated_at = apply_demo_market_update(session, market, career_id)
        before_demand = before_snapshot.job_demand
        after_twin = generate_career_twin(session, profile, market)
        after_career = next(
            career for career in after_twin.career_options if career.id == career_id
        )
        after_rank = next(
            index for index, career in enumerate(after_twin.career_options, start=1)
            if career.id == career_id
        )
        return MarketRefreshRead(
            market=after_twin.market,
            action=action,
            career_id=career_id,
            before_demand=before_demand,
            after_demand=updated_record.job_demand,
            before_fit_score=before_fit,
            after_fit_score=after_career.fit_score,
            before_rank=before_rank,
            after_rank=after_rank,
            changed_factors=[
                f"Demand index ({before_snapshot.demand_index:g} → {updated_record.demand_index:g})",
                f"Demand trend ({before_snapshot.demand_trend} → {updated_record.demand_trend})",
                f"Hiring trend ({before_snapshot.hiring_trend} → {updated_record.hiring_trend})",
            ],
            explanation=(
                f"{after_career.title} fit changed from {before_fit:g} to "
                f"{after_career.fit_score:g} because its illustrative demand index "
                f"changed from {before_snapshot.demand_index:g} to {updated_record.demand_index:g}/100, "
                f"demand trend changed from {before_snapshot.demand_trend} to "
                f"{updated_record.demand_trend}, and hiring trend changed from "
                f"{before_snapshot.hiring_trend} to {updated_record.hiring_trend}. "
                "Profile alignment and all other market signals were held constant; "
                "the weighted market component was recalculated."
            ),
            updated_at=updated_at,
            career_twin=after_twin,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/careers", response_model=list[CareerRead], tags=["careers"])
def list_careers(session: Session = Depends(get_db)) -> list[Career]:
    return list(session.scalars(select(Career).order_by(Career.category, Career.title)))


@router.get("/simulations", response_model=CareerSimulationsRead, tags=["simulations"])
def get_career_simulations(
    market: Literal["IN", "US"] = Query(default="IN"),
    session: Session = Depends(get_db),
) -> CareerSimulationsRead:
    careers = list(session.scalars(select(Career).order_by(Career.title)))
    selected_market, simulations = build_career_simulations(careers, market)
    records = market_records(session, market)
    return CareerSimulationsRead(
        market=selected_market,
        salary_basis=(
            "Illustrative scenario-based annual salary ranges in nominal local currency; "
            "not predictions or guarantees. "
            "Year-by-year values are linearly interpolated between sample career-stage estimates; "
            "they exclude bonus, tax, inflation, location-level variation, and individual outcomes."
        ),
        careers=enrich_simulations_with_market(simulations, records),
    )


@router.post(
    "/profiles/{profile_id}/what-if",
    response_model=WhatIfComparisonRead,
    tags=["what-if simulator"],
)
def run_what_if(
    profile_id: int,
    scenario: WhatIfScenario,
    market: Literal["IN", "US"] = Query(default="IN"),
    session: Session = Depends(get_db),
    user: User = Depends(current_user_dependency),
) -> WhatIfComparisonRead:
    profile = _owned_profile(session, profile_id, user)
    careers = list(session.scalars(select(Career).order_by(Career.title)))
    if not careers:
        raise HTTPException(status_code=503, detail="The local career catalog is unavailable.")
    return compare_what_if(
        profile,
        careers,
        market,
        scenario,
        market_records(session, market),
    )


@router.post(
    "/profiles",
    response_model=StudentProfileRead,
    status_code=status.HTTP_201_CREATED,
    tags=["profiles"],
)
def create_profile(
    profile_data: StudentProfileInput,
    session: Session = Depends(get_db),
    user: User = Depends(current_user_dependency),
) -> StudentProfile:
    existing = session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Your account already has a saved profile.")
    profile = StudentProfile(
        user_id=user.id,
        **profile_data.model_dump(),
        created_at=datetime.now(timezone.utc),
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/profiles/{profile_id}", response_model=StudentProfileRead, tags=["profiles"])
def get_profile(
    profile_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(current_user_dependency),
) -> StudentProfile:
    return _owned_profile(session, profile_id, user)


@router.put("/profiles/{profile_id}", response_model=StudentProfileRead, tags=["profiles"])
def update_profile(
    profile_id: int,
    profile_data: StudentProfileInput,
    session: Session = Depends(get_db),
    user: User = Depends(current_user_dependency),
) -> StudentProfile:
    profile = _owned_profile(session, profile_id, user)
    for field, value in profile_data.model_dump().items():
        setattr(profile, field, value)
    session.commit()
    session.refresh(profile)
    return profile


@router.post(
    "/profiles/{profile_id}/careertwin",
    response_model=CareerTwinRead,
    tags=["career twin"],
)
def create_career_twin(
    profile_id: int,
    market: Literal["IN", "US"] = Query(default="IN"),
    session: Session = Depends(get_db),
    user: User = Depends(current_user_dependency),
) -> CareerTwinRead:
    profile = _owned_profile(session, profile_id, user)
    return generate_career_twin(session, profile, market)
