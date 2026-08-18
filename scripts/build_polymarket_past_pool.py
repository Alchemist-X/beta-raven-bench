#!/usr/bin/env python3
"""Build a FutureX-compatible Polymarket past-bench question set.

The script deliberately separates agent-visible questions from sealed outcomes and
source provenance. It uses only the Python standard library so the selection can
be replayed in a clean environment.
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import random
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


SCHEMA_VERSION = "raven.polymarket-past-pool.v1"
SELECTOR_VERSION = "2026-08-17.2"
GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"
ID_NAMESPACE = uuid.UUID("da329f30-433c-55b8-a211-48a93c436e68")
UTC = dt.timezone.utc
MANUAL_EXCLUSION_FILE = (
    Path(__file__).resolve().parent.parent / "config/polymarket_march_2026_manual_exclusions.json"
)


def load_manual_exclusions() -> set[str]:
    if not MANUAL_EXCLUSION_FILE.exists():
        return set()
    payload = json.loads(MANUAL_EXCLUSION_FILE.read_text(encoding="utf-8"))
    values = payload.get("legacy_opaque_ids", [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError(f"Invalid manual exclusion file: {MANUAL_EXCLUSION_FILE}")
    return set(values)


MANUAL_EXCLUSION_IDS = load_manual_exclusions()

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

DOMAIN_ORDER = [
    "politics_elections",
    "geopolitics_conflict",
    "law_regulation",
    "ai_technology",
    "science_space",
    "business_organizations",
    "macro_public_policy",
    "health_public_safety",
    "climate_environment",
    "energy_infrastructure",
    "culture_media",
    "sports",
    "other",
]

DOMAIN_LABELS = {
    "politics_elections": "Politics and elections",
    "geopolitics_conflict": "Geopolitics, conflict, and diplomacy",
    "law_regulation": "Law, courts, and regulation",
    "ai_technology": "AI, technology, and cybersecurity",
    "science_space": "Science and space",
    "business_organizations": "Business and organizations (non-price)",
    "macro_public_policy": "Macroeconomics and public policy (non-price)",
    "health_public_safety": "Health and public safety",
    "climate_environment": "Climate, environment, and disasters",
    "energy_infrastructure": "Energy and infrastructure",
    "culture_media": "Culture, media, and awards",
    "sports": "Sports and competitions",
    "other": "Other",
}

# Category-stratified discovery avoids letting sports and high-frequency crypto
# markets dominate the source pool. IDs are public Gamma tag identifiers.
DISCOVERY_TAGS = {
    "politics": 2,
    "geopolitics": 100265,
    "courts": 1628,
    "ai": 439,
    "science": 74,
    "business": 107,
    "economy": 100328,
    "disease": 101894,
    "climate_science": 103037,
    "energy": 404,
    "pop_culture": 596,
}

PRICE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("odds_or_market_probability", re.compile(r"\b(odds|implied probability|market probability)\b", re.I)),
    ("explicit_price", re.compile(r"\b(price|priced|all[- ]time high|ath)\b", re.I)),
    ("valuation", re.compile(r"\b(market cap(?:italization)?|fdv|fully diluted valuation|valuation)\b", re.I)),
    (
        "asset_threshold",
        re.compile(
            r"\b(bitcoin|btc|ethereum|eth|solana|sol|xrp|dogecoin|doge|gold|silver|oil|crude|stock|shares?|s&p(?: 500)?|nasdaq|dow jones)\b"
            r".{0,80}\b(above|below|over|under|reach(?:es)?|hit(?:s)?|trade|worth|close|open|up|down|higher|lower)\b",
            re.I,
        ),
    ),
    (
        "currency_threshold",
        re.compile(r"\b(above|below|over|under|reach|hit|trade|worth|close|open)\b.{0,50}(?:US\$|\$|€|£|¥)\s?\d", re.I),
    ),
    ("price_direction", re.compile(r"\b(up or down|higher or lower)\b.*\b(stock|crypto|token|coin|index|market)\b", re.I)),
    (
        "index_or_asset_settlement",
        re.compile(
            r"\b(vix|volatility index|gold|silver|crude oil|brent|wti|usd\s*[/x-]\s*[a-z]{3})\b"
            r".{0,100}\b(close|settle|settlement|high|low|above|below|over|under)\b",
            re.I,
        ),
    ),
    ("real_estate_value", re.compile(r"\b(median|average)\s+(?:home|house|property)\s+(?:value|price)\b", re.I)),
    ("net_worth_threshold", re.compile(r"\bnet worth\b.{0,80}(?:US\$|\$|trillion|billion|million)", re.I)),
]

UNSCHEDULED_ACTION_WORDS = re.compile(
    r"\b(release|launch|announce|resign|step down|ceasefire|strike|attack|invade|invasion|military action|"
    r"war|conflict end|recognize|meet|visit|sign|treaty|deal|acquire|merger|bankrupt|file for|approve|"
    r"ban|sanction|tariff|deport|pardon|indict|convict|sentence|rule|ruling|confirm|nominate|withdraw|"
    r"shutdown|pass(?:es|ed)?|repeal|veto|deploy|hostage|nuclear test|launch a token)\b",
    re.I,
)

FIXED_COMPETITION_WORDS = re.compile(
    r"\b(vs\.?|versus|win (?:the|at)|winner|champion|score|goals?|points?|nba|nfl|nhl|mlb|ufc|"
    r"premier league|champions league|grand prix|tournament|match|game \d|oscars?|grammys?|eurovision)\b",
    re.I,
)


def iso_z(value: dt.datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_datetime(value: Any) -> dt.datetime | None:
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip().replace(" ", "T", 1)
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def stable_tiebreak(value: str, seed: str) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()
    return int(digest[:16], 16)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def http_json(url: str, *, attempts: int = 9, timeout: int = 45) -> Any:
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "raven-bench-polymarket-builder/0.1",
                "Connection": "close",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in {429, 500, 502, 503, 504}:
                raise
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(0.5 * (2**attempt), 12)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            delay = min(0.5 * (2**attempt), 12)
        time.sleep(delay + random.Random(attempt).random() * 0.2)
    assert last_error is not None
    raise last_error


def fetch_gamma_universe(year: int, month: int, max_pages: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    month_start = dt.datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        next_month = dt.datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        next_month = dt.datetime(year, month + 1, 1, tzinfo=UTC)
    markets: dict[str, dict[str, Any]] = {}
    page_receipts: list[dict[str, Any]] = []

    # Event-first, category-stratified discovery is materially faster than walking
    # every sports/crypto interval market. We still filter and label on each child
    # market's own timestamps. Both event states are required because a still-open
    # date-bucket event can contain child markets that have already resolved.
    for discovery_tag, tag_id in DISCOVERY_TAGS.items():
        for event_closed in (True, False):
            cursor: str | None = None
            for page_number in range(1, max_pages + 1):
                params: dict[str, Any] = {
                    "closed": str(event_closed).lower(),
                    "start_date_max": iso_z(next_month - dt.timedelta(microseconds=1)),
                    "order": "closedTime" if event_closed else "id",
                    "ascending": "false" if event_closed else "true",
                    "tag_id": tag_id,
                    "related_tags": "true",
                    "limit": 100,
                }
                if cursor:
                    params["after_cursor"] = cursor
                url = f"{GAMMA_BASE}/events/keyset?{urllib.parse.urlencode(params)}"
                payload = http_json(url)
                page = payload.get("events", []) if isinstance(payload, dict) else []
                if not isinstance(page, list):
                    raise RuntimeError(f"Unexpected Gamma event page shape at page {page_number}")
                page_json = json.dumps(page, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                event_closed_times = [parse_datetime(item.get("closedTime")) for item in page]
                valid_event_closed = [value for value in event_closed_times if value]
                child_count = 0
                for event in page:
                    children = event.get("markets")
                    if not isinstance(children, list):
                        continue
                    event_summary = {key: value for key, value in event.items() if key != "markets"}
                    for market in children:
                        if not isinstance(market, dict):
                            continue
                        child_count += 1
                        closed_at = parse_datetime(market.get("closedTime"))
                        if closed_at and closed_at >= month_start:
                            child = dict(market)
                            child["events"] = [event_summary]
                            markets[str(child.get("id"))] = child
                page_receipts.append(
                    {
                        "entity": "events",
                        "discovery_tag": discovery_tag,
                        "tag_id": tag_id,
                        "event_closed_filter": event_closed,
                        "page": page_number,
                        "request_url": url,
                        "event_count": len(page),
                        "child_market_count": child_count,
                        "body_sha256": hashlib.sha256(page_json.encode()).hexdigest(),
                        "first_closed_at": iso_z(max(valid_event_closed)) if valid_event_closed else None,
                        "last_closed_at": iso_z(min(valid_event_closed)) if valid_event_closed else None,
                        "next_cursor_sha256": hashlib.sha256(str(payload.get("next_cursor", "")).encode()).hexdigest(),
                    }
                )
                print(
                    f"Gamma tag={discovery_tag} closed={event_closed} page {page_number}: {len(page)} events / "
                    f"{child_count} child markets; kept {len(markets)}; event closed range "
                    f"{page_receipts[-1]['first_closed_at']}..{page_receipts[-1]['last_closed_at']}",
                    flush=True,
                )
                next_cursor = payload.get("next_cursor")
                if not page or not next_cursor or next_cursor == cursor:
                    break
                if event_closed and valid_event_closed and max(valid_event_closed) < month_start:
                    break
                cursor = str(next_cursor)
                time.sleep(0.12)
            else:
                raise RuntimeError(
                    f"Gamma event pagination exceeded max_pages={max_pages} for tag={discovery_tag} closed={event_closed}"
                )

    return sorted(markets.values(), key=lambda item: str(item.get("id"))), page_receipts


def event_for(market: dict[str, Any]) -> dict[str, Any]:
    events = market.get("events")
    return events[0] if isinstance(events, list) and events and isinstance(events[0], dict) else {}


def tag_text(market: dict[str, Any]) -> str:
    tags: list[str] = []
    for holder in (market, event_for(market)):
        values = holder.get("tags")
        if isinstance(values, list):
            for tag in values:
                if isinstance(tag, dict):
                    tags.extend(str(tag.get(key, "")) for key in ("label", "slug"))
                else:
                    tags.append(str(tag))
    return " ".join(tags)


def source_text(market: dict[str, Any], include_description: bool = False) -> str:
    event = event_for(market)
    parts = [
        str(market.get("question", "")),
        str(event.get("title", "")),
        tag_text(market),
    ]
    if include_description:
        parts.extend([str(market.get("description", "")), str(event.get("description", ""))])
    return " ".join(parts).strip()


def price_filter_reasons(market: dict[str, Any]) -> list[str]:
    text = source_text(market, include_description=False)
    reasons = [name for name, pattern in PRICE_PATTERNS if pattern.search(text)]
    description = source_text(market, include_description=True).lower()
    if "derivative.polymarket.com" in description or (
        "polymarket.com" in description and re.search(r"\b(price|priced|odds|probability|percent)\b", description)
    ):
        reasons.append("market_dependent_resolution")
    return reasons


def classify_domain(market: dict[str, Any]) -> str:
    # Resolution descriptions often mention unrelated institutions or fallback
    # sources. Use the market/event title and tags for taxonomy instead.
    text = source_text(market, include_description=False).lower()
    rules: list[tuple[str, tuple[str, ...]]] = [
        (
            "geopolitics_conflict",
            (
                "ceasefire",
                "military",
                "strike iran",
                "attack",
                "invade",
                "invasion",
                "war",
                "conflict",
                "hostage",
                "nato",
                "ukraine",
                "russia",
                "iran",
                "israel",
                "gaza",
                "china x taiwan",
                "north korea",
                "diplomatic",
                "treaty",
            ),
        ),
        (
            "law_regulation",
            (
                "supreme court",
                "court",
                "judge",
                "lawsuit",
                "convict",
                "sentence",
                "indict",
                "legal",
                "regulation",
                "regulator",
                "sec approve",
                "ftc",
                "doj",
                "trial",
            ),
        ),
        (
            "health_public_safety",
            (
                "fda",
                "vaccine",
                "pandemic",
                "covid",
                "virus",
                "disease",
                "drug approval",
                "health",
                "fatalit",
                "outbreak",
                "cdc",
            ),
        ),
        (
            "science_space",
            (
                "spacex",
                "nasa",
                "rocket",
                "spacecraft",
                "moon",
                "mars",
                "asteroid",
                "scientist",
                "research",
                "quantum",
                "starship",
            ),
        ),
        (
            "ai_technology",
            (
                "gpt-",
                "openai",
                "anthropic",
                "claude",
                "artificial intelligence",
                " ai ",
                "model release",
                "cyber",
                "hack",
                "apple",
                "google",
                "meta",
                "microsoft",
                "tiktok",
                "software",
                "tech",
                "robot",
            ),
        ),
        (
            "politics_elections",
            (
                "election",
                "president",
                "prime minister",
                "parliament",
                "congress",
                "senate",
                "governor",
                "nominee",
                "cabinet",
                "democrat",
                "republican",
                "approval rating",
                "resign",
                "impeach",
            ),
        ),
        (
            "macro_public_policy",
            (
                "federal reserve",
                "fed rate",
                "interest rate",
                "inflation",
                "cpi",
                "gdp",
                "unemployment",
                "recession",
                "tariff",
                "government shutdown",
                "debt ceiling",
                "immigration",
                "deport",
                "executive order",
            ),
        ),
        (
            "climate_environment",
            (
                "hurricane",
                "earthquake",
                "wildfire",
                "climate",
                "temperature",
                "weather",
                "storm",
                "flood",
                "emissions",
                "volcano",
            ),
        ),
        (
            "energy_infrastructure",
            (
                "nuclear power",
                "power plant",
                "electricity",
                "pipeline",
                "oil production",
                "opec",
                "energy",
                "grid",
                "infrastructure",
                "data center",
            ),
        ),
        (
            "culture_media",
            (
                "oscar",
                "grammy",
                "emmy",
                "eurovision",
                "album",
                "movie",
                "film",
                "box office",
                "netflix",
                "youtube",
                "stream",
                "music",
                "celebrity",
                "pope",
            ),
        ),
        (
            "sports",
            (
                " sports ",
                "nba",
                "nfl",
                "nhl",
                "mlb",
                "ufc",
                "soccer",
                "football",
                "basketball",
                "baseball",
                "tennis",
                "golf",
                "formula 1",
                "champions league",
                "premier league",
                "world cup",
                "tournament",
                "match",
                "fight",
                "fight next",
                "mvp",
            ),
        ),
        (
            "business_organizations",
            (
                "company",
                "ceo",
                "acquire",
                "merger",
                "bankrupt",
                "ipo",
                "business",
                "corporate",
                "disney",
                "tesla",
                "amazon",
                "boeing",
                "organization",
            ),
        ),
    ]
    padded = f" {text} "
    for domain, needles in rules:
        if any(needle in padded for needle in needles):
            return domain
    return "other"


def parse_question_deadline(question: str, anchor: dt.datetime, target_year: int) -> tuple[dt.datetime | None, str | None]:
    text = question.strip()
    lower = text.lower()

    iso_match = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", lower)
    if iso_match:
        year, month, day = (int(value) for value in iso_match.groups())
        try:
            return dt.datetime(year, month, day, 23, 59, 59, tzinfo=UTC), "question_iso_date"
        except ValueError:
            pass

    month_names = "|".join(MONTHS)
    dated = re.search(
        rf"\b(by|before|through|on|in|during)\s+(?:the\s+end\s+of\s+)?({month_names})"
        rf"(?:\s+(\d{{1,2}})(?:st|nd|rd|th)?)?(?:,?\s+(20\d{{2}}))?\b",
        lower,
    )
    if dated:
        relation, month_name, day_text, year_text = dated.groups()
        year = int(year_text) if year_text else target_year
        month = MONTHS[month_name]
        if relation == "before" and not day_text:
            first_day = dt.datetime(year, month, 1, tzinfo=UTC)
            return first_day - dt.timedelta(seconds=1), "question_named_date"
        if day_text:
            day = int(day_text)
        else:
            if month == 12:
                day = 31
            else:
                day = (dt.date(year, month + 1, 1) - dt.timedelta(days=1)).day
        try:
            deadline = dt.datetime(year, month, day, 23, 59, 59, tzinfo=UTC)
        except ValueError:
            deadline = None
        if deadline and relation == "before":
            deadline -= dt.timedelta(days=1)
        return deadline, "question_named_date"

    quarter = re.search(r"\b(?:by|in|during|before)?\s*q([1-4])(?:\s+(20\d{2}))?\b", lower)
    if quarter:
        q, year_text = quarter.groups()
        year = int(year_text) if year_text else target_year
        month = int(q) * 3
        next_month = dt.date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        last_day = next_month - dt.timedelta(days=1)
        return dt.datetime.combine(last_day, dt.time(23, 59, 59), UTC), "question_quarter"

    year_match = re.search(r"\b(by|before|in|during)\s+(20\d{2})\b", lower)
    if year_match:
        relation, year_text = year_match.groups()
        year = int(year_text)
        if relation == "before":
            year -= 1
        return dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC), "question_year"

    return None, None


def parse_description_deadlines(
    description: str, anchor: dt.datetime, target_year: int
) -> list[tuple[dt.datetime, str]]:
    """Extract explicit by/before/through deadlines, including common US zones."""
    month_names = "|".join(MONTHS)
    pattern = re.compile(
        rf"\b(?P<relation>scheduled to be released on|released on|published on|by|before|through|until|no later than)\s*"
        rf"(?:the\s+end\s+of\s+)?(?P<month>{month_names})\s+"
        rf"(?P<day>\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(?P<year>20\d{{2}}))?"
        rf"(?:,?\s+(?:at\s+)?(?P<hour>\d{{1,2}})(?::(?P<minute>\d{{2}}))?\s*(?P<ampm>AM|PM))?"
        rf"(?:\s*(?P<zone>ET|EST|EDT|PT|PST|PDT|UTC|GMT|KST|JST|CET|CEST))?\b",
        re.I,
    )
    zone_names = {
        "et": "America/New_York",
        "est": "America/New_York",
        "edt": "America/New_York",
        "pt": "America/Los_Angeles",
        "pst": "America/Los_Angeles",
        "pdt": "America/Los_Angeles",
        "kst": "Asia/Seoul",
        "jst": "Asia/Tokyo",
        "cet": "Europe/Paris",
        "cest": "Europe/Paris",
        "utc": "UTC",
        "gmt": "UTC",
    }
    values: list[tuple[dt.datetime, str]] = []
    for match in pattern.finditer(description):
        groups = match.groupdict()
        year = int(groups["year"] or target_year)
        month = MONTHS[groups["month"].lower()]
        day = int(groups["day"])
        hour_text = groups.get("hour")
        if hour_text:
            hour = int(hour_text) % 12
            if (groups.get("ampm") or "").lower() == "pm":
                hour += 12
            minute = int(groups.get("minute") or 0)
            second = 0
        else:
            hour, minute, second = 23, 59, 59
        zone_key = (groups.get("zone") or "utc").lower()
        try:
            local = dt.datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(zone_names[zone_key]))
        except (ValueError, KeyError):
            continue
        value = local.astimezone(UTC)
        if groups["relation"].lower() == "before" and not hour_text:
            value -= dt.timedelta(days=1)
        if value > anchor:
            values.append((value, f"resolution_criteria_{zone_key}"))
    return values


def resolution_label(market: dict[str, Any]) -> tuple[str | None, str | None]:
    outcomes = [str(value) for value in parse_json_list(market.get("outcomes"))]
    prices_raw = parse_json_list(market.get("outcomePrices"))
    if len(outcomes) != 2 or len(prices_raw) != 2:
        return None, "not_binary"
    lowered = [value.strip().lower() for value in outcomes]
    if set(lowered) != {"yes", "no"}:
        return None, "not_yes_no"
    try:
        prices = [float(value) for value in prices_raw]
    except (TypeError, ValueError):
        return None, "invalid_prices"
    if max(prices) < 0.99 or min(prices) > 0.01:
        return None, "not_final_or_void"
    winner = outcomes[prices.index(max(prices))]
    if winner.strip().lower() not in {"yes", "no"}:
        return None, "unknown_winner"
    return winner.title(), None


def temporal_archetype(market: dict[str, Any]) -> str:
    text = source_text(market, include_description=False).lower()
    if any(word in text for word in ("ceasefire", "strike", "attack", "invasion", "war", "conflict")):
        return "conflict_transition"
    if any(word in text for word in ("release", "launch", "announce", "ship", "debut")):
        return "release_or_launch"
    if any(word in text for word in ("court", "rule", "convict", "sentence", "approve", "ban", "regulation")):
        return "legal_or_regulatory_action"
    if re.search(r"\b(by|before|when|through)\b", text):
        return "unscheduled_deadline_event"
    if any(word in text for word in ("election", "nominee", "primary")):
        return "election_or_appointment"
    if FIXED_COMPETITION_WORDS.search(text):
        return "scheduled_competition"
    if re.search(r"\b(at least|more than|fewer than|reach|total)\b", text):
        return "cumulative_threshold"
    return "other_event"


def topic_family(market: dict[str, Any]) -> str | None:
    text = f" {source_text(market, include_description=False).lower()} "
    families: list[tuple[str, tuple[str, ...]]] = [
        ("iran", (" iran ", "iranian")),
        ("microstrategy", ("microstrategy", "strategy bitcoin")),
        ("russia_ukraine", (" ukraine ", " russia ", "putin", "zelensky")),
        ("openai_gpt", ("openai", "gpt-", "chatgpt")),
        ("spacex_starship", ("spacex", "starship")),
        ("federal_reserve", ("federal reserve", "fed chair", "fed rate", "fomc")),
        ("supreme_court", ("supreme court", "scotus")),
        ("pope_vatican", (" pope ", "vatican")),
        ("trump_non_iran", (" trump ",)),
    ]
    for family, needles in families:
        if any(needle in text for needle in needles):
            return family
    return None


def template_family(question: str) -> str:
    value = question.lower()
    value = re.sub(r"\b(?:" + "|".join(MONTHS) + r")\b", " <month> ", value)
    value = re.sub(r"\b20\d{2}\b", " <year> ", value)
    value = re.sub(r"\b\d+(?:\.\d+)?(?:st|nd|rd|th|k|m|b|%)?\b", " <n> ", value)
    value = re.sub(r"[^a-z<>]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def mechanical_family(question: str) -> str | None:
    value = question.lower()
    if re.search(r"\b(out as|out from|resign|step down|retire|removed as)\b", value):
        return "leader_exit"
    if re.search(r"\b(fed|fomc|ecb|bank of canada|bank of japan|interest rates?|bps)\b", value):
        return "central_bank_decision"
    if re.search(r"\bearthquake|megaquake\b", value):
        return "earthquake"
    if re.search(r"\b(release|launch|announce|debut)\b", value):
        return "release_or_launch"
    if re.search(r"\b(between .+%|seats? in|win \d+ or|win \d+\+)\b", value):
        return "election_bucket"
    return None


def region_label(market: dict[str, Any]) -> str:
    text = source_text(market, include_description=True).lower()
    international = (
        "ukraine",
        "russia",
        "iran",
        "israel",
        "china",
        "taiwan",
        "europe",
        "canada",
        "mexico",
        "india",
        "korea",
        "japan",
        "germany",
        "france",
        "uk ",
        "united kingdom",
        "australia",
        "brazil",
        "argentina",
        "africa",
    )
    us = ("united states", " u.s.", " us ", "trump", "congress", "senate", "white house", "federal reserve")
    if any(value in text for value in international):
        return "international_or_cross_border"
    if any(value in f" {text} " for value in us):
        return "united_states"
    return "global_or_unspecified"


def heuristic_scores(
    market: dict[str, Any],
    domain: str,
    archetype: str,
    horizon_days: float | None,
    deadline_source: str,
) -> dict[str, int]:
    text = source_text(market, include_description=False)
    description = str(market.get("description") or event_for(market).get("description") or "")

    temporal = 2
    if re.search(r"\b(by|before|when|through)\b", text, re.I):
        temporal += 1
    if UNSCHEDULED_ACTION_WORDS.search(text):
        temporal += 2
    if horizon_days is not None and horizon_days >= 60:
        temporal += 1
    if archetype == "scheduled_competition":
        temporal -= 2
    temporal = max(1, min(5, temporal))

    research = {
        "geopolitics_conflict": 4,
        "politics_elections": 4,
        "law_regulation": 4,
        "ai_technology": 4,
        "science_space": 4,
        "macro_public_policy": 4,
        "health_public_safety": 3,
        "climate_environment": 3,
        "energy_infrastructure": 3,
        "business_organizations": 3,
        "culture_media": 2,
        "sports": 2,
        "other": 2,
    }[domain]
    if re.search(r"\b(and|or|versus|vs\.?|coalition|agreement|deal)\b", text, re.I):
        research = min(5, research + 1)

    nontriviality = 4 if UNSCHEDULED_ACTION_WORDS.search(text) else 3
    if archetype == "scheduled_competition":
        nontriviality = 3
    if horizon_days is not None and horizon_days < 3:
        nontriviality = max(1, nontriviality - 1)

    causal = 4 if domain in {"geopolitics_conflict", "politics_elections", "macro_public_policy", "law_regulation"} else 3
    if archetype in {"conflict_transition", "unscheduled_deadline_event"}:
        causal = min(5, causal + 1)
    if archetype == "scheduled_competition":
        causal = 2

    resolvability = 3
    if len(description) >= 120:
        resolvability += 1
    if re.search(r"\b(primary resolution source|resolution source|official information|resolve to)\b", description, re.I):
        resolvability += 1
    resolvability = min(5, resolvability)

    corpus_fit = 4 if domain not in {"sports", "culture_media", "other"} else 3
    if deadline_source == "gamma_end_date" and not description:
        corpus_fit = max(1, corpus_fit - 1)

    return {
        "temporal_uncertainty": temporal,
        "research_difficulty": research,
        "ex_ante_nontriviality": nontriviality,
        "causal_complexity": causal,
        "resolvability": resolvability,
        "frozen_corpus_fit": corpus_fit,
    }


def weighted_quality(scores: dict[str, int]) -> int:
    return (
        6 * scores["temporal_uncertainty"]
        + 4 * scores["research_difficulty"]
        + 3 * scores["ex_ante_nontriviality"]
        + 3 * scores["causal_complexity"]
        + 2 * scores["resolvability"]
        + 2 * scores["frozen_corpus_fit"]
    )


def horizon_bucket(days: float | None) -> str:
    if days is None:
        return "unknown"
    if days <= 30:
        return "7_to_30_days" if days >= 7 else "under_7_days"
    if days <= 60:
        return "31_to_60_days"
    if days <= 120:
        return "61_to_120_days"
    return "over_120_days"


def normalize_market(
    market: dict[str, Any], year: int, month: int, id_secret: bytes
) -> tuple[dict[str, Any] | None, list[str]]:
    month_start = dt.datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        next_month = dt.datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        next_month = dt.datetime(year, month + 1, 1, tzinfo=UTC)
    may_cutoff = dt.datetime(year, 6, 1, tzinfo=UTC)
    may_start = dt.datetime(year, 5, 1, tzinfo=UTC)

    reasons: list[str] = []
    market_id = str(market.get("id") or "")
    condition_id = str(market.get("conditionId") or "")
    question = str(market.get("question") or "").strip()
    event = event_for(market)
    description = str(market.get("description") or event.get("description") or "").strip()
    if not market_id or not condition_id or not question:
        reasons.append("missing_identity_or_question")
    if re.search(r"\b(?:Person|Candidate|Bank|Party)\s+[A-Z]\b", question, re.I) or re.search(
        r"\b(?:some other candidate|no listed (?:leader|candidate|individual))\b", question, re.I
    ):
        reasons.append("non_self_contained_anonymous_option")
    if re.search(r"\b(?:Movie|Film|Song)\s+[A-Z]\b", question, re.I):
        reasons.append("non_self_contained_anonymous_option")
    if re.search(r"\bTSA\b.*\bpassengers?\b", question, re.I):
        reasons.append("routine_reporting_task_excluded")
    if re.search(r"\bNepal\b", question, re.I) and re.search(r"\bseats?\b", question, re.I) and re.search(
        r"National Assembly seats?.*House of Representatives", description, re.I | re.S
    ):
        reasons.append("internally_inconsistent_resolution_criteria")
    if re.search(r"\bTexas\b.*\b(?:Senate )?Primary\b.*\b(?:between|by \d)", question, re.I):
        reasons.append("short_horizon_election_margin_bucket")

    closed_at = parse_datetime(market.get("closedTime"))
    if not closed_at:
        reasons.append("missing_closed_time")
    elif closed_at < month_start:
        reasons.append("resolved_before_march")

    opened_raw = market.get("acceptingOrdersTimestamp")
    opened_at = parse_datetime(opened_raw)
    opened_source = "acceptingOrdersTimestamp"
    if not opened_at:
        opened_at = parse_datetime(market.get("startDate"))
        opened_source = "startDate_fallback"
    if not opened_at:
        reasons.append("missing_available_time")
    elif opened_at >= next_month:
        reasons.append("not_available_by_march_end")

    anchor = max(month_start, opened_at) if opened_at else month_start
    if closed_at and closed_at <= anchor:
        reasons.append("resolved_at_or_before_anchor")

    winner, label_error = resolution_label(market)
    if label_error:
        reasons.append(label_error)

    price_reasons = price_filter_reasons(market)
    reasons.extend(f"price_related:{value}" for value in price_reasons)

    parsed_deadline, parsed_source = parse_question_deadline(question, anchor, year)
    criteria_deadlines = parse_description_deadlines(description, anchor, year)
    gamma_deadline = parse_datetime(market.get("endDate"))
    if gamma_deadline and gamma_deadline.time() == dt.time(0, 0):
        gamma_deadline += dt.timedelta(hours=23, minutes=59, seconds=59)
        gamma_source = "gamma_end_date_day_end_normalized"
    else:
        gamma_source = "gamma_end_date"

    effective_deadline = parsed_deadline
    deadline_source = parsed_source
    if parsed_deadline:
        same_day = [item for item in criteria_deadlines if item[0].date() == parsed_deadline.date()]
        if same_day:
            effective_deadline, deadline_source = same_day[0]
        elif re.search(r"\b(CPI|inflation|temperature|GDP|unemployment|jobs report)\b", question, re.I):
            later_candidates = [
                item for item in criteria_deadlines if parsed_deadline < item[0] <= parsed_deadline + dt.timedelta(days=45)
            ]
            if later_candidates:
                effective_deadline, deadline_source = later_candidates[0]
            elif gamma_deadline and parsed_deadline < gamma_deadline <= parsed_deadline + dt.timedelta(days=45):
                effective_deadline, deadline_source = gamma_deadline, gamma_source
    else:
        available_deadlines = list(criteria_deadlines)
        if gamma_deadline:
            available_deadlines.append((gamma_deadline, gamma_source))
        if available_deadlines:
            effective_deadline, deadline_source = min(available_deadlines, key=lambda item: item[0])
        else:
            effective_deadline, deadline_source = None, None
    if not effective_deadline:
        reasons.append("missing_deadline")
    elif effective_deadline < month_start:
        reasons.append("deadline_before_march")
    elif effective_deadline <= anchor:
        reasons.append("deadline_at_or_before_anchor")

    if reasons:
        return None, reasons

    assert opened_at and closed_at and effective_deadline and winner
    event_id = str(event.get("id") or condition_id)
    legacy_opaque_id = str(uuid.uuid5(ID_NAMESPACE, condition_id.lower()))
    if legacy_opaque_id in MANUAL_EXCLUSION_IDS:
        return None, ["manual_multi_reviewer_exclusion"]
    opaque_id = str(
        uuid.UUID(
            bytes=hashlib.blake2b(condition_id.lower().encode(), key=id_secret, digest_size=16).digest(),
            version=4,
        )
    )
    opaque_cluster = str(
        uuid.UUID(
            bytes=hashlib.blake2b(f"event:{event_id}".encode(), key=id_secret, digest_size=16).digest(),
            version=4,
        )
    )
    domain = classify_domain(market)
    if domain == "sports":
        return None, ["sports_fixed_schedule_source_excluded"]
    archetype = temporal_archetype(market)
    horizon = (effective_deadline - anchor).total_seconds() / 86400
    scores = heuristic_scores(market, domain, archetype, horizon, deadline_source)
    quality = weighted_quality(scores)
    status = "resolved_by_may_end" if closed_at < may_cutoff else "unresolved_at_may_end_but_later_settled"
    resolution_source = str(market.get("resolutionSource") or event.get("resolutionSource") or "").strip()
    mismatch_days = abs((parsed_deadline - gamma_deadline).total_seconds()) / 86400 if parsed_deadline and gamma_deadline else None
    deadline_audit = "mismatch_gt_3d" if mismatch_days is not None and mismatch_days > 3 else "consistent_or_single_source"
    event_slug = str(event.get("slug") or "")

    return {
        "id": opaque_id,
        "condition_id": condition_id,
        "source_market_id": market_id,
        "source_market_slug": str(market.get("slug") or ""),
        "source_event_id": event_id,
        "source_event_slug": event_slug,
        "event_cluster_id": opaque_cluster,
        "question": question,
        "resolution_criteria": description,
        "resolution_source": resolution_source,
        "opened_at": iso_z(opened_at),
        "opened_at_source": opened_source,
        "forecast_anchor": iso_z(anchor),
        "effective_deadline": iso_z(effective_deadline),
        "effective_deadline_source": deadline_source,
        "gamma_end_date": iso_z(gamma_deadline) if gamma_deadline else None,
        "deadline_mismatch_days": round(mismatch_days, 3) if mismatch_days is not None else None,
        "deadline_audit": deadline_audit,
        "resolved_at": iso_z(closed_at),
        "resolved_in_may": may_start <= closed_at < may_cutoff,
        "may_status": status,
        "winner": winner,
        "ground_truth": "A" if winner == "Yes" else "B",
        "domain": domain,
        "domain_label": DOMAIN_LABELS[domain],
        "region": region_label(market),
        "temporal_archetype": archetype,
        "topic_family": topic_family(market),
        "template_family": template_family(question),
        "mechanical_family": mechanical_family(question),
        "horizon_days": round(horizon, 3),
        "horizon_bucket": horizon_bucket(horizon),
        "heuristic_scores": scores,
        "quality_score": quality,
        "forecast_difficulty": "hard" if quality >= 70 and scores["temporal_uncertainty"] >= 4 else "medium",
        "source_url": f"https://polymarket.com/event/{event_slug}" if event_slug else None,
        "gamma_url": f"{GAMMA_BASE}/markets/{market_id}",
        "clob_url": f"{CLOB_BASE}/markets/{condition_id}",
        "current_market_updated_at": market.get("updatedAt"),
        "rule_snapshot_warning": "Current Gamma description is not a proven anchor-time historical snapshot.",
        "selection_review_status": "automated_needs_human_review",
        "volume_num_private": market.get("volumeNum"),
    }, []


def dedupe_candidates(records: list[dict[str, Any]], seed: str) -> list[dict[str, Any]]:
    best_by_question: dict[str, dict[str, Any]] = {}
    for record in records:
        key = re.sub(r"\W+", " ", record["question"].lower()).strip()
        existing = best_by_question.get(key)
        ranking = (record["quality_score"], -stable_tiebreak(record["id"], seed))
        if not existing or ranking > (existing["quality_score"], -stable_tiebreak(existing["id"], seed)):
            best_by_question[key] = record
    return list(best_by_question.values())


def domain_quotas(records: list[dict[str, Any]], count: int, *, selected: bool) -> dict[str, int]:
    supply = collections.Counter(record["domain"] for record in records)
    quotas = {domain: min(supply[domain], 8 if selected and supply[domain] >= 8 else 0) for domain in DOMAIN_ORDER}
    if not selected:
        quotas = {domain: 0 for domain in DOMAIN_ORDER}
    caps: dict[str, int] = {}
    for domain in DOMAIN_ORDER:
        if selected:
            cap = 25 if domain in {"sports", "other"} else 45
        else:
            cap = 60 if domain in {"sports", "other"} else 110
        caps[domain] = min(supply[domain], cap)

    while sum(quotas.values()) < count:
        available = [domain for domain in DOMAIN_ORDER if quotas[domain] < caps[domain]]
        if not available:
            # Supply/cap shortfall: relax caps without changing the hard price/cluster filters.
            available = [domain for domain in DOMAIN_ORDER if quotas[domain] < supply[domain]]
        if not available:
            break
        chosen = max(
            available,
            key=lambda domain: (
                math.sqrt(max(supply[domain], 1)) / (quotas[domain] + 1),
                -DOMAIN_ORDER.index(domain),
            ),
        )
        quotas[chosen] += 1
    return quotas


def choose_diverse(
    records: list[dict[str, Any]],
    count: int,
    *,
    seed: str,
    cluster_cap: int,
    selected: bool,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    if len(records) < count:
        raise RuntimeError(f"Only {len(records)} eligible records are available; need {count}")
    quotas = domain_quotas(records, count, selected=selected)
    status_supply = collections.Counter(record["may_status"] for record in records)
    statuses = ["resolved_by_may_end", "unresolved_at_may_end_but_later_settled"]
    status_targets = {statuses[0]: count // 2, statuses[1]: count - count // 2}
    if any(status_supply[status] < status_targets[status] for status in statuses):
        lacking = next(status for status in statuses if status_supply[status] < status_targets[status])
        other = statuses[1] if lacking == statuses[0] else statuses[0]
        status_targets[lacking] = status_supply[lacking]
        status_targets[other] = count - status_targets[lacking]

    chosen: list[dict[str, Any]] = []
    chosen_ids: set[str] = set()
    cluster_counts: collections.Counter[str] = collections.Counter()
    domain_counts: collections.Counter[str] = collections.Counter()
    status_counts: collections.Counter[str] = collections.Counter()
    horizon_counts: collections.Counter[str] = collections.Counter()
    archetype_counts: collections.Counter[str] = collections.Counter()
    template_counts: collections.Counter[str] = collections.Counter()
    topic_counts: collections.Counter[str] = collections.Counter()
    mechanical_counts: collections.Counter[str] = collections.Counter()
    template_cap = 1 if selected else 3
    topic_caps = {
        "iran": 15 if selected else 40,
        "microstrategy": 3 if selected else 8,
        "russia_ukraine": 12 if selected else 30,
        "openai_gpt": 5 if selected else 12,
        "spacex_starship": 6 if selected else 15,
        "federal_reserve": 6 if selected else 15,
        "supreme_court": 8 if selected else 18,
        "pope_vatican": 5 if selected else 12,
        "trump_non_iran": 12 if selected else 30,
    }
    mechanical_caps = {
        "leader_exit": 12 if selected else 30,
        "central_bank_decision": 12 if selected else 30,
        "earthquake": 4 if selected else 10,
        "release_or_launch": 35 if selected else 80,
        "election_bucket": 12 if selected else 30,
    }

    while len(chosen) < count:
        feasible: list[tuple[float, int, dict[str, Any]]] = []
        for record in records:
            if record["id"] in chosen_ids:
                continue
            if cluster_counts[record["event_cluster_id"]] >= cluster_cap:
                continue
            if template_counts[record["template_family"]] >= template_cap:
                continue
            family = record.get("topic_family")
            if family and topic_counts[family] >= topic_caps.get(family, count):
                continue
            mechanism = record.get("mechanical_family")
            if mechanism and mechanical_counts[mechanism] >= mechanical_caps.get(mechanism, count):
                continue
            if domain_counts[record["domain"]] >= quotas.get(record["domain"], 0):
                continue
            if status_counts[record["may_status"]] >= status_targets[record["may_status"]]:
                continue
            score = float(record["quality_score"])
            score += 12 * (1 - domain_counts[record["domain"]] / max(quotas[record["domain"]], 1))
            score += 8 * (1 - status_counts[record["may_status"]] / max(status_targets[record["may_status"]], 1))
            score += 3 / (1 + horizon_counts[record["horizon_bucket"]])
            score += 3 / (1 + archetype_counts[record["temporal_archetype"]])
            if "gpt-6" in record["question"].lower() or "iran" in record["question"].lower():
                score += 4
            feasible.append((score, -stable_tiebreak(record["id"], seed), record))
        if not feasible:
            # Relax the computed domain quotas first. Hard filters and cluster caps remain.
            remaining = [
                record
                for record in records
                if record["id"] not in chosen_ids
                and cluster_counts[record["event_cluster_id"]] < cluster_cap
                and template_counts[record["template_family"]] < template_cap
                and (
                    not record.get("topic_family")
                    or topic_counts[record["topic_family"]] < topic_caps.get(record["topic_family"], count)
                )
                and (
                    not record.get("mechanical_family")
                    or mechanical_counts[record["mechanical_family"]]
                    < mechanical_caps.get(record["mechanical_family"], count)
                )
                and status_counts[record["may_status"]] < status_targets[record["may_status"]]
            ]
            if not remaining:
                # Last resort: relax diversity caps but never the historical-status
                # target or event-cluster independence.
                remaining = [
                    record
                    for record in records
                    if record["id"] not in chosen_ids
                    and cluster_counts[record["event_cluster_id"]] < cluster_cap
                    and status_counts[record["may_status"]] < status_targets[record["may_status"]]
                ]
            if not remaining:
                raise RuntimeError(f"Could select only {len(chosen)} of {count} under cluster_cap={cluster_cap}")
            record = max(
                remaining,
                key=lambda value: (value["quality_score"], -stable_tiebreak(value["id"], seed)),
            )
            quotas[record["domain"]] = max(quotas.get(record["domain"], 0), domain_counts[record["domain"]] + 1)
        else:
            record = max(feasible, key=lambda item: (item[0], item[1]))[2]
        chosen.append(record)
        chosen_ids.add(record["id"])
        cluster_counts[record["event_cluster_id"]] += 1
        domain_counts[record["domain"]] += 1
        status_counts[record["may_status"]] += 1
        horizon_counts[record["horizon_bucket"]] += 1
        archetype_counts[record["temporal_archetype"]] += 1
        template_counts[record["template_family"]] += 1
        if record.get("topic_family"):
            topic_counts[record["topic_family"]] += 1
        if record.get("mechanical_family"):
            mechanical_counts[record["mechanical_family"]] += 1

    return chosen, dict(quotas), dict(status_targets)


def clob_verify(record: dict[str, Any]) -> dict[str, Any]:
    url = record["clob_url"]
    try:
        payload = http_json(url, attempts=7)
    except Exception as error:  # noqa: BLE001 - stored as an audit result
        return {"status": "request_failed", "error": f"{type(error).__name__}: {error}"[:500]}
    tokens = payload.get("tokens", []) if isinstance(payload, dict) else []
    winners = [token for token in tokens if isinstance(token, dict) and token.get("winner") is True]
    winner = str(winners[0].get("outcome")) if len(winners) == 1 else None
    gamma_match = winner and winner.lower() == record["winner"].lower()
    gamma_opened = record["opened_at"]
    clob_opened = parse_datetime(payload.get("accepting_order_timestamp")) if isinstance(payload, dict) else None
    return {
        "status": "verified" if gamma_match else "mismatch",
        "clob_winner": winner,
        "gamma_winner": record["winner"],
        "winner_match": bool(gamma_match),
        "is_50_50_outcome": payload.get("is_50_50_outcome") if isinstance(payload, dict) else None,
        "clob_closed": payload.get("closed") if isinstance(payload, dict) else None,
        "clob_accepting_order_timestamp": iso_z(clob_opened) if clob_opened else None,
        "gamma_opened_at": gamma_opened,
        "opened_at_match": bool(clob_opened and abs((clob_opened - parse_datetime(gamma_opened)).total_seconds()) <= 2),
        "observed_url": url,
    }


def verify_records(records: list[dict[str, Any]], workers: int) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(clob_verify, record): record["id"] for record in records}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            record_id = futures[future]
            results[record_id] = future.result()
            completed += 1
            if completed % 25 == 0 or completed == len(records):
                print(f"CLOB verification: {completed}/{len(records)}", flush=True)
    return results


def sanitize_agent_visible_criteria(value: str) -> str:
    """Remove live result links and source-market branding from agent input."""
    cleaned = re.sub(r"(?:https?://|www\.)[^\s)\]>]+", "[source URL withheld]", value, flags=re.I)
    cleaned = re.sub(
        r"\b(?:[a-z0-9-]+\.)+(?:com|org|net|gov|edu|io|ai|co|uk|de|fr|ch|cl)(?:/[^\s)\]>]*)?",
        "[source domain withheld]",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"\bpolymarket\b", "source market", cleaned, flags=re.I)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    return cleaned.strip()


def public_question(record: dict[str, Any]) -> dict[str, Any]:
    criteria = sanitize_agent_visible_criteria(record["resolution_criteria"])
    criteria_block = f"\n\nResolution criteria:\n{criteria}" if criteria else ""
    prompt = (
        f"Use only information available on or before {record['forecast_anchor']}.\n\n"
        f"Forecast the following event:\n{record['question']}"
        f"{criteria_block}\n\n"
        "For this binary task, Yes means the outcome stated in the question occurs under "
        "the resolution criteria; No means it does not.\n\n"
        "A. Yes\nB. No\n\nReturn the single best choice, A or B."
    )
    return {
        "id": record["id"],
        "prompt": prompt,
        "end_time": record["effective_deadline"],
        "level": 1,
        "en_title": record["question"],
        "task_type": "single_choice",
        "options": [{"key": "A", "text": "Yes"}, {"key": "B", "text": "No"}],
        "forecast_anchor": record["forecast_anchor"],
        "forecast_difficulty": record["forecast_difficulty"],
        "domain": record["domain"],
        "temporal_archetype": record["temporal_archetype"],
    }


def sealed_label(record: dict[str, Any], verification: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "id": record["id"],
        "ground_truth": record["ground_truth"],
        "winning_outcome": record["winner"],
        "status_as_of_may_end": record["may_status"],
        "status_snapshot_at": record["resolved_at"][:4] + "-06-01T00:00:00Z",
        "resolved_in_may": record["resolved_in_may"],
        "resolved_at": record["resolved_at"],
        "final_resolution_state": "resolved_yes" if record["winner"] == "Yes" else "resolved_no",
        "clob_verification": verification or {"status": "not_run"},
        "schema_version": SCHEMA_VERSION,
    }


def private_provenance(record: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "id",
        "condition_id",
        "source_market_id",
        "source_market_slug",
        "source_event_id",
        "source_event_slug",
        "source_url",
        "gamma_url",
        "clob_url",
        "event_cluster_id",
        "opened_at",
        "opened_at_source",
        "forecast_anchor",
        "effective_deadline",
        "effective_deadline_source",
        "gamma_end_date",
        "deadline_mismatch_days",
        "deadline_audit",
        "resolution_source",
        "current_market_updated_at",
        "rule_snapshot_warning",
        "selection_review_status",
        "volume_num_private",
        "quality_score",
        "heuristic_scores",
        "domain",
        "region",
        "temporal_archetype",
        "topic_family",
        "template_family",
        "mechanical_family",
        "horizon_days",
        "horizon_bucket",
    ]
    return {**{key: record.get(key) for key in keys}, "selector_version": SELECTOR_VERSION, "schema_version": SCHEMA_VERSION}


def status_snapshot(record: dict[str, Any], year: int) -> dict[str, Any]:
    return {
        "id": record["id"],
        "forecast_anchor": {"at": record["forecast_anchor"], "status": "open_assumed_from_order_window"},
        "may_end": {
            "at": f"{year}-06-01T00:00:00Z",
            "status": "resolved" if record["may_status"] == "resolved_by_may_end" else "open_or_unresolved",
        },
        "final": {"at": record["resolved_at"], "status": "resolved"},
        "schema_version": SCHEMA_VERSION,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for value in values:
            handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def collection_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(records),
        "unique_event_clusters": len({record["event_cluster_id"] for record in records}),
        "status": dict(sorted(collections.Counter(record["may_status"] for record in records).items())),
        "domains": dict(sorted(collections.Counter(record["domain"] for record in records).items())),
        "horizons": dict(sorted(collections.Counter(record["horizon_bucket"] for record in records).items())),
        "temporal_archetypes": dict(sorted(collections.Counter(record["temporal_archetype"] for record in records).items())),
        "topic_families": dict(
            sorted(collections.Counter(record["topic_family"] for record in records if record.get("topic_family")).items())
        ),
        "mechanical_families": dict(
            sorted(
                collections.Counter(
                    record["mechanical_family"] for record in records if record.get("mechanical_family")
                ).items()
            )
        ),
        "difficulty": dict(sorted(collections.Counter(record["forecast_difficulty"] for record in records).items())),
        "deadline_audit": dict(sorted(collections.Counter(record["deadline_audit"] for record in records).items())),
        "quality_score": {
            "min": min(record["quality_score"] for record in records),
            "max": max(record["quality_score"] for record in records),
            "mean": round(sum(record["quality_score"] for record in records) / len(records), 3),
        },
    }


def export_collection(
    public_root: Path,
    private_root: Path,
    records: list[dict[str, Any]],
    verification: dict[str, dict[str, Any]],
    year: int,
) -> list[Path]:
    questions = [public_question(record) for record in records]
    paths = [
        public_root / "questions.json",
        public_root / "questions.jsonl",
        private_root / "labels_sealed.jsonl",
        private_root / "provenance_private.jsonl",
        private_root / "status_snapshots.jsonl",
    ]
    write_json(paths[0], questions)
    write_jsonl(paths[1], questions)
    write_jsonl(paths[2], (sealed_label(record, verification.get(record["id"])) for record in records))
    write_jsonl(paths[3], (private_provenance(record) for record in records))
    write_jsonl(paths[4], (status_snapshot(record, year) for record in records))
    return paths


def markdown_table(mapping: dict[str, Any], left: str, right: str) -> str:
    lines = [f"| {left} | {right} |", "|---|---:|"]
    lines.extend(f"| `{key}` | {value} |" for key, value in mapping.items())
    return "\n".join(lines)


def build_data_card(
    output: Path,
    year: int,
    candidate_stats: dict[str, Any],
    selected_stats: dict[str, Any],
    rejection_counts: dict[str, int],
    generated_at: str,
) -> Path:
    path = output / "README.md"
    text = f"""# Polymarket March {year} past-bench seed set

