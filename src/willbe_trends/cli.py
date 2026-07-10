import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from willbe_trends.config import LLMProviderName, SearchProviderName, get_settings
from willbe_trends.llm.registry import create_provider, list_providers
from willbe_trends.models.preferences import UserPreferences
from willbe_trends.models.trends import TrendCategory, TrendReport
from willbe_trends.research.neutral import research_neutral_trends
from willbe_trends.research.personalized import research_personalized_trends
from willbe_trends.media.diagnostics import mark_image_probe_passed, run_image_generation_test

load_dotenv()

app = typer.Typer(
    no_args_is_help=True,
    help="Willbe AI trending research — neutral and personalized nail trends.",
)
console = Console()


def _resolve_provider(provider: str | None) -> LLMProviderName | None:
    if provider is None:
        return None
    normalized = provider.strip().lower()
    if normalized not in list_providers():
        raise typer.BadParameter(
            f"Unknown provider '{provider}'. Choose from: {', '.join(list_providers())}"
        )
    return normalized  # type: ignore[return-value]


def _resolve_search_provider(provider: str | None) -> SearchProviderName | None:
    if provider is None:
        return None
    normalized = provider.strip().lower()
    if normalized not in list_search_providers():
        raise typer.BadParameter(
            f"Unknown search provider '{provider}'. "
            f"Choose from: {', '.join(list_search_providers())}"
        )
    return normalized  # type: ignore[return-value]


