import re
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_KNOWLEDGE_DIMENSIONS = ["facts", "strategies", "procedures", "rationales"]

DIMENSION_LABELS = {
    "facts": "Facts",
    "strategies": "Strategies",
    "procedures": "Procedures",
    "rationales": "Rationales",
    "other": "Other",
}


def clamp_probability(value: float, lower: float = 0.01, upper: float = 0.99) -> float:
    return max(lower, min(upper, float(value)))


def update_bkt_probability(
    prior: float,
    is_correct: bool,
    learn_probability: float = 0.18,
    guess_probability: float = 0.2,
    slip_probability: float = 0.1,
) -> float:
    """Update a mastery probability using Bayesian Knowledge Tracing.

    BKT models a student's latent mastery of one knowledge component and updates
    it after each observed correct/incorrect opportunity. The model follows the
    classic Corbett-Anderson four-parameter form: prior, learn, guess, and slip.
    """
    prior = clamp_probability(prior)
    learn_probability = clamp_probability(learn_probability, 0.0, 1.0)
    guess_probability = clamp_probability(guess_probability, 0.0, 0.49)
    slip_probability = clamp_probability(slip_probability, 0.0, 0.49)

    if is_correct:
        numerator = prior * (1 - slip_probability)
        denominator = numerator + ((1 - prior) * guess_probability)
    else:
        numerator = prior * slip_probability
        denominator = numerator + ((1 - prior) * (1 - guess_probability))

    posterior = numerator / denominator if denominator else prior
    learned_after_opportunity = posterior + ((1 - posterior) * learn_probability)
    return round(clamp_probability(learned_after_opportunity), 4)


def extract_knowledge_observations(
    assessment_payload: Dict[str, Any],
    evaluation_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Convert the LLM evaluation output into BKT-ready observations.

    The current evaluator schema is not guaranteed to be stable, so this parser
    intentionally accepts several report shapes and falls back to the submitted
    self-assessment text when a dimension-specific score is absent.
    """
    self_assessment = assessment_payload.get("self_assessment", {}) if isinstance(assessment_payload, dict) else {}
    knowledge_types = self_assessment.get("knowledge_types") or []

    if not knowledge_types:
        knowledge_types = [{"type": dimension, "examples": "", "uncertainties": ""} for dimension in DEFAULT_KNOWLEDGE_DIMENSIONS]

    observations = []
    for knowledge_type in knowledge_types:
        dimension = normalize_dimension(knowledge_type.get("type"))
        examples = knowledge_type.get("examples", "")
        uncertainties = knowledge_type.get("uncertainties", "")
        report_section = find_dimension_report(evaluation_report, dimension)
        score = extract_numeric_score(report_section)
        evidence = {
            "dimension": dimension,
            "student_examples": examples,
            "student_uncertainties": uncertainties,
            "evaluation": report_section,
        }

        has_student_evidence = bool(text_from_any(examples).strip() or text_from_any(uncertainties).strip())
        if not has_student_evidence and report_section in ({}, None, ""):
            continue

        if score is not None:
            is_correct = score >= 0.7
            confidence = max(0.55, min(0.95, abs(score - 0.5) + 0.45))
        else:
            is_correct, confidence = infer_correctness(report_section, examples, uncertainties)

        observations.append(
            {
                "dimension": dimension,
                "knowledge_point": DIMENSION_LABELS.get(dimension, dimension.title()),
                "is_correct": is_correct,
                "confidence": round(confidence, 2),
                "evidence": evidence,
            }
        )

    return observations


def normalize_dimension(value: Any) -> str:
    text = str(value or "other").strip().lower()
    text = re.sub(r"[^a-z0-9_ -]", "", text).replace(" ", "_")
    if text in DIMENSION_LABELS:
        return text
    if text.startswith("fact"):
        return "facts"
    if text.startswith("strateg"):
        return "strategies"
    if text.startswith("procedure"):
        return "procedures"
    if text.startswith("rationale") or text.startswith("reason"):
        return "rationales"
    return "other"


def find_dimension_report(report: Any, dimension: str) -> Any:
    if not isinstance(report, dict):
        return {}

    candidates = [
        report.get(dimension),
        report.get(DIMENSION_LABELS.get(dimension, "")),
        report.get("dimension_analysis", {}).get(dimension) if isinstance(report.get("dimension_analysis"), dict) else None,
        report.get("dimensions", {}).get(dimension) if isinstance(report.get("dimensions"), dict) else None,
    ]

    dimension_analysis = report.get("dimension_analysis")
    if isinstance(dimension_analysis, list):
        for item in dimension_analysis:
            if isinstance(item, dict) and normalize_dimension(item.get("type") or item.get("dimension") or item.get("name")) == dimension:
                candidates.append(item)

    for candidate in candidates:
        if candidate not in (None, "", {}):
            return candidate
    return {}


def extract_numeric_score(section: Any) -> Optional[float]:
    if not isinstance(section, dict):
        return None

    for key in ("score", "mastery", "mastery_probability", "proficiency", "confidence"):
        value = section.get(key)
        if isinstance(value, (int, float)):
            return clamp_probability(value / 100 if value > 1 else value, 0.0, 1.0)
        if isinstance(value, str):
            match = re.search(r"\d+(?:\.\d+)?", value)
            if match:
                number = float(match.group(0))
                return clamp_probability(number / 100 if number > 1 else number, 0.0, 1.0)
    return None


def infer_correctness(section: Any, examples: Any, uncertainties: Any) -> tuple[bool, float]:
    text_blob = text_from_any(section).lower()
    uncertainty_text = text_from_any(uncertainties).strip()
    examples_text = text_from_any(examples).strip()

    negative_markers = (
        "incorrect",
        "missing",
        "misconception",
        "uncertain",
        "not sure",
        "weak",
        "error",
        "incomplete",
        "needs",
    )
    positive_markers = ("correct", "accurate", "complete", "strong", "understand", "good")

    if uncertainty_text:
        return False, 0.7
    if any(marker in text_blob for marker in negative_markers):
        return False, 0.75
    if any(marker in text_blob for marker in positive_markers):
        return True, 0.7
    if examples_text:
        return True, 0.6
    return False, 0.55


def text_from_any(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(text_from_any(item) for item in value.values())
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        return " ".join(text_from_any(item) for item in value)
    return str(value)