Status: **draft / human review required**  
Generated: `{generated_at}`  
Schema: `{SCHEMA_VERSION}`

This directory contains a 600-question candidate pool and a 300-question selected
set. Both are compatible with the FutureX question shape (`id`, `prompt`,
`end_time`, `level`, `en_title`) and add safe Raven metadata. Agent-visible files
under `agent_view/` are physically separated from final outcomes and source IDs
under `private/`.

## Frozen time definition

- Assumed target year: **{year}**.
- March availability: a market began accepting orders before `{year}-04-01T00:00:00Z`,
  had not resolved before `{year}-03-01T00:00:00Z`, and its effective event deadline
  was not already past. `acceptingOrdersTimestamp` is preferred; `startDate` is a
  flagged fallback.
- Forecast anchor: the later of `{year}-03-01T00:00:00Z` and the market's first
  accepting-orders timestamp.
- May status checkpoint: `{year}-06-01T00:00:00Z` (exclusive boundary).
- Every final task is now resolved. The later-settled stratum was unresolved at
  the May checkpoint but acquired a final Yes/No outcome later.

## Files

- `agent_view/candidates_600/questions.json`: FutureX-compatible candidate input.
- `agent_view/selected_300/questions.json`: final FutureX-compatible agent input.
- `private/*/labels_sealed.jsonl`: final answers and May checkpoint state; never expose to the agent.
  Published in encrypted form only, at the repository root under `answers/`.
