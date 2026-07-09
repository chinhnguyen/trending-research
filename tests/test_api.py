import pytest
from fastapi.testclient import TestClient

from willbe_trends.api.app import create_app
from willbe_trends.llm.base import LLMProvider, LLMResponse
from willbe_trends.db.repository import report_to_schema, save_report
from willbe_trends.models.search import WebCitation, WebResearchBundle
from willbe_trends.models.trends import TrendCategory, TrendReport, TrendSignal
from willbe_trends.models.usage import LLMUsageStats


@pytest.fixture()
def db_session(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("WILLBE_DATABASE_URL", f"sqlite:///{db_path}")

    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None

    db_models.init_db()
    session = db_models.SessionLocal()
    yield session
    session.close()
    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None


def test_save_and_load_report(db_session):
    report = TrendReport(
        category=TrendCategory.NAILS,
        mode="neutral",
        research_time="July 2026",
        summary="Test summary",
        trends=[
            TrendSignal(
                name="Milky French",
                description="Sheer base with crisp tips",
                popularity="rising",
                colors=["milky white"],
                techniques=["micro French"],
                tags=["minimal"],
                confidence=0.8,
                source_hint="Allure",
            )
        ],
        generated_at="2026-07-04T12:00:00+00:00",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        llm_usage=LLMUsageStats(
            prompt_tokens=1200,
            completion_tokens=450,
            total_tokens=1650,
            estimated_cost_usd=0.0024,
        ),
        web_research=WebResearchBundle(
            search_provider="duckduckgo",
            queries=["nails trends 2026"],
            citations=[
                WebCitation(
                    title="Summer nail trends",
                    url="https://www.allure.com/story/example",
                    snippet="Glazed nails are everywhere.",
                    preferred=True,
                    source_name="Allure",
                    query="nails trends 2026",
                )
            ],
        ),
    )

    row = save_report(db_session, report, region="global", web_search_enabled=True)
    loaded = report_to_schema(row)

    assert loaded.summary == "Test summary"
    assert loaded.trends[0].name == "Milky French"
    assert loaded.llm_usage is not None
    assert loaded.llm_usage.total_tokens == 1650
    assert loaded.llm_usage.estimated_cost_usd == pytest.approx(0.0024)
    assert loaded.web_research is not None
    assert loaded.web_research.citations[0].preferred is True


def test_list_and_detail_endpoints(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("WILLBE_DATABASE_URL", f"sqlite:///{db_path}")

    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None
    db_models.init_db()
    session = db_models.SessionLocal()

    report = TrendReport(
        category=TrendCategory.NAILS,
        mode="neutral",
        research_time="July 2026",
        summary="Listed summary",
        trends=[
            TrendSignal(
                name="Aura Nails",
                description="Soft gradient glow finish",
                popularity="rising",
            )
        ],
        generated_at="2026-07-04T12:00:00+00:00",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
    )
    row = save_report(session, report, region="global", web_search_enabled=True)
    session.close()

    client = TestClient(create_app())
    listing = client.get("/api/research")
    assert listing.status_code == 200
    payload = listing.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == row.id
    assert payload["items"][0]["trend_count"] == 1

    detail = client.get(f"/api/research/{row.id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["report"]["summary"] == "Listed summary"
    assert body["report"]["trends"][0]["name"] == "Aura Nails"

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None


def test_prompts_endpoints(tmp_path, monkeypatch):
    prompts_path = tmp_path / "prompts.yaml"
    monkeypatch.setenv("WILLBE_PROMPTS_PATH", str(prompts_path))
    monkeypatch.setenv("WILLBE_DATABASE_URL", "sqlite:///:memory:")

    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None

    client = TestClient(create_app())

    initial = client.get("/api/prompts")
    assert initial.status_code == 200
    body = initial.json()
    assert body["is_default"] is True
    assert "neutral_system_prompt" in body["config"]

    updated = body["config"]
    updated["neutral_system_prompt"] = "Custom neutral prompt"
    saved = client.put("/api/prompts", json=updated)
    assert saved.status_code == 200
    assert saved.json()["config"]["neutral_system_prompt"] == "Custom neutral prompt"
    assert saved.json()["is_default"] is False
    assert prompts_path.exists()

    reset = client.post("/api/prompts/reset")
    assert reset.status_code == 200
    assert reset.json()["is_default"] is True

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None


def test_sources_endpoints(tmp_path, monkeypatch):
    sources_path = tmp_path / "preferred_sources.yaml"
    monkeypatch.setenv("WILLBE_PREFERRED_SOURCES_PATH", str(sources_path))
    monkeypatch.setenv("WILLBE_DATABASE_URL", "sqlite:///:memory:")

    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None

    client = TestClient(create_app())

    initial = client.get("/api/sources")
    assert initial.status_code == 200
    body = initial.json()
    assert body["is_default"] is True
    assert len(body["config"]["sources"]) >= 1

    updated = body["config"]
    updated["sources"] = [
        {
            "name": "Example",
            "domain": "example.com",
            "weight": 1.0,
            "categories": [],
            "enabled": True,
        }
    ]
    saved = client.put("/api/sources", json=updated)
    assert saved.status_code == 200
    assert saved.json()["config"]["sources"][0]["domain"] == "example.com"
    assert saved.json()["is_default"] is False
    assert sources_path.exists()

    reset = client.post("/api/sources/reset")
    assert reset.status_code == 200
    assert reset.json()["is_default"] is True
    assert reset.json()["config"]["sources"][0]["domain"] == "allure.com"

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None


def test_health_endpoint(monkeypatch):
    monkeypatch.setenv("WILLBE_DATABASE_URL", "sqlite:///:memory:")
    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None

    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    get_settings.cache_clear()


def test_http_basic_auth_protects_site_but_not_health(monkeypatch):
    import base64

    monkeypatch.setenv("WILLBE_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("WILLBE_HTTP_AUTH_USER", "willbe")
    monkeypatch.setenv("WILLBE_HTTP_AUTH_PASSWORD", "secret-pass")
    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None
    client = TestClient(create_app())
    unauthorized = client.get("/api/research")
    assert unauthorized.status_code == 401
    assert unauthorized.headers["www-authenticate"].startswith('Basic realm="Willbe Trends"')

    health = client.get("/api/health")
    assert health.status_code == 200

    token = base64.b64encode(b"willbe:wrong-pass").decode("ascii")
    wrong_password = client.get("/api/research", headers={"Authorization": f"Basic {token}"})
    assert wrong_password.status_code == 401
    get_settings.cache_clear()


class StubBriefLLM(LLMProvider):
    name = "stub"

    async def complete(self, system: str, user: str) -> LLMResponse:
        return LLMResponse(
            content="""
            {
              "evidence_summary": "Backed by saved citations and the report summary.",
              "why_now": "The trend is timely and visible across current inspiration sources.",
              "caveats": null,
              "angles": ["Showcase the finish", "Pair with a seasonal offer", "Use a close-up reel hook"],
              "captions": [{"locale": "en", "caption": "Fresh trend, polished finish, salon-ready now.", "cta": "Book this week"}],
              "hashtags": ["#nailtrend", "#saloninspo", "#booknow"],
              "posting_tip": "Pair the caption with your latest close-up client set.",
              "service_suggestion": "Signature chrome refresh",
              "product_suggestion": "Cuticle oil add-on",
              "rationale": "The trend naturally supports both a service spotlight and retail upsell."
            }
            """,
            provider="stub",
            model="stub-model",
            usage=LLMUsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150, estimated_cost_usd=0),
        )


def test_brief_generation_and_idea_regeneration(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("WILLBE_DATABASE_URL", f"sqlite:///{db_path}")

    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models
    import willbe_trends.api.routes.briefs as brief_routes

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None
    db_models.init_db()
    session = db_models.SessionLocal()

    report = TrendReport(
        category=TrendCategory.NAILS,
        mode="neutral",
        research_time="July 2026",
        summary="Chrome and sheer finishes are leading the month.",
        trends=[
            TrendSignal(
                name="Soft Chrome",
                description="Milky bases with reflective chrome finishes.",
                popularity="rising",
                colors=["milky white", "silver"],
                techniques=["chrome powder"],
                tags=["clean girl"],
                confidence=0.86,
                source_hint="Allure",
            )
        ],
        generated_at="2026-07-04T12:00:00+00:00",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        web_research=WebResearchBundle(
            search_provider="duckduckgo",
            queries=["chrome nails july 2026"],
            citations=[
                WebCitation(
                    title="Chrome nails lead July",
                    url="https://example.com/chrome",
                    snippet="Chrome finishes and sheer milky bases keep appearing.",
                    preferred=True,
                    source_name="Example",
                    query="chrome nails july 2026",
                )
            ],
        ),
    )
    row = save_report(session, report, region="finland", web_search_enabled=True)
    session.close()

    monkeypatch.setattr(brief_routes, "create_provider", lambda provider=None, settings=None: StubBriefLLM())

    client = TestClient(create_app())

    created = client.post("/api/briefs/generate", json={"report_id": row.id})
    assert created.status_code == 200
    brief = created.json()
    assert brief["report_id"] == row.id
    assert len(brief["items"]) == 1
    assert brief["items"][0]["content_idea"]["captions"][0]["locale"] == "en"

    fetched = client.get(f"/api/briefs/{brief['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["items"][0]["trend"]["name"] == "Soft Chrome"

    latest = client.get(f"/api/briefs/latest?report_id={row.id}")
    assert latest.status_code == 200
    assert latest.json()["id"] == brief["id"]

    idea = client.post("/api/ideas/generate", json={"brief_item_id": brief["items"][0]["id"]})
    assert idea.status_code == 200
    assert idea.json()["brief_item_id"] == brief["items"][0]["id"]
    assert "hashtags" in idea.json()

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None
