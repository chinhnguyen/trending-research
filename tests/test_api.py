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
        if "Return a fresh hook" in user:
            return LLMResponse(
                content='{"hook": "Reloaded hook for your salon feed."}',
                provider="stub",
                model="stub-model",
                usage=LLMUsageStats(prompt_tokens=20, completion_tokens=10, total_tokens=30, estimated_cost_usd=0),
            )
        if "Return a fresh caption" in user:
            return LLMResponse(
                content='{"caption": "Reloaded caption with a fresh salon angle."}',
                provider="stub",
                model="stub-model",
                usage=LLMUsageStats(prompt_tokens=20, completion_tokens=10, total_tokens=30, estimated_cost_usd=0),
            )
        if "Return a fresh hashtags" in user:
            return LLMResponse(
                content='{"hashtags": ["#freshnails", "#chromeglow", "#booknow"]}',
                provider="stub",
                model="stub-model",
                usage=LLMUsageStats(prompt_tokens=20, completion_tokens=10, total_tokens=30, estimated_cost_usd=0),
            )
        if "generation prompt as JSON" in user:
            return LLMResponse(
                content='{"prompt": "Reloaded salon chrome nail macro shot under ring light"}',
                provider="stub",
                model="stub-model",
                usage=LLMUsageStats(prompt_tokens=20, completion_tokens=10, total_tokens=30, estimated_cost_usd=0),
            )

        platform = "tiktok" if "tiktok" in user.lower() else "instagram"
        content_format = "tiktok_video" if platform == "tiktok" else "instagram_reel"
        is_regeneration = "REGENERATION REQUEST" in user
        is_video = "post format: video" in user.lower()
        image_prompt = (
            "Macro chrome nail art under moody salon lighting"
            if is_regeneration
            else "Salon manicure with soft chrome finish, clean background"
        )
        hook = (
            "A fresh angle on chrome nails for your feed."
            if is_regeneration
            else "Chrome nails that catch the light instantly."
        )
        caption = (
            "New caption: soft chrome, salon-perfect, book your glow-up."
            if is_regeneration
            else "Fresh trend, polished finish, salon-ready now."
        )
        if is_video:
            return LLMResponse(
                content=f"""
                {{
                  "evidence_summary": "Backed by saved citations and the report summary.",
                  "why_now": "The trend is timely and visible across current inspiration sources.",
                  "caveats": null,
                  "angles": ["Showcase the finish", "Pair with a seasonal offer", "Use a close-up reel hook"],
                  "captions": [{{"locale": "en", "caption": "{caption}", "cta": "Book this week"}}],
                  "hashtags": ["#nailtrend", "#saloninspo", "#booknow"],
                  "posting_tip": "Pair the caption with your latest close-up client set.",
                  "service_suggestion": "Signature chrome refresh",
                  "product_suggestion": "Cuticle oil add-on",
                  "rationale": "The trend naturally supports both a service spotlight and retail upsell.",
                  "platform_review": {{
                    "content_format": "{content_format}",
                    "strengths": ["Strong visual trend", "Clear service tie-in"],
                    "improvements": ["Add your own salon photo", "Keep hook under 3 seconds"],
                    "hook": "{hook}",
                    "caption": "{caption}",
                    "hashtags": ["#nailtrend", "#saloninspo"],
                    "posting_checklist": ["Use vertical 9:16", "Add location tag"],
                    "sound_strategy": "Soft trending instrumental",
                    "cover_tip": "Close-up chrome thumb frame"
                  }},
                  "image_recommendations": [],
                  "video_recommendations": [
                    {{
                      "label": "Reel clip",
                      "aspect_ratio": "9:16",
                      "prompt": "Vertical close-up of chrome nail art under salon ring light, slow camera push-in",
                      "duration_seconds": 8,
                      "hook": "{hook}",
                      "caption": "{caption}",
                      "hashtags": ["#nailtrend", "#saloninspo", "#booknow"],
                      "scenes": [
                        {{
                          "scene_number": 1,
                          "duration_seconds": 3,
                          "visual_prompt": "Close-up chrome nail under ring light",
                          "on_screen_text": "Trending now",
                          "voiceover": "This chrome finish is everywhere right now."
                        }}
                      ]
                    }}
                  ],
                  "video_recommendation": {{
                    "hook": "Watch the chrome catch the light",
                    "total_duration_seconds": 8,
                    "music_mood": "soft trending",
                    "scenes": []
                  }}
                }}
                """,
                provider="stub",
                model="stub-model",
                usage=LLMUsageStats(prompt_tokens=100, completion_tokens=50, total_tokens=150, estimated_cost_usd=0),
            )
        return LLMResponse(
            content=f"""
            {{
              "evidence_summary": "Backed by saved citations and the report summary.",
              "why_now": "The trend is timely and visible across current inspiration sources.",
              "caveats": null,
              "angles": ["Showcase the finish", "Pair with a seasonal offer", "Use a close-up reel hook"],
              "captions": [{{"locale": "en", "caption": "{caption}", "cta": "Book this week"}}],
              "hashtags": ["#nailtrend", "#saloninspo", "#booknow"],
              "posting_tip": "Pair the caption with your latest close-up client set.",
              "service_suggestion": "Signature chrome refresh",
              "product_suggestion": "Cuticle oil add-on",
              "rationale": "The trend naturally supports both a service spotlight and retail upsell.",
              "platform_review": {{
                "content_format": "{content_format}",
                "strengths": ["Strong visual trend", "Clear service tie-in"],
                "improvements": ["Add your own salon photo", "Keep hook under 3 seconds"],
                "hook": "{hook}",
                "caption": "{caption}",
                "hashtags": ["#nailtrend", "#saloninspo"],
                "posting_checklist": ["Use vertical 9:16", "Add location tag"],
                "sound_strategy": "Soft trending instrumental",
                "cover_tip": "Close-up chrome thumb frame"
              }},
              "image_recommendations": [
                {{
                  "label": "Hero shot",
                  "aspect_ratio": "9:16",
                  "prompt": "{image_prompt}",
                  "hook": "{hook}",
                  "caption": "{caption}",
                  "hashtags": ["#nailtrend", "#saloninspo", "#booknow"]
                }}
              ],
              "video_recommendation": {{
                "hook": "Watch the chrome catch the light",
                "total_duration_seconds": 15,
                "music_mood": "soft trending",
                "scenes": [
                  {{
                    "scene_number": 1,
                    "duration_seconds": 3,
                    "visual_prompt": "Close-up chrome nail under ring light",
                    "on_screen_text": "Trending now",
                    "voiceover": "This chrome finish is everywhere right now."
                  }}
                ]
              }}
            }}
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

    created = client.post(
        "/api/briefs/generate",
        json={"report_id": row.id, "trend_name": "Soft Chrome", "platform": "instagram"},
    )
    assert created.status_code == 200
    brief = created.json()
    assert brief["report_id"] == row.id
    assert brief["title"] == "Instagram post — Soft Chrome"
    assert len(brief["items"]) == 1
    assert brief["items"][0]["content_idea"]["platform"] == "instagram"
    assert brief["items"][0]["content_idea"]["platform_review"]["content_format"] == "instagram_reel"
    assert len(brief["items"][0]["content_idea"]["image_recommendations"]) == 1
    assert (
        brief["items"][0]["content_idea"]["image_recommendations"][0]["generation_status"]
        == "prompt_only"
    )
    assert (
        brief["items"][0]["content_idea"]["image_recommendations"][0]["hook"]
        == "Chrome nails that catch the light instantly."
    )
    assert brief["items"][0]["content_idea"]["captions"][0]["locale"] == "en"

    fetched = client.get(f"/api/briefs/{brief['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["items"][0]["trend"]["name"] == "Soft Chrome"

    latest = client.get(f"/api/briefs/latest?report_id={row.id}")
    assert latest.status_code == 200
    assert latest.json()["id"] == brief["id"]

    idea = client.post(
        "/api/ideas/generate",
        json={"brief_item_id": brief["items"][0]["id"], "platform": "tiktok"},
    )
    assert idea.status_code == 200
    assert idea.json()["active_media_job"] is None
    assert idea.json()["brief_item_id"] == brief["items"][0]["id"]
    assert idea.json()["platform"] == "tiktok"
    assert idea.json()["platform_review"]["hook"] == "A fresh angle on chrome nails for your feed."
    assert len(idea.json()["image_recommendations"]) == 2
    assert idea.json()["image_recommendations"][0]["hook"] == "Chrome nails that catch the light instantly."
    assert idea.json()["image_recommendations"][1]["hook"] == "A fresh angle on chrome nails for your feed."
    assert idea.json()["image_recommendations"][1]["caption"] == (
        "New caption: soft chrome, salon-perfect, book your glow-up."
    )
    assert idea.json()["image_recommendations"][1]["generation_status"] == "prompt_only"
    assert idea.json()["video_recommendation"]["scenes"][0]["scene_number"] == 1
    assert "hashtags" in idea.json()

    refetched = client.get(f"/api/briefs/{brief['id']}")
    assert refetched.status_code == 200
    refetched_idea = refetched.json()["items"][0]["content_idea"]
    assert refetched_idea["platform_review"]["hook"] == "A fresh angle on chrome nails for your feed."
    assert len(refetched_idea["image_recommendations"]) == 2

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None


def test_video_brief_generation(tmp_path, monkeypatch):
    db_path = tmp_path / "video-test.db"
    monkeypatch.setenv("WILLBE_DATABASE_URL", f"sqlite:///{db_path}")

    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models
    import willbe_trends.api.routes.briefs as brief_routes_module
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
            citations=[],
        ),
    )
    row = save_report(session, report, region="finland", web_search_enabled=True)
    session.close()

    monkeypatch.setattr(
        brief_routes_module,
        "create_provider",
        lambda provider=None, settings=None: StubBriefLLM(),
    )
    client = TestClient(create_app())

    created = client.post(
        "/api/briefs/generate",
        json={
            "report_id": row.id,
            "trend_name": "Soft Chrome",
            "platform": "tiktok",
            "post_format": "video",
        },
    )
    assert created.status_code == 200
    idea = created.json()["items"][0]["content_idea"]
    assert idea["post_format"] == "video"
    assert len(idea["video_recommendations"]) == 1
    assert idea["image_recommendations"] == []
    assert idea["video_recommendations"][0]["generation_status"] == "prompt_only"
    assert idea["video_recommendations"][0]["aspect_ratio"] == "9:16"

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None


def test_init_brief_shell_and_mixed_option_generation(tmp_path, monkeypatch):
    db_path = tmp_path / "init-test.db"
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
            citations=[],
        ),
    )
    row = save_report(session, report, region="finland", web_search_enabled=True)
    session.close()

    monkeypatch.setattr(brief_routes, "create_provider", lambda provider=None, settings=None: StubBriefLLM())
    client = TestClient(create_app())

    created = client.post(
        "/api/briefs/init",
        json={"report_id": row.id, "trend_name": "Soft Chrome"},
    )
    assert created.status_code == 200
    brief = created.json()
    assert brief["items"][0]["content_idea"] is None
    assert "Create post" in brief["title"]

    item_id = brief["items"][0]["id"]

    first = client.post(
        "/api/ideas/generate",
        json={"brief_item_id": item_id, "platform": "instagram", "post_format": "image"},
    )
    assert first.status_code == 200
    assert len(first.json()["image_recommendations"]) == 1
    assert first.json()["image_recommendations"][0]["platform"] == "instagram"
    assert first.json()["image_recommendations"][0]["sequence"] == 1
    assert first.json()["image_recommendations"][0]["generation_status"] == "prompt_only"
    assert first.json()["active_media_job"] is None

    second = client.post(
        "/api/ideas/generate",
        json={"brief_item_id": item_id, "platform": "tiktok", "post_format": "video"},
    )
    assert second.status_code == 200
    body = second.json()
    assert len(body["image_recommendations"]) == 1
    assert len(body["video_recommendations"]) == 1
    assert body["image_recommendations"][0]["sequence"] == 1
    assert body["video_recommendations"][0]["sequence"] == 2
    assert body["video_recommendations"][0]["platform"] == "tiktok"
    assert body["video_recommendations"][0]["generation_status"] == "prompt_only"

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None


def test_media_prompt_accept_schedules_job(tmp_path, monkeypatch):
    db_path = tmp_path / "prompt-test.db"
    monkeypatch.setenv("WILLBE_DATABASE_URL", f"sqlite:///{db_path}")

    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models
    import willbe_trends.api.routes.briefs as brief_routes
    import willbe_trends.api.routes.media_prompts as media_prompt_routes
    from datetime import datetime, timezone
    from willbe_trends.models.media_jobs import MediaJobStatus

    scheduled: list[tuple[str, int]] = []
    now = datetime.now(timezone.utc)

    def fake_schedule(*args, **kwargs):
        scheduled.append((kwargs["target_kind"], kwargs["target_sequence"]))
        return MediaJobStatus(
            id="job-1",
            status="queued",
            stage="Waiting to start…",
            progress_percent=0,
            error_message=None,
            brief_id=kwargs["brief_id"],
            brief_item_id=kwargs["brief_item_id"],
            content_idea_id=kwargs["content_idea"].id,
            target_kind=kwargs["target_kind"],
            target_sequence=kwargs["target_sequence"],
            created_at=now,
            updated_at=now,
            completed_at=None,
        )

    monkeypatch.setattr(media_prompt_routes, "schedule_media_job_for_option", fake_schedule)

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
            )
        ],
        generated_at="2026-07-04T12:00:00+00:00",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        web_research=WebResearchBundle(
            search_provider="duckduckgo",
            queries=["chrome nails july 2026"],
            citations=[],
        ),
    )
    row = save_report(session, report, region="finland", web_search_enabled=True)
    session.close()

    monkeypatch.setattr(brief_routes, "create_provider", lambda provider=None, settings=None: StubBriefLLM())
    client = TestClient(create_app())

    created = client.post(
        "/api/briefs/init",
        json={"report_id": row.id, "trend_name": "Soft Chrome"},
    )
    item_id = created.json()["items"][0]["id"]
    idea = client.post(
        "/api/ideas/generate",
        json={"brief_item_id": item_id, "platform": "instagram", "post_format": "image"},
    )
    content_idea_id = idea.json()["id"]
    sequence = idea.json()["image_recommendations"][0]["sequence"]

    accepted = client.post(
        "/api/media-prompts/accept",
        json={"content_idea_id": content_idea_id, "kind": "image", "sequence": sequence},
    )
    assert accepted.status_code == 200
    assert accepted.json()["image_recommendations"][0]["generation_status"] == "generating"
    assert accepted.json()["active_media_job"]["status"] == "queued"
    assert scheduled == [("image", sequence)]

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None


def test_media_prompt_regenerate_copy_fields(tmp_path, monkeypatch):
    db_path = tmp_path / "copy-regen-test.db"
    monkeypatch.setenv("WILLBE_DATABASE_URL", f"sqlite:///{db_path}")

    from willbe_trends.config import get_settings
    import willbe_trends.db.models as db_models
    import willbe_trends.api.routes.briefs as brief_routes
    import willbe_trends.api.routes.media_prompts as media_prompt_routes

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
            )
        ],
        generated_at="2026-07-04T12:00:00+00:00",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        web_research=WebResearchBundle(
            search_provider="duckduckgo",
            queries=["chrome nails july 2026"],
            citations=[],
        ),
    )
    row = save_report(session, report, region="finland", web_search_enabled=True)
    session.close()

    stub = StubBriefLLM()
    monkeypatch.setattr(brief_routes, "create_provider", lambda provider=None, settings=None: stub)
    monkeypatch.setattr(media_prompt_routes, "create_provider", lambda provider=None, settings=None: stub)
    client = TestClient(create_app())

    created = client.post(
        "/api/briefs/init",
        json={"report_id": row.id, "trend_name": "Soft Chrome"},
    )
    item_id = created.json()["items"][0]["id"]
    idea = client.post(
        "/api/ideas/generate",
        json={"brief_item_id": item_id, "platform": "instagram", "post_format": "image"},
    )
    content_idea_id = idea.json()["id"]
    sequence = idea.json()["image_recommendations"][0]["sequence"]

    hook = client.post(
        "/api/media-prompts/regenerate",
        json={"content_idea_id": content_idea_id, "kind": "image", "sequence": sequence, "field": "hook"},
    )
    assert hook.status_code == 200
    assert hook.json()["image_recommendations"][0]["hook"] == "Reloaded hook for your salon feed."

    caption = client.post(
        "/api/media-prompts/regenerate",
        json={"content_idea_id": content_idea_id, "kind": "image", "sequence": sequence, "field": "caption"},
    )
    assert caption.status_code == 200
    assert caption.json()["image_recommendations"][0]["caption"] == "Reloaded caption with a fresh salon angle."

    hashtags = client.post(
        "/api/media-prompts/regenerate",
        json={"content_idea_id": content_idea_id, "kind": "image", "sequence": sequence, "field": "hashtags"},
    )
    assert hashtags.status_code == 200
    assert hashtags.json()["image_recommendations"][0]["hashtags"] == ["#freshnails", "#chromeglow", "#booknow"]

    get_settings.cache_clear()
    db_models._engine = None
    db_models._session_factory = None
