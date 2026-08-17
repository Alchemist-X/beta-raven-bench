# Polymarket March 2026 past-bench seed set

Status: **draft / human review required**  
Generated: `2026-08-17T08:02:49.289567Z`  
Schema: `raven.polymarket-past-pool.v1`

This directory contains a 600-question candidate pool and a 300-question selected
set. Both are compatible with the FutureX question shape (`id`, `prompt`,
`end_time`, `level`, `en_title`) and add safe Raven metadata. Agent-visible files
under `agent_view/` are physically separated from final outcomes and source IDs
under `private/`.

The public `beta-raven-bench` repository tracks `agent_view/`, this data card,
the aggregate manifest, the information policy, and the reproducible builder.
All `private/` paths listed below are operator-only local artifacts and are
intentionally absent from the public Git history.

## Frozen time definition

- Assumed target year: **2026**.
- March availability: a market began accepting orders before `2026-04-01T00:00:00Z`,
  had not resolved before `2026-03-01T00:00:00Z`, and its effective event deadline
  was not already past. `acceptingOrdersTimestamp` is preferred; `startDate` is a
  flagged fallback.
- Forecast anchor: the later of `2026-03-01T00:00:00Z` and the market's first
  accepting-orders timestamp.
- May status checkpoint: `2026-06-01T00:00:00Z` (exclusive boundary).
- Every final task is now resolved. The later-settled stratum was unresolved at
  the May checkpoint but acquired a final Yes/No outcome later.

## Files

- `agent_view/candidates_600/questions.json`: FutureX-compatible candidate input.
- `agent_view/selected_300/questions.json`: final FutureX-compatible agent input.
- `private/*/labels_sealed.jsonl`: final answers and May checkpoint state; never expose to the agent.
- `private/*/provenance_private.jsonl`: source IDs/URLs, deadline audit, and selection scores.
- `private/*/status_snapshots.jsonl`: anchor, May-end, and final status records.
- `private/raw/gamma_markets.jsonl`: current Gamma API source view, including outcome-bearing fields.
- `private/raw/gamma_pages.jsonl`: request/page receipts and hashes.
- `private/screening_rejections.jsonl`: rejected source IDs and reason codes.
- `information_policy.json`: operator-side frozen retrieval and source-blocking contract.
- `manifest.json`: parameters, counts, quotas, provenance, and file hashes.

## Candidate pool

| Domain | Questions |
|---|---:|
| `ai_technology` | 70 |
| `business_organizations` | 16 |
| `climate_environment` | 23 |
| `culture_media` | 44 |
| `geopolitics_conflict` | 151 |
| `health_public_safety` | 3 |
| `law_regulation` | 17 |
| `macro_public_policy` | 49 |
| `other` | 60 |
| `politics_elections` | 146 |
| `science_space` | 21 |

Status balance:

| Status at May end | Questions |
|---|---:|
| `resolved_by_may_end` | 300 |
| `unresolved_at_may_end_but_later_settled` | 300 |

## Selected set

| Domain | Questions |
|---|---:|
| `ai_technology` | 44 |
| `business_organizations` | 12 |
| `climate_environment` | 14 |
| `culture_media` | 29 |
| `geopolitics_conflict` | 72 |
| `health_public_safety` | 2 |
| `law_regulation` | 13 |
| `macro_public_policy` | 24 |
| `other` | 31 |
| `politics_elections` | 48 |
| `science_space` | 11 |

Status balance:

| Status at May end | Questions |
|---|---:|
| `resolved_by_may_end` | 150 |
| `unresolved_at_may_end_but_later_settled` | 150 |

## Screening exclusions

| Reason | Source markets |
|---|---:|
| `below_temporal_quality_floor` | 17038 |
| `deadline_at_or_before_anchor` | 17 |
| `deadline_before_march` | 998 |
| `internally_inconsistent_resolution_criteria` | 18 |
| `manual_multi_reviewer_exclusion` | 122 |
| `missing_available_time` | 1 |
| `missing_deadline` | 201 |
| `non_self_contained_anonymous_option` | 5649 |
| `not_available_by_march_end` | 375 |
| `not_final_or_void` | 8 |
| `not_yes_no` | 92 |
| `price_related:asset_threshold` | 455 |
| `price_related:currency_threshold` | 513 |
| `price_related:explicit_price` | 159 |
| `price_related:index_or_asset_settlement` | 411 |
| `price_related:market_dependent_resolution` | 18 |
| `price_related:net_worth_threshold` | 27 |
| `price_related:odds_or_market_probability` | 14 |
| `price_related:real_estate_value` | 175 |
| `price_related:valuation` | 277 |
| `routine_reporting_task_excluded` | 294 |
| `short_horizon_election_margin_bucket` | 49 |
| `sports_fixed_schedule_source_excluded` | 104 |

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
python3 scripts/build_polymarket_past_pool.py --year 2026
python3 scripts/validate_polymarket_past_pool.py

# Public checkout without operator-only artifacts
python3 scripts/validate_polymarket_past_pool.py --public-only
```

Official source references:

- Polymarket Gamma events API: https://docs.polymarket.com/api-reference/events/list-events-keyset-pagination
- Polymarket public CLOB fields: https://docs.polymarket.com/trading/clients/public
- FutureX public dataset: https://huggingface.co/datasets/futurex-ai/Futurex-Online
