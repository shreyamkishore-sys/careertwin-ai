from collections.abc import Generator
import os

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base

def _database_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("CAREERTWIN_DATABASE_URL") or "sqlite:///./careertwin.db"
    # Render and other PostgreSQL providers commonly supply one of these URL schemes.
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _database_url()
_engine_options = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_database() -> None:
    from app.models import Career

    Base.metadata.create_all(bind=engine)
    profile_columns = {column["name"] for column in inspect(engine).get_columns("student_profiles")}
    with engine.begin() as connection:
        if "user_id" not in profile_columns:
            connection.execute(
                text("ALTER TABLE student_profiles ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE")
            )
        for column, sql_type in (
            ("skill_ratings", "JSON"),
            ("preference_ratings", "JSON"),
            ("priority_ratings", "JSON"),
        ):
            if column not in profile_columns:
                if column != "user_id":
                    connection.execute(text(f"ALTER TABLE student_profiles ADD COLUMN {column} {sql_type}"))
        connection.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS uq_student_profiles_user_id ON student_profiles(user_id)")
        )
    columns = {column["name"] for column in inspect(engine).get_columns("career_market_data")}
    if "currency" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE career_market_data ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT ''")
            )
            connection.execute(
                text(
                    "UPDATE career_market_data SET currency = CASE market_code "
                    "WHEN 'IN' THEN 'INR' WHEN 'US' THEN 'USD' ELSE '' END"
                )
            )
    with SessionLocal() as session:
        from app.data.careers import CAREER_SEED_DATA

        existing_ids = set(session.scalars(select(Career.id)).all())
        for career_data in CAREER_SEED_DATA:
            if career_data["id"] not in existing_ids:
                session.add(Career(**career_data))
        session.commit()
        from app.services.market_service import seed_market_data

        seed_market_data(session)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
