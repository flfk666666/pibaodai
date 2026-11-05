"""Calculate versioned project-rule scores; never estimate population ranks.

The caller supplies the published anchors and evidence for each item. This
module checks and combines those decisions; it does not validate the rubric
or turn an interview into a standardized test. A score of 60 is the project's
declared practical baseline, not a population mean or percentile.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP

ANCHORS = frozenset((0, 20, 40, 60, 80, 100))
BASELINE = 60
HUNDRED = Decimal(100)


def _number(value):
    """Keep whole quantities readable while retaining fractional weights."""
    return int(value) if value == value.to_integral_value() else float(value)


def calculate_axis(items):
    """Return the observed weighted mean and the full missing-data range.

    Items must declare weights summing to 100. Unknown scores remain unknown;
    the displayed mean uses only known positive weights, while lower/upper
    retain the original denominator and assign unknown weights 0/100 solely
    to calculate mathematical limits. These limits are not confidence bounds.
    A zero-weight item is a fact outside this rule score and must stay null.
    """
    if not isinstance(items, list) or not items:
        raise ValueError("Provide a nonempty list of explicitly weighted items")
    identifiers = set()
    rows = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each item must be an object")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in identifiers:
            raise ValueError("Item IDs must be nonempty and unique")
        identifiers.add(identifier)
        weight = item.get("weight")
        if type(weight) not in (int, float):
            raise ValueError("Weights must be finite nonnegative numbers, not booleans")
        weight = Decimal(str(weight))
        if not weight.is_finite() or weight < 0:
            raise ValueError("Weights must be finite nonnegative numbers")
        if "score" not in item:
            raise ValueError("Each item must explicitly provide an anchor score or null")
        score = item["score"]
        if score is not None and (type(score) is not int or score not in ANCHORS):
            raise ValueError("Scores must be 0, 20, 40, 60, 80, 100, or null")
        if not weight and score is not None:
            raise ValueError("Zero-weight facts must remain unscored")
        for field in ("anchor", "reason"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Each item needs a nonempty {field}")
        rows.append((identifier, weight, score))
    if sum((weight for _, weight, _ in rows), Decimal(0)) != HUNDRED:
        raise ValueError("Declared item weights must sum to 100")

    known = [(identifier, weight, score) for identifier, weight, score in rows
             if weight > 0 and score is not None]
    known_weight = sum((weight for _, weight, _ in known), Decimal(0))
    weighted_sum = sum((weight * score for _, weight, score in known), Decimal(0))
    missing_weight = HUNDRED - known_weight
    observed = weighted_sum / known_weight if known_weight else None
    displayed = int(observed.quantize(Decimal(1), rounding=ROUND_HALF_UP)) if observed is not None else None
    terms = " + ".join(f"{score}×{_number(weight)}" for _, weight, score in known)
    formula = (f"({terms}) ÷ {_number(known_weight)} = {displayed}"
               if known_weight else "无已评分权重，分数留空")
    if missing_weight:
        formula += f"；未知权重 {_number(missing_weight)}%，未当作0分计入均值"
    return {
        "score": displayed,
        "known_weight": _number(known_weight),
        "coverage_pct": _number(known_weight),
        "scored_items": len(known),
        "total_weighted_items": sum(weight > 0 for _, weight, _ in rows),
        "lower": _number(weighted_sum / HUNDRED),
        "upper": _number((weighted_sum + missing_weight * HUNDRED) / HUNDRED),
        "formula": formula,
        "delta_from_60": displayed - BASELINE if displayed is not None else None,
        "partial": known_weight < HUNDRED,
    }


def calculate_report(report):
    """Copy and recalculate exactly six axes without reading regional data."""
    if not isinstance(report, dict):
        raise ValueError("The report must be an object")
    if report.get("rating_type") != "anchored_review" or report.get("version") != "anchored-review-v0.2":
        raise ValueError("Use the explicit anchored-review-v0.2 report contract")
    if type(report.get("baseline")) is not int or report["baseline"] != BASELINE:
        raise ValueError("This rule version uses project baseline 60, not a population average")
    if report.get("population_percentile") is not None:
        raise ValueError("Project-rule scores cannot claim population percentiles")
    axes = report.get("axes")
    if (not isinstance(axes, list) or len(axes) != 6
            or not all(isinstance(axis, dict) for axis in axes)
            or [axis.get("id") for axis in axes] != list("ABCDEF")):
        raise ValueError("Provide exactly six axes in A, B, C, D, E, F order")
    result = deepcopy(report)
    for axis in result["axes"]:
        if axis.get("population_percentile") is not None:
            raise ValueError("An axis rule score cannot claim a population percentile")
        axis.update(calculate_axis(axis.get("items")))
    result["population_percentile"] = None
    return result