def _render_report(report: TrendReport) -> None:
    subtitle = f"{report.llm_provider}/{report.llm_model}"
    if report.web_research and report.web_research.enabled:
        subtitle += f" · web:{report.web_research.search_provider}"
        subtitle += f" · {len(report.web_research.citations)} sources"

    console.print(
        Panel(
            report.summary,
            title=f"{report.category.value.title()} · {report.mode.title()} trends",
            subtitle=subtitle,
        )
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("Trend", style="cyan", no_wrap=True)
    table.add_column("Popularity")
    table.add_column("Description")
    table.add_column("Colors")

    for trend in report.trends:
        colors = ", ".join(trend.colors[:3]) if trend.colors else "—"
        table.add_row(trend.name, trend.popularity, trend.description, colors)

    console.print(table)

    if report.web_research and report.web_research.citations:
        source_table = Table(title="Web sources", show_header=True, header_style="bold")
        source_table.add_column("Preferred")
        source_table.add_column("Title")
        source_table.add_column("URL")
        for citation in report.web_research.citations[:5]:
            preferred = "✓" if citation.preferred else ""
            source_table.add_row(preferred, citation.title[:50], citation.url[:60])
        console.print(source_table)


def _write_output(report: TrendReport, output: Path | None) -> None:
    if output is None:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[green]Saved[/green] {output}")


@app.command("providers")
def providers_cmd() -> None:
    """List supported LLM providers."""
    settings = get_settings()
    for name in list_providers():
        marker = " (default)" if name == settings.willbe_llm_provider else ""
        console.print(f"- {name}{marker}")


@app.command("search-providers")
def search_providers_cmd() -> None:
    """List supported web search providers."""
    settings = get_settings()
    for name in list_search_providers():
        marker = " (default)" if name == settings.willbe_search_provider else ""
        console.print(f"- {name}{marker}")


@app.command("neutral")
def neutral_cmd(
    category: Annotated[
        TrendCategory, typer.Argument(help="Trend category to research")
    ] = TrendCategory.NAILS,
    provider: Annotated[
        str | None,
        typer.Option("--provider", "-p", help="LLM provider override"),
    ] = None,
    region: Annotated[
        str, typer.Option("--region", "-r", help="Geographic focus")
    ] = "global",
    time: Annotated[
        str | None,
        typer.Option("--time", "-t", help="Research time period, e.g. 'July 2026'"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write JSON report to file"),
    ] = None,
    web_search: Annotated[
        bool,
        typer.Option("--web-search/--no-web-search", help="Enable web-backed research"),
    ] = True,
    search_provider: Annotated[
        str | None,
        typer.Option("--search-provider", help="Web search provider override"),
    ] = None,
    sources: Annotated[
        Path | None,
        typer.Option(
            "--sources",
            help="Preferred sources YAML (default: config/preferred_sources.yaml)",
        ),
    ] = None,
) -> None:
    """Research neutral, category-wide trends."""
    settings = get_settings()
    if search_provider:
        settings = settings.model_copy(
            update={"willbe_search_provider": _resolve_search_provider(search_provider)}
        )
    llm = create_provider(_resolve_provider(provider))
    report = asyncio.run(
        research_neutral_trends(
            category=category,
            llm=llm,
            region=region,
            research_time=time,
            web_search=web_search,
            preferred_sources_path=sources,
            settings=settings,
        )
    )
    _render_report(report)
    _write_output(report, output)


@app.command("personalized")
def personalized_cmd(
    category: Annotated[
        TrendCategory, typer.Argument(help="Trend category to research")
    ] = TrendCategory.NAILS,
    preferences: Annotated[
        Path,
        typer.Option(
            "--preferences",
            "-f",
            help="Path to user preferences JSON",
        ),
    ] = Path("samples/user_preferences.json"),
    provider: Annotated[
        str | None,
        typer.Option("--provider", "-p", help="LLM provider override"),
    ] = None,
    region: Annotated[
        str, typer.Option("--region", "-r", help="Geographic focus")
    ] = "global",
    time: Annotated[
        str | None,
        typer.Option("--time", "-t", help="Research time period, e.g. 'July 2026'"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write JSON report to file"),
    ] = None,
    web_search: Annotated[
        bool,
        typer.Option("--web-search/--no-web-search", help="Enable web-backed research"),
    ] = True,
    search_provider: Annotated[
        str | None,
        typer.Option("--search-provider", help="Web search provider override"),
    ] = None,
    sources: Annotated[
        Path | None,
        typer.Option(
            "--sources",
            help="Preferred sources YAML (default: config/preferred_sources.yaml)",
        ),
    ] = None,
) -> None:
    """Research personalized 'you may like it' trends."""
    if not preferences.exists():
        raise typer.BadParameter(f"Preferences file not found: {preferences}")

    settings = get_settings()
    if search_provider:
        settings = settings.model_copy(
            update={"willbe_search_provider": _resolve_search_provider(search_provider)}
        )

    user_prefs = UserPreferences.model_validate_json(preferences.read_text())
    llm = create_provider(_resolve_provider(provider))
    report = asyncio.run(
        research_personalized_trends(
            category=category,
            preferences=user_prefs,
            llm=llm,
            region=region,
            research_time=time,
            web_search=web_search,
            preferred_sources_path=sources,
            settings=settings,
        )
    )
    _render_report(report)
    _write_output(report, output)


@app.command("validate-preferences")
def validate_preferences_cmd(
    preferences: Annotated[
        Path,
        typer.Argument(help="Path to user preferences JSON"),
    ],
) -> None:
    """Validate a user preferences JSON file."""
    data = UserPreferences.model_validate_json(preferences.read_text())
    console.print(json.dumps(data.model_dump(mode="json"), indent=2))


@app.command("test-image-gen")
def test_image_gen_cmd(
    enable: Annotated[
        bool,
        typer.Option(
            "--enable/--no-enable",
            help="After a successful probe, allow image generation in post briefs.",
        ),
    ] = False,
    prompt: Annotated[
        str,
        typer.Option(help="Test prompt for image generation"),
    ] = "Close-up salon manicure with soft chrome finish, neutral background.",
) -> None:
    """Verify OpenAI GPT Image generation before enabling it in post briefs."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise typer.BadParameter("OPENAI_API_KEY is required. Add it to .env and retry.")

    console.print(
        Panel(
            f"Model preference: {settings.openai_image_model}\n"
            f"Probe required: {settings.willbe_media_require_probe}\n"
            f"Media enabled: {settings.willbe_media_generation_enabled}",
            title="Image generation probe",
        )
    )

    result = asyncio.run(run_image_generation_test(settings=settings, prompt=prompt))
    if result.status != "generated" or not result.url:
        console.print(f"[red]FAILED[/red] {result.error or 'No image returned.'}")
        raise typer.Exit(code=1)

    preview = result.url[:80] + "…" if len(result.url) > 80 else result.url
    console.print(f"[green]OK[/green] model={result.model}")
    console.print(f"Image data: {preview}")

    if enable or settings.willbe_media_generation_enabled:
        path = mark_image_probe_passed(settings)
        console.print(
            f"Probe recorded at {path}. Post briefs will now generate AI images "
            "(no extra env needed after probe; set WILLBE_MEDIA_GENERATION_ENABLED=true to require explicit enable in prod)."
        )
    else:
        console.print(
            "Re-run with --enable after verifying output to allow images in post briefs."
        )


if __name__ == "__main__":
    app()
