# =========================
# priority_system.py
# =========================
import argparse
import json
import sys
from typing import Dict, List, Tuple, Optional, Any

# ------------------------------------------------------------
# 🧩 第一部分：Label 层逻辑
# ------------------------------------------------------------

LABELS = ["False Knowledge", "Omission", "Know-Don't Know", "Irrelevant Knowledge", "Know-Know"]
BASE_LABEL_WEIGHTS = [0.30, 0.30, 0.25, 0.15, 0.00]

DIFFICULTY_MULT_LABEL = {
    "easy":   [1.15, 1.15, 1.10, 1.05, 1.00],
    "medium": [1.00, 1.00, 1.00, 1.00, 1.00],
    "hard":   [0.90, 0.90, 0.95, 1.00, 1.00],
}

ABILITY_MULT_LABEL = {
    "low":   [0.95, 0.95, 1.10, 1.00, 1.00],
    "mid":   [1.00, 1.00, 1.00, 1.00, 1.00],
    "high":  [1.10, 1.10, 0.95, 1.00, 1.00],
}

DEFAULT_CONTEXT = {"difficulty": "medium", "ability": "mid"}
LABEL_INDEX = {label: idx for idx, label in enumerate(LABELS)}
DIMENSION_ALIASES = {
    "fact": "Fact",
    "facts": "Fact",
    "strategies": "Strategies",
    "strategy": "Strategies",
    "procedure": "Procedure",
    "procedures": "Procedure",
    "rationale": "Rationales",
    "rationales": "Rationales",
}

def _sanitize_counts(counts: List[int]) -> List[int]:
    """Ensure counts vector of length 5 and nonnegative integers."""
    fixed = (list(counts) + [0]*5)[:5]
    return [max(int(c), 0) for c in fixed]

def _pick_multiplier(table: Dict[str, List[float]], key: Optional[str]) -> List[float]:
    return table.get(key, next(iter(table.values())))

def _elementwise_product(a: List[float], b: List[float]) -> List[float]:
    return [x*y for x,y in zip(a,b)]

def _compute_label_weights(context: Optional[Dict[str,str]]) -> List[float]:
    """Dynamic label weights from difficulty × ability."""
    ctx = {**DEFAULT_CONTEXT, **(context or {})}
    diff_m = _pick_multiplier(DIFFICULTY_MULT_LABEL, ctx.get("difficulty"))
    abil_m = _pick_multiplier(ABILITY_MULT_LABEL, ctx.get("ability"))
    w = _elementwise_product(BASE_LABEL_WEIGHTS, diff_m)
    w = _elementwise_product(w, abil_m)
    return w

def _scores_from(counts: List[int], weights: List[float]) -> List[float]:
    return [c*w for c,w in zip(counts, weights)]

def _top_label(scores: List[float]) -> str:
    m = max(scores)
    idx = min(i for i,v in enumerate(scores) if v==m)
    return LABELS[idx]

def compute_label_priority(counts: List[int], *, use_dynamic=True, context=None) -> Tuple[List[float], str]:
    c = _sanitize_counts(counts)
    weights = _compute_label_weights(context) if use_dynamic else BASE_LABEL_WEIGHTS
    scores = _scores_from(c, weights)
    return scores, _top_label(scores)

def _sum_label_scores(counts: List[int], *, use_dynamic=True, context=None) -> float:
    """Return total label score for a given dimension."""
    scores, _ = compute_label_priority(counts, use_dynamic=use_dynamic, context=context)
    return sum(scores)


def _canonical_dimension_name(raw: Optional[str]) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    return DIMENSION_ALIASES.get(raw.strip().lower())


def _extract_dimension_payloads(report: Any) -> Dict[str, Dict[str, Any]]:
    if isinstance(report, str):
        try:
            report = json.loads(report)
        except json.JSONDecodeError:
            return {}

    if not isinstance(report, dict):
        return {}

    matched: Dict[str, Dict[str, Any]] = {}

    for key, value in report.items():
        canon = _canonical_dimension_name(key)
        if canon and isinstance(value, dict):
            matched[canon] = value

    if matched:
        return matched

    dimensions = report.get("dimensions")
    if isinstance(dimensions, dict):
        for key, value in dimensions.items():
            canon = _canonical_dimension_name(key)
            if canon and isinstance(value, dict):
                matched[canon] = value
        if matched:
            return matched
    elif isinstance(dimensions, list):
        for item in dimensions:
            if not isinstance(item, dict):
                continue
            name = (
                _canonical_dimension_name(item.get("dimension"))
                or _canonical_dimension_name(item.get("name"))
                or _canonical_dimension_name(item.get("title"))
            )
            if name and isinstance(item, dict):
                matched[name] = item
        if matched:
            return matched

    return matched


def _tally_labels(labels: Any, counts: List[int]) -> None:
    if not isinstance(labels, (list, tuple)):
        return
    for label in labels:
        if not isinstance(label, str):
            continue
        idx = LABEL_INDEX.get(label.strip())
        if idx is not None:
            counts[idx] += 1


def build_dimension_counts_from_report(report: Any) -> Dict[str, List[int]]:
    """Aggregate label counts per dimension from structured evaluation JSON."""
    dimension_counts = {dim: [0, 0, 0, 0, 0] for dim in DIMENSIONS}
    payloads = _extract_dimension_payloads(report)
    for dim_name, payload in payloads.items():
        aspects = payload.get("aspects", [])
        if not isinstance(aspects, list):
            continue
        counts = dimension_counts[dim_name]
        for aspect in aspects:
            if not isinstance(aspect, dict):
                continue
            _tally_labels(aspect.get("labels"), counts)
    return dimension_counts