- `private/*/provenance_private.jsonl`: source IDs/URLs, deadline audit, and selection scores.
- `private/*/status_snapshots.jsonl`: anchor, May-end, and final status records.
- `private/raw/gamma_markets.jsonl`: current Gamma API source view, including outcome-bearing fields.
- `private/raw/gamma_pages.jsonl`: request/page receipts and hashes.
- `private/screening_rejections.jsonl`: rejected source IDs and reason codes.
- `information_policy.json`: operator-side frozen retrieval and source-blocking contract.
- `manifest.json`: parameters, counts, quotas, provenance, and file hashes.

## Candidate pool

{markdown_table(candidate_stats['domains'], 'Domain', 'Questions')}

Status balance:

{markdown_table(candidate_stats['status'], 'Status at May end', 'Questions')}

## Selected set

{markdown_table(selected_stats['domains'], 'Domain', 'Questions')}

Status balance:

{markdown_table(selected_stats['status'], 'Status at May end', 'Questions')}

## Screening exclusions

{markdown_table(rejection_counts, 'Reason', 'Source markets')}

## Important limitations

1. Gamma is a current database view, not a March historical snapshot. The prompt
   uses the current resolution description because Gamma does not expose general
   question/description version history. Every task therefore remains
   `automated_needs_human_review` until the March wording is independently archived.
