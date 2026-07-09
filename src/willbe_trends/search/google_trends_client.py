from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

GOOGLE_TRENDS_SCOPE = "https://www.googleapis.com/auth/searchtrends"
GOOGLE_TRENDS_BASE_URL = "https://searchtrends.googleapis.com/v1alpha"
SITE_QUERY_PATTERN = re.compile(r"\bsite:\S+\s*", re.IGNORECASE)
TIME_HINT_PATTERN = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december|"
    r"spring|summer|autumn|fall|winter|\d{4})\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GoogleTrendsPoint:
    timestamp: datetime
    search_interest: float | None
    scaled_search_interest: int | None


@dataclass(frozen=True)
class GoogleTrendsSeries:
    term: str
    geo_code: str
    points: list[GoogleTrendsPoint]


class GoogleTrendsClient:
    def __init__(
        self,
        *,
        project_id: str,
        credentials_path: Path,
        token_path: Path | None = None,
    ) -> None:
        self._project_id = project_id
        self._credentials_path = credentials_path
        self._token_path = token_path or Path(".cache/google-trends-token.json")

    async def fetch_time_series(
        self,
        term: str,
        *,
        geo_code: str = "US",
        months: int = 12,
        time_resolution: str = "MONTH",
    ) -> GoogleTrendsSeries:
        access_token = await asyncio.to_thread(self._load_access_token)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Goog-User-Project": self._project_id,
            "Content-Type": "application/json",
        }
        end_time = datetime.now(tz=UTC) - timedelta(days=2)
        start_time = end_time - timedelta(days=months * 30)

        payload = {
            "spec": {
                "expression": {"terms": [{"value": term, "type": "BROAD"}]},
                "geo": {"type": "GEO_TYPE_COUNTRY_OR_REGION", "code": geo_code},
                "timeRange": {
                    "startTime": {"seconds": int(start_time.timestamp())},
                    "endTime": {"seconds": int(end_time.timestamp())},
                },
                "timeResolution": time_resolution,
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            start_response = await client.post(
                f"{GOOGLE_TRENDS_BASE_URL}/fetchTimeSeries",
                headers=headers,
                json=payload,
            )
            start_response.raise_for_status()
            operation_name = start_response.json()["name"]
            operation = await self._poll_operation(client, operation_name, headers)
            points = self._parse_points(operation)

        return GoogleTrendsSeries(term=term, geo_code=geo_code, points=points)

    async def _poll_operation(
        self,
        client: httpx.AsyncClient,
        operation_name: str,
        headers: dict[str, str],
        *,
        attempts: int = 20,
        delay_seconds: float = 1.0,
    ) -> dict:
        url = f"{GOOGLE_TRENDS_BASE_URL}/{operation_name}"
        for _ in range(attempts):
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()
            if payload.get("done"):
                if payload.get("error"):
                    raise RuntimeError(f"Google Trends operation failed: {payload['error']}")
                return payload
            await asyncio.sleep(delay_seconds)
        raise TimeoutError("Google Trends operation did not complete in time.")

    def _parse_points(self, operation: dict) -> list[GoogleTrendsPoint]:
        response = operation.get("response") or {}
        time_series = response.get("timeSeries") or {}
        raw_points = time_series.get("points") or []
        points: list[GoogleTrendsPoint] = []
        for point in raw_points:
            timestamp = point.get("date")
            if not timestamp:
                continue
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            points.append(
                GoogleTrendsPoint(
                    timestamp=parsed,
                    search_interest=_optional_float(point.get("searchInterest")),
                    scaled_search_interest=_optional_int(point.get("scaledSearchInterest")),
                )
            )
        return points

    def _load_access_token(self) -> str:
        credentials_data = json.loads(self._credentials_path.read_text(encoding="utf-8"))
        creds_type = credentials_data.get("type")

        if creds_type == "service_account":
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                str(self._credentials_path),
                scopes=[GOOGLE_TRENDS_SCOPE],
            )
            credentials.refresh(Request())
            return credentials.token

        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        credentials: Credentials | None = None
        if self._token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self._token_path),
                scopes=[GOOGLE_TRENDS_SCOPE],
            )

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        elif not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self._credentials_path),
                scopes=[GOOGLE_TRENDS_SCOPE],
            )
            credentials = flow.run_local_server(port=0)
            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            self._token_path.write_text(credentials.to_json(), encoding="utf-8")

        if credentials is None or not credentials.token:
            raise RuntimeError("Unable to obtain Google Trends access token.")
        return credentials.token


def region_to_geo_code(region: str) -> str:
    normalized = region.strip().lower()
    if not normalized or normalized in {"global", "worldwide", "world"}:
        return "US"
    mapping = {
        "united states": "US",
        "usa": "US",
        "us": "US",
        "united kingdom": "GB",
        "uk": "GB",
        "finland": "FI",
        "australia": "AU",
        "canada": "CA",
        "germany": "DE",
        "france": "FR",
    }
    if normalized in mapping:
        return mapping[normalized]
    if len(normalized) == 2 and normalized.isalpha():
        return normalized.upper()
    return "US"


def query_to_trend_term(query: str) -> str:
    cleaned = SITE_QUERY_PATTERN.sub(" ", query)
    cleaned = TIME_HINT_PATTERN.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    if not cleaned:
        return query.strip()[:80]
    return cleaned[:80]


def summarize_trend_series(series: GoogleTrendsSeries) -> str:
    if not series.points:
        return f"No Google Trends data returned for '{series.term}' in {series.geo_code}."

    scaled = [point.scaled_search_interest for point in series.points if point.scaled_search_interest is not None]
    raw = [point.search_interest for point in series.points if point.search_interest is not None]
    latest = series.points[-1]
    latest_label = latest.timestamp.strftime("%Y-%m")

    if scaled:
        peak = max(scaled)
        peak_point = next(
            point for point in series.points if point.scaled_search_interest == peak
        )
        latest_scaled = latest.scaled_search_interest
        return (
            f"Google Trends scaled interest for '{series.term}' in {series.geo_code}: "
            f"latest {latest_scaled} in {latest_label}, peak {peak} in "
            f"{peak_point.timestamp.strftime('%Y-%m')} across {len(series.points)} periods."
        )

    if raw:
        peak = max(raw)
        latest_raw = latest.search_interest
        return (
            f"Google Trends search interest for '{series.term}' in {series.geo_code}: "
            f"latest {latest_raw:.2f} in {latest_label}, peak {peak:.2f} across "
            f"{len(series.points)} periods."
        )

    return f"Google Trends returned an empty time series for '{series.term}' in {series.geo_code}."


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