# ------------------------------------------------------------
# 🧮 第二部分：Dimension 层逻辑
# ------------------------------------------------------------

DIMENSIONS = ["Fact", "Strategies", "Procedure", "Rationales"]
BASE_DIM_WEIGHTS = [0.35, 0.30, 0.25, 0.10]

DIFFICULTY_MULT_DIM = {
    "easy":   [1.10, 1.05, 1.00, 0.95],
    "medium": [1.00, 1.00, 1.00, 1.00],
    "hard":   [0.95, 1.10, 1.10, 1.00],
}

ABILITY_MULT_DIM = {
    "low":   [1.00, 0.98, 0.98, 1.05],
    "mid":   [1.00, 1.00, 1.00, 1.00],
    "high":  [1.00, 1.05, 1.05, 0.95],
}

def _compute_dimension_weights(context: Optional[Dict[str,str]]) -> List[float]:
    ctx = {**DEFAULT_CONTEXT, **(context or {})}
    diff_m = _pick_multiplier(DIFFICULTY_MULT_DIM, ctx.get("difficulty"))
    abil_m = _pick_multiplier(ABILITY_MULT_DIM, ctx.get("ability"))
    w = _elementwise_product(BASE_DIM_WEIGHTS, diff_m)
    w = _elementwise_product(w, abil_m)
    return w

def _top_dimension(scores: List[float]) -> str:
    m = max(scores)
    idx = min(i for i,v in enumerate(scores) if v==m)
    return DIMENSIONS[idx]

def compute_dimension_priority(
    dimension_counts: Dict[str, List[int]],
    *,
    use_dynamic_labels=True,
    use_dynamic_dimensions=True,
    context=None
) -> Dict[str, Any]:
    """Compute per-dimension scores and pick top dimension."""
    dim_weights = _compute_dimension_weights(context) if use_dynamic_dimensions else BASE_DIM_WEIGHTS
    dim_scores = []

    # 计算每个维度的 E（各自 label 的总得分）
    for dim_name in DIMENSIONS:
        counts = dimension_counts.get(dim_name, [0,0,0,0,0])
        E = _sum_label_scores(counts, use_dynamic=use_dynamic_labels, context=context)
        dim_score = E * dim_weights[DIMENSIONS.index(dim_name)]
        dim_scores.append(dim_score)

    top_dim = _top_dimension(dim_scores)
    return {
        "dimension_scores": dict(zip(DIMENSIONS, dim_scores)),
        "top_dimension": top_dim
    }

# ------------------------------------------------------------
# 🧩 第三部分：综合输出（哪个 dimension + 哪个 label 最重要）
# ------------------------------------------------------------

def compute_full_priority(dimension_counts: Dict[str, List[int]], *, context=None) -> Dict[str, Any]:
    """Return top dimension and its top label."""
    # 1️⃣ 计算维度优先级
    dim_result = compute_dimension_priority(dimension_counts, context=context)
    top_dim = dim_result["top_dimension"]

    # 2️⃣ 找出该维度中最重要的 label
    top_counts = dimension_counts[top_dim]
    label_scores, top_label = compute_label_priority(top_counts, use_dynamic=True, context=context)

    return {
        "top_dimension": top_dim,
        "top_label_in_top_dimension": top_label,
        "dimension_scores": dim_result["dimension_scores"],
        "label_scores_in_top_dimension": dict(zip(LABELS, label_scores)),
    }


def compute_full_priority_from_report(report: Any, *, context=None) -> Dict[str, Any]:
    """Wrapper that tallies counts from a structured report first."""
    counts = build_dimension_counts_from_report(report)
    result = compute_full_priority(counts, context=context)
    result["dimension_counts"] = counts
    return result

# ------------------------------------------------------------
# 🧪 测试样例（写死 counts，可换为数据库统计）
# ------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute priority rankings from a structured labeling report."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a JSON file or an inline JSON string. Reads stdin if omitted.",
    )
    parser.add_argument(
        "--difficulty",
        choices=list(DIFFICULTY_MULT_LABEL.keys()),
        help="Override difficulty context (default: medium).",
    )
    parser.add_argument(
        "--ability",
        choices=list(ABILITY_MULT_LABEL.keys()),
        help="Override ability context (default: mid).",
    )
    parser.add_argument(
        "--context",
        help="Additional JSON snippet with context overrides (merged after difficulty/ability).",
    )
    args = parser.parse_args()

    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as fh:
                raw_payload = fh.read()
        except FileNotFoundError:
            raw_payload = args.input
    else:
        raw_payload = sys.stdin.read()

    try:
        report_data = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse labeling report JSON: {exc}") from exc

    ctx = {**DEFAULT_CONTEXT}
    if args.difficulty:
        ctx["difficulty"] = args.difficulty
    if args.ability:
        ctx["ability"] = args.ability
    if args.context:
        try:
            ctx.update(json.loads(args.context))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid --context JSON: {exc}") from exc

    priority_result = compute_full_priority_from_report(report_data, context=ctx)
    print("===== PRIORITY RESULT =====")
    print(f"Top dimension: {priority_result['top_dimension']}")
    print(f"Top label within top dimension: {priority_result['top_label_in_top_dimension']}")
    print("\nDimension scores:")
    for dim, score in priority_result["dimension_scores"].items():
        print(f"  - {dim}: {score:.4f}")
    print("\nLabel scores in top dimension:")
    for label, score in priority_result["label_scores_in_top_dimension"].items():
        print(f"  - {label}: {score:.4f}")
    print("\nRaw label counts per dimension:")
    for dim, counts in priority_result["dimension_counts"].items():
        counts_str = ", ".join(f"{LABELS[idx]}={count}" for idx, count in enumerate(counts))
        print(f"  - {dim}: {counts_str}")
