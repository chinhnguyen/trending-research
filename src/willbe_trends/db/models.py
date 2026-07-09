import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from willbe_trends.config import get_settings


class Base(DeclarativeBase):
    pass


class ResearchReportRow(Base):
    __tablename__ = "research_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    mode: Mapped[str] = mapped_column(String(32), index=True)
    summary: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(64), default="global")
    research_time: Mapped[str] = mapped_column(String(64), default="")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    llm_provider: Mapped[str] = mapped_column(String(32))
    llm_model: Mapped[str] = mapped_column(String(64))
    llm_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    llm_completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    llm_total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    llm_estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    web_search_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    web_search_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    web_queries_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferences_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    trends: Mapped[list["TrendSignalRow"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="TrendSignalRow.position",
    )
    citations: Mapped[list["WebCitationRow"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="WebCitationRow.position",
    )
    briefs: Mapped[list["ResearchBriefRow"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ResearchBriefRow.created_at.desc()",
    )


class TrendSignalRow(Base):
    __tablename__ = "trend_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_reports.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    popularity: Mapped[str] = mapped_column(String(32))
    colors_json: Mapped[str] = mapped_column(Text, default="[]")
    techniques_json: Mapped[str] = mapped_column(Text, default="[]")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    source_hint: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_alt: Mapped[str | None] = mapped_column(Text, nullable=True)

    report: Mapped[ResearchReportRow] = relationship(back_populates="trends")


class WebCitationRow(Base):
    __tablename__ = "web_citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_reports.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    snippet: Mapped[str] = mapped_column(Text, default="")
    preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    query: Mapped[str] = mapped_column(Text, default="")

    report: Mapped[ResearchReportRow] = relationship(back_populates="citations")


class ResearchBriefRow(Base):
    __tablename__ = "research_briefs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_reports.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(64), default="global")
    research_time: Mapped[str] = mapped_column(String(64), default="")
    llm_provider: Mapped[str] = mapped_column(String(32))
    llm_model: Mapped[str] = mapped_column(String(64))
    llm_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    llm_completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    llm_total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    llm_estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    report: Mapped[ResearchReportRow] = relationship(back_populates="briefs")
    items: Mapped[list["BriefItemRow"]] = relationship(
        back_populates="brief",
        cascade="all, delete-orphan",
        order_by="BriefItemRow.rank",
    )


class BriefItemRow(Base):
    __tablename__ = "brief_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brief_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_briefs.id", ondelete="CASCADE"), index=True
    )
    rank: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    trend_name: Mapped[str] = mapped_column(String(255))
    trend_description: Mapped[str] = mapped_column(Text)
    trend_popularity: Mapped[str] = mapped_column(String(32))
    colors_json: Mapped[str] = mapped_column(Text, default="[]")
    techniques_json: Mapped[str] = mapped_column(Text, default="[]")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    source_hint: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_alt: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_summary: Mapped[str] = mapped_column(Text, default="")
    why_now: Mapped[str] = mapped_column(Text, default="")
    caveats: Mapped[str | None] = mapped_column(Text, nullable=True)

    brief: Mapped[ResearchBriefRow] = relationship(back_populates="items")
    ideas: Mapped[list["ContentIdeaRow"]] = relationship(
        back_populates="brief_item",
        cascade="all, delete-orphan",
        order_by="ContentIdeaRow.created_at.desc()",
    )


class ContentIdeaRow(Base):
    __tablename__ = "content_ideas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    brief_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("brief_items.id", ondelete="CASCADE"), index=True
    )
    angles_json: Mapped[str] = mapped_column(Text, default="[]")
    captions_json: Mapped[str] = mapped_column(Text, default="[]")
    hashtags_json: Mapped[str] = mapped_column(Text, default="[]")
    posting_tip: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    brief_item: Mapped[BriefItemRow] = relationship(back_populates="ideas")


_engine = None
_session_factory = None


def get_engine():
    global _engine
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.willbe_database_url.startswith("sqlite") else {}
    _engine = create_engine(settings.willbe_database_url, connect_args=connect_args)
    return _engine


def get_session_factory():
    global _session_factory
    _session_factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _session_factory


def SessionLocal():
    return get_session_factory()()


def init_db() -> None:
    if get_settings().willbe_database_url.startswith("sqlite:///./"):
        from pathlib import Path

        Path("data").mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _migrate_schema(engine)


def _migrate_schema(engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "trend_signals" not in table_names:
        return

    with engine.begin() as connection:
        trend_columns = {column["name"] for column in inspector.get_columns("trend_signals")}
        for column_name, column_type in {
            "image_url": "TEXT",
            "image_source_url": "TEXT",
            "image_alt": "TEXT",
        }.items():
            if column_name not in trend_columns:
                connection.execute(
                    text(f"ALTER TABLE trend_signals ADD COLUMN {column_name} {column_type}")
                )

        if "research_reports" in table_names:
            report_columns = {column["name"] for column in inspector.get_columns("research_reports")}
            for column_name, column_type in {
                "research_time": "TEXT DEFAULT ''",
                "llm_prompt_tokens": "INTEGER DEFAULT 0",
                "llm_completion_tokens": "INTEGER DEFAULT 0",
                "llm_total_tokens": "INTEGER DEFAULT 0",
                "llm_estimated_cost_usd": "REAL DEFAULT 0.0",
            }.items():
                if column_name not in report_columns:
                    connection.execute(
                        text(f"ALTER TABLE research_reports ADD COLUMN {column_name} {column_type}")
                    )


def dumps_json(value) -> str:
    return json.dumps(value, ensure_ascii=True)


def loads_json(value: str | None, default):
    if not value:
        return default
    return json.loads(value)
