from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    related_interests: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    relevant_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    work_styles: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    priorities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    starter_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class CareerMarketData(Base):
    __tablename__ = "career_market_data"
    __table_args__ = (
        UniqueConstraint("career_id", "market_code", name="uq_career_market_data_career_market"),
        Index("ix_career_market_data_market_code", "market_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    career_id: Mapped[str] = mapped_column(
        ForeignKey("careers.id", ondelete="CASCADE"),
        nullable=False,
    )
    market_code: Mapped[str] = mapped_column(String(2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    job_demand: Mapped[str] = mapped_column(String(16), nullable=False)
    demand_index: Mapped[float] = mapped_column(Float, nullable=False)
    demand_trend: Mapped[str] = mapped_column(String(16), nullable=False)
    salary_low: Mapped[float] = mapped_column(Float, nullable=False)
    salary_high: Mapped[float] = mapped_column(Float, nullable=False)
    salary_growth_rate: Mapped[float] = mapped_column(Float, nullable=False)
    ai_impact: Mapped[str] = mapped_column(String(16), nullable=False)
    automation_exposure: Mapped[float] = mapped_column(Float, nullable=False)
    emerging_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    emerging_skill_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    declining_skills: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    hiring_trend: Mapped[str] = mapped_column(String(16), nullable=False)
    market_growth: Mapped[float] = mapped_column(Float, nullable=False)
    geographic_demand: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    possible_transition: Mapped[str] = mapped_column(String(180), nullable=False)
    data_source: Mapped[str] = mapped_column(String(180), nullable=False)
    data_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    data_status: Mapped[str] = mapped_column(String(24), nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    education_level: Mapped[str] = mapped_column(String(40), nullable=False)
    field_of_study: Mapped[str] = mapped_column(String(120), nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    skill_ratings: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)
    interests: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    work_preferences: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    preference_ratings: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)
    career_priorities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    priority_ratings: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CareerTwin(Base):
    __tablename__ = "career_twins"
    __table_args__ = (UniqueConstraint("student_profile_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_profile_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    overview: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_career_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
