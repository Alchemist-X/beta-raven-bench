#!/usr/bin/env python3
"""Validate the generated Polymarket March 2026 past-bench seed set."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_FUTUREX = {"id", "prompt", "end_time", "level", "en_title"}
ALLOWED_LEVELS = {1, 2, 3, 4}


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise AssertionError(f"{path}:{number}: invalid JSON: {error}") from error
        assert isinstance(value, dict), f"{path}:{number}: expected object"
        rows.append(value)
    return rows


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_public_collection(public_root: Path, expected: int) -> dict[str, Any]:
    """Validate files that are safe to ship in the public repository."""
    questions_json = json.loads((public_root / "questions.json").read_text(encoding="utf-8"))
    questions_jsonl = load_jsonl(public_root / "questions.jsonl")
    assert isinstance(questions_json, list)
    assert len(questions_json) == len(questions_jsonl) == expected
    assert questions_json == questions_jsonl, f"{public_root}: JSON and JSONL question views differ"

    ids = [row["id"] for row in questions_json]
    assert len(ids) == len(set(ids)), f"{public_root}: duplicate question IDs"
    for row in questions_json:
        assert REQUIRED_FUTUREX <= set(row), f"{public_root}: missing FutureX fields for {row.get('id')}"
        assert isinstance(row["id"], str) and row["id"]
        assert isinstance(row["prompt"], str) and row["prompt"]
        assert isinstance(row["en_title"], str) and row["en_title"]
        assert row["level"] in ALLOWED_LEVELS
        assert "ground_truth" not in row and "winning_outcome" not in row
        lowered = row["prompt"].lower()
        for leak in ("outcomeprices", "closedtime", "winning outcome", "ground truth", "polymarket", "gamma", "clob"):
            assert leak not in lowered, f"{public_root}: agent-visible leak marker {leak} in {row['id']}"
        assert "http://" not in lowered and "https://" not in lowered, f"{public_root}: live URL in {row['id']}"
        assert not re.search(
            r"\b(?:[a-z0-9-]+\.)+(?:com|org|net|gov|edu|io|ai|co|uk|de|fr|ch|cl)(?:/|\b)",
            lowered,
        ), f"{public_root}: live domain in {row['id']}"
        assert "event_cluster_id" not in row and "source_type" not in row
        title = row["en_title"]
        assert not re.search(r"\bVIX\b|median (?:home|house|property) (?:value|price)", title, re.I)
        assert not re.search(r"\b(?:person|candidate|bank|party|movie|film|song)\s+[a-z]\b", title, re.I)

    return {
        "count": expected,
        "domains": dict(sorted(collections.Counter(row["domain"] for row in questions_json).items())),
    }


def validate_collection(
    public_root: Path, private_root: Path, expected: int, *, cluster_cap: int, require_clob: bool
) -> dict[str, Any]:
    questions_json = json.loads((public_root / "questions.json").read_text(encoding="utf-8"))
    questions_jsonl = load_jsonl(public_root / "questions.jsonl")
    labels = load_jsonl(private_root / "labels_sealed.jsonl")
    provenance = load_jsonl(private_root / "provenance_private.jsonl")
    snapshots = load_jsonl(private_root / "status_snapshots.jsonl")

    assert isinstance(questions_json, list)
    assert len(questions_json) == len(questions_jsonl) == len(labels) == len(provenance) == len(snapshots) == expected
    assert questions_json == questions_jsonl, f"{public_root}: JSON and JSONL question views differ"

    ids = [row["id"] for row in questions_json]
    assert len(ids) == len(set(ids)), f"{public_root}: duplicate question IDs"
    assert set(ids) == {row["id"] for row in labels} == {row["id"] for row in provenance} == {row["id"] for row in snapshots}

    for row in questions_json:
        assert REQUIRED_FUTUREX <= set(row), f"{public_root}: missing FutureX fields for {row.get('id')}"
        assert isinstance(row["id"], str) and row["id"]
        assert isinstance(row["prompt"], str) and row["prompt"]
        assert isinstance(row["en_title"], str) and row["en_title"]
        assert row["level"] in ALLOWED_LEVELS
        assert "ground_truth" not in row and "winning_outcome" not in row
        lowered = row["prompt"].lower()
        for leak in ("outcomeprices", "closedtime", "winning outcome", "ground truth", "polymarket", "gamma", "clob"):
            assert leak not in lowered, f"{public_root}: agent-visible leak marker {leak} in {row['id']}"
        assert "http://" not in lowered and "https://" not in lowered, f"{public_root}: live URL in {row['id']}"
        assert not re.search(
            r"\b(?:[a-z0-9-]+\.)+(?:com|org|net|gov|edu|io|ai|co|uk|de|fr|ch|cl)(?:/|\b)",
            lowered,
        ), f"{public_root}: live domain in {row['id']}"
        assert "event_cluster_id" not in row and "source_type" not in row
        title = row["en_title"]
        assert not re.search(r"\bVIX\b|median (?:home|house|property) (?:value|price)", title, re.I)
        assert not re.search(r"\b(?:person|candidate|bank|party|movie|film|song)\s+[a-z]\b", title, re.I)

    provenance_by_id = {row["id"]: row for row in provenance}
    labels_by_id = {row["id"]: row for row in labels}
    cluster_counts = collections.Counter(row["event_cluster_id"] for row in provenance)
    assert max(cluster_counts.values()) <= cluster_cap

    for row_id in ids:
        private = provenance_by_id[row_id]
        label = labels_by_id[row_id]
        anchor = parse_time(private["forecast_anchor"])
        deadline = parse_time(private["effective_deadline"])
        resolved = parse_time(label["resolved_at"])
        assert anchor < deadline, f"{row_id}: anchor must precede deadline"
        assert anchor < resolved, f"{row_id}: anchor must precede resolution"
        assert label["ground_truth"] in {"A", "B"}
        assert (label["ground_truth"] == "A") == (label["winning_outcome"] == "Yes")
        assert label["status_as_of_may_end"] in {
            "resolved_by_may_end",
            "unresolved_at_may_end_but_later_settled",
        }
        if require_clob:
            verification = label["clob_verification"]
            assert verification["status"] == "verified", f"{row_id}: CLOB outcome not verified"
            assert verification["opened_at_match"] is True, f"{row_id}: CLOB available time mismatch"

    return {
        "count": expected,
        "unique_clusters": len(cluster_counts),
        "domains": dict(sorted(collections.Counter(row["domain"] for row in questions_json).items())),
        "status": dict(sorted(collections.Counter(row["status_as_of_may_end"] for row in labels).items())),
        "winners": dict(sorted(collections.Counter(row["winning_outcome"] for row in labels).items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("data/polymarket-march-2026"))
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Validate only tracked agent-view files and aggregate manifest claims",
    )
    args = parser.parse_args()

    manifest = json.loads((args.root / "manifest.json").read_text(encoding="utf-8"))
    for relative, receipt in manifest["files"].items():
        path = args.root / relative
        if args.public_only and relative.startswith("private/"):
            continue
        assert path.exists(), f"manifest file missing: {relative}"
        assert path.stat().st_size == receipt["bytes"], f"size mismatch: {relative}"
        assert sha256_file(path) == receipt["sha256"], f"hash mismatch: {relative}"

    if args.public_only:
        candidate = validate_public_collection(args.root / "agent_view/candidates_600", 600)
        selected = validate_public_collection(args.root / "agent_view/selected_300", 300)
        candidate_ids = {
            row["id"]
            for row in json.loads((args.root / "agent_view/candidates_600/questions.json").read_text())
        }
        selected_ids = {
            row["id"]
            for row in json.loads((args.root / "agent_view/selected_300/questions.json").read_text())
        }
        assert selected_ids <= candidate_ids, "selected set is not a subset of candidate pool"
        assert manifest["selection"]["candidate_count"] == 600
        assert manifest["selection"]["selected_count"] == 300
        assert manifest["selected_stats"]["status"] == {
            "resolved_by_may_end": 150,
            "unresolved_at_may_end_but_later_settled": 150,
        }
        assert manifest["clob_verification"].get("verified") == 300
        assert len(selected["domains"]) >= 8, "selected set lacks domain heterogeneity"
        print(json.dumps({"valid": True, "mode": "public_only", "candidate": candidate, "selected": selected}, indent=2))
        return

    candidate = validate_collection(
        args.root / "agent_view/candidates_600",
        args.root / "private/candidates_600",
        600,
        cluster_cap=2,
        require_clob=False,
    )
    selected = validate_collection(
        args.root / "agent_view/selected_300",
        args.root / "private/selected_300",
        300,
        cluster_cap=1,
        require_clob=True,
    )
    candidate_ids = {
        row["id"] for row in json.loads((args.root / "agent_view/candidates_600/questions.json").read_text())
    }
    selected_ids = {
        row["id"] for row in json.loads((args.root / "agent_view/selected_300/questions.json").read_text())
    }
    assert selected_ids <= candidate_ids, "selected set is not a subset of candidate pool"
    assert selected["status"].get("resolved_by_may_end") == 150
    assert selected["status"].get("unresolved_at_may_end_but_later_settled") == 150
    assert len(selected["domains"]) >= 8, "selected set lacks domain heterogeneity"

    print(json.dumps({"valid": True, "candidate": candidate, "selected": selected}, indent=2))


if __name__ == "__main__":
    main()