2. `endDate` is known to be wrong for some markets. The builder first extracts a
   deadline from the question and records any >3-day mismatch; those rows need
   human adjudication before benchmark release.
3. Selection scores are deterministic heuristics, not two-reviewer blind ratings.
   They implement the desired diversity and temporal-difficulty preference but do
   not replace manual review.
4. The 300 questions are one per Polymarket event cluster. This prevents large
   multi-outcome/date-bucket events from dominating the benchmark.
5. Market probabilities and current prices are intentionally absent from agent
   input. They remain only in the private raw source file.
6. Discovery is stratified across 11 non-sports Gamma tags. Sports and high-frequency
   price markets are intentionally outside this seed set; this is a selected pool,
   not a census of every market that was open in March.
7. Only mount `agent_view/` in an agent sandbox. The output root intentionally also
   contains sealed labels and source identifiers for benchmark operators.
8. Exact market wording can identify the source on an unrestricted web search.
   Enforce `information_policy.json`; file separation alone is not a retrieval sandbox.

## Rebuild

```bash
python3 scripts/build_polymarket_past_pool.py --year {year}
python3 scripts/validate_polymarket_past_pool.py
```

Official source references:

- Polymarket Gamma events API: https://docs.polymarket.com/api-reference/events/list-events-keyset-pagination
- Polymarket public CLOB fields: https://docs.polymarket.com/trading/clients/public
- FutureX public dataset: https://huggingface.co/datasets/futurex-ai/Futurex-Online
"""
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--month", type=int, default=3)
    parser.add_argument("--candidate-count", type=int, default=600)
    parser.add_argument("--selected-count", type=int, default=300)
    parser.add_argument("--max-pages", type=int, default=250)
    parser.add_argument("--seed", default="raven-polymarket-march-2026-v1")
    parser.add_argument("--clob-workers", type=int, default=8)
    parser.add_argument("--skip-clob-verification", action="store_true")
    parser.add_argument("--reuse-raw", action="store_true", help="Reuse raw/*.jsonl and rerun screening/selection offline")
    parser.add_argument("--output", type=Path, default=Path("data/polymarket-march-2026"))
    args = parser.parse_args()
    if args.month != 3:
        raise SystemExit("v1 status helpers currently require --month 3")
    if args.selected_count > args.candidate_count:
        raise SystemExit("selected-count must not exceed candidate-count")

    generated_at = iso_z(dt.datetime.now(UTC))
    args.output.mkdir(parents=True, exist_ok=True)
    private_root = args.output / "private"
    id_secret_path = private_root / "id_secret.hex"
    if id_secret_path.exists():
        id_secret = bytes.fromhex(id_secret_path.read_text(encoding="utf-8").strip())
        if len(id_secret) < 16:
            raise SystemExit(f"Invalid ID secret at {id_secret_path}")
    else:
        id_secret = secrets.token_bytes(32)
        id_secret_path.parent.mkdir(parents=True, exist_ok=True)
        id_secret_path.write_text(id_secret.hex() + "\n", encoding="utf-8")
        id_secret_path.chmod(0o600)
    raw_market_path = private_root / "raw/gamma_markets.jsonl"
    raw_page_path = private_root / "raw/gamma_pages.jsonl"
    if args.reuse_raw:
        if not raw_market_path.exists() or not raw_page_path.exists():
            raise SystemExit("--reuse-raw requested but raw Gamma files do not exist")
        print(f"Reusing {raw_market_path}...", flush=True)
        raw_markets = read_jsonl(raw_market_path)
        page_receipts = read_jsonl(raw_page_path)
    else:
        print(f"Fetching Gamma universe for March {args.year}...", flush=True)
        raw_markets, page_receipts = fetch_gamma_universe(args.year, args.month, args.max_pages)
    write_jsonl(raw_market_path, raw_markets)
    write_jsonl(raw_page_path, page_receipts)

    eligible: list[dict[str, Any]] = []
    rejection_rows: list[dict[str, Any]] = []
    rejection_counts: collections.Counter[str] = collections.Counter()
    for market in raw_markets:
        record, reasons = normalize_market(market, args.year, args.month, id_secret)
        if record:
            # Quality floor preserves hard, researchable events while keeping enough breadth.
            if record["heuristic_scores"]["temporal_uncertainty"] < 3 or record["quality_score"] < 55:
                reasons = ["below_temporal_quality_floor"]
            else:
                eligible.append(record)
                continue
        for reason in reasons:
            rejection_counts[reason] += 1
        rejection_rows.append({"source_market_id": str(market.get("id") or ""), "reasons": reasons})

    eligible = dedupe_candidates(eligible, args.seed)
    print(f"Source markets: {len(raw_markets)}; eligible after screening/dedupe: {len(eligible)}", flush=True)
    candidates, candidate_quotas, candidate_status_targets = choose_diverse(
        eligible,
        args.candidate_count,
        seed=args.seed + ":candidate",
        cluster_cap=2,
        selected=False,
    )
    selected, selected_quotas, selected_status_targets = choose_diverse(
        candidates,
        args.selected_count,
        seed=args.seed + ":selected",
        cluster_cap=1,
        selected=True,
    )

    verification: dict[str, dict[str, Any]] = {}
    if not args.skip_clob_verification:
        verification = verify_records(selected, args.clob_workers)

    rejection_path = private_root / "screening_rejections.jsonl"
    write_jsonl(rejection_path, rejection_rows)
    exported: list[Path] = [
        raw_market_path,
        raw_page_path,
        rejection_path,
        id_secret_path,
    ]
    exported.extend(
        export_collection(
            args.output / "agent_view/candidates_600",
            private_root / "candidates_600",
            candidates,
            verification,
            args.year,
        )
    )
    information_policy_path = args.output / "information_policy.json"
    write_json(
        information_policy_path,
        {
            "schema_version": "raven.frozen-information-policy.v1",
            "agent_mount_allowlist": [
                "agent_view/candidates_600/questions.json",
                "agent_view/candidates_600/questions.jsonl",
                "agent_view/selected_300/questions.json",
                "agent_view/selected_300/questions.jsonl",
            ],
            # The published answer bundle lives at the repository root, outside this
            # dataset tree. Both spellings are listed so a mount check catches it
            # whether prefixes are resolved against the repo or the dataset root.
            "deny_path_prefixes": ["private/", "answers/", "../../answers/"],
            "retrieval_mode": "frozen_corpus_only",
            "deny_live_internet": True,
            "enforce_document_crawl_time_lte_task_forecast_anchor": True,
            "blocked_domains": [
                "polymarket.com",
                "gamma-api.polymarket.com",
                "clob.polymarket.com",
                "manifold.markets",
                "kalshi.com",
            ],
            "blocked_content_classes": [
                "prediction_market_pages",
                "market_odds_or_prices",
                "benchmark_private_labels",
                "encrypted_answer_bundle",
                "post_anchor_documents",
            ],
        },
    )
    exported.append(information_policy_path)
    exported.extend(
        export_collection(
            args.output / "agent_view/selected_300",
            private_root / "selected_300",
            selected,
            verification,
            args.year,
        )
    )
    candidate_stats = collection_stats(candidates)
    selected_stats = collection_stats(selected)
    data_card = build_data_card(
        args.output,
        args.year,
        candidate_stats,
        selected_stats,
        dict(sorted(rejection_counts.items())),
        generated_at,
    )
    exported.append(data_card)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "selector_version": SELECTOR_VERSION,
        "generated_at": generated_at,
        "assumed_year": args.year,
        "target_month": args.month,
        "availability_semantics": "tradable_at_any_time_during_march_assumed_from_accepting_orders_and_resolution_window",
        "march_start_utc": f"{args.year}-03-01T00:00:00Z",
        "march_end_exclusive_utc": f"{args.year}-04-01T00:00:00Z",
        "may_status_cutoff_exclusive_utc": f"{args.year}-06-01T00:00:00Z",
        "source": {
            "gamma_endpoint": f"{GAMMA_BASE}/events/keyset",
            "discovery_tags": DISCOVERY_TAGS,
            "gamma_page_count": len(page_receipts),
            "raw_market_count": len(raw_markets),
            "retrieval_is_current_view_not_historical_snapshot": True,
            "clob_endpoint": f"{CLOB_BASE}/markets/{{condition_id}}",
        },
        "selection": {
            "seed": args.seed,
            "eligible_count": len(eligible),
            "candidate_count": len(candidates),
            "selected_count": len(selected),
            "candidate_domain_quotas": candidate_quotas,
            "candidate_status_targets": candidate_status_targets,
            "selected_domain_quotas": selected_quotas,
            "selected_status_targets": selected_status_targets,
            "candidate_cluster_cap": 2,
            "selected_cluster_cap": 1,
            "price_questions_excluded": True,
            "manual_exclusion_count": len(MANUAL_EXCLUSION_IDS),
            "manual_exclusion_file": str(MANUAL_EXCLUSION_FILE.relative_to(Path(__file__).resolve().parent.parent)),
            "human_review_complete": False,
        },
        "candidate_stats": candidate_stats,
        "selected_stats": selected_stats,
        "clob_verification": dict(sorted(collections.Counter(value["status"] for value in verification.values()).items())),
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "files": {},
    }
    for path in sorted(exported):
        relative = str(path.relative_to(args.output))
        manifest["files"][relative] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    write_json(args.output / "manifest.json", manifest)

    print(json.dumps({"candidate_stats": candidate_stats, "selected_stats": selected_stats}, indent=2), flush=True)
    print(f"Wrote dataset to {args.output.resolve()}", flush=True)


if __name__ == "__main__":
    main()
