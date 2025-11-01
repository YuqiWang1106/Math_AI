import re
from typing import Dict, List

from langchain.prompts import PromptTemplate

Label = str  # kept for parity with arithmetic module

GEOMETRY_KB: Dict[str, List[str]] = {
    "global": [
        "Geometry evaluations focus on describing shapes, graphs, transformations, similarity, congruence, and measurements accurately.",
        "Label definitions: Know-Know = relevant and correct; Know-Don't Know = the student explicitly admits uncertainty or missing knowledge; False Knowledge = relevant but wrong; Omission = required idea never mentioned; Irrelevant Knowledge = off-topic information.",
        "Always ground feedback in concrete geometric features such as coordinates, angles, lengths, slopes, and symmetry.",
    ],
    "general_geometry": [
        "Use precise geometric features: coordinates, lengths, angles, slopes, symmetry, transformations, similarity, and congruence.",
        "Check definitions against the object: verify slope-intercept for lines, center-radius for circles, and angle/side properties for polygons.",
        "Always perform a quick verification: substitute coordinates, compare slopes, test symmetry, or check distances.",
        "When describing graphs, address key points, symmetry or axes, domain, range, and monotonicity where relevant.",
    ],
    "quadratic_parabola": [
        "For y = x^2, the vertex is (0,0).",
        "For y = x^2, the axis of symmetry is x = 0 (the y-axis).",
        "For y = x^2, the graph opens upward and is symmetric about x = 0.",
        "For y = x^2, the domain is all real numbers; the range is y ≥ 0.",
        "For y = x^2, the function decreases on x < 0 and increases on x > 0.",
        "Points such as (±1, 1) and (±2, 4) lie on the curve.",
    ],
    "absolute_value": [
        "For y = |x|, the vertex is (0,0).",
        "For y = |x|, the graph is V-shaped, symmetric about x = 0, and opens upward.",
        "For y = |x|, the domain is all real numbers and the range is y ≥ 0.",
        "For y = |x|, the function decreases on x < 0 and increases on x > 0.",
    ],
    "linear": [
        "For y = mx + b, slope m determines whether the line increases (m > 0), decreases (m < 0), or is constant (m = 0).",
        "For y = mx + b, the y-intercept is (0, b).",
        "All non-vertical lines have domain and range equal to all real numbers.",
        "Parallel lines share equal slopes; perpendicular non-vertical lines have slopes whose product is -1.",
    ],
    "circle": [
        "For (x - h)^2 + (y - k)^2 = r^2, the center is (h, k) with radius r > 0.",
        "Points on the circle are exactly distance r from the center.",
        "A circle is symmetric about the vertical and horizontal lines through its center.",
        "Diameter = 2r, circumference = 2πr, area = πr^2.",
    ],
    "triangle": [
        "The sum of the interior angles of a triangle is 180 degrees.",
        "Similarity criteria include AA, SAS (proportional), and SSS (proportional).",
        "Congruence criteria include SSS, SAS, ASA, AAS, and HL for right triangles.",
    ],
    "distance_midpoint": [
        "Distance between (x1, y1) and (x2, y2) is sqrt((x2 - x1)^2 + (y2 - y1)^2).",
        "The midpoint of two points is ((x1 + x2)/2, (y1 + y2)/2).",
    ],
    "transformations": [
        "Translations, rotations, and reflections are rigid motions that preserve distance and angle measure; dilations change size but keep shape.",
        "Reflections preserve distance and angle measure while reversing orientation.",
    ],
}

GEOMETRY_TOPIC_TITLES: Dict[str, str] = {
    "quadratic_parabola": "Quadratic / Parabola (e.g., y = x^2)",
    "absolute_value": "Absolute Value (e.g., y = |x|)",
    "linear": "Linear Function (y = mx + b)",
    "circle": "Circle Geometry",
    "triangle": "Triangles (Similarity & Congruence)",
    "distance_midpoint": "Coordinate Geometry (Distance & Midpoint)",
    "transformations": "Transformations (Translation / Rotation / Reflection / Dilation)",
    "general_geometry": "Geometry (General)",
}


def route_geometry_topic(problem: str, student_text: str, fallback: str = "quadratic_parabola") -> str:
    text = f"{problem} {student_text}".lower()

    # Normalize common mathematical symbols to aid keyword routing.
    text = text.replace("≤", "<=").replace("≥", ">=").replace("−", "-")
    text = text.replace("|x|", "abs(x)").replace("∣x∣", "abs(x)")
    text = re.sub(r"\s+", " ", text)

    quad_patterns = [
        r"\bx\^2\b",
        r"\by\s*=\s*x\^2\b",
        r"\bparabola\b",
        r"\bquadratic\b",
        r"\bvertex\b",
        r"\baxis of symmetry\b",
    ]
    if any(re.search(pattern, text) for pattern in quad_patterns):
        return "quadratic_parabola"

    abs_patterns = [
        r"\babs\(x\)\b",
        r"y\s*=\s*\|x\|",
        r"\babsolute value\b",
        r"\bv[- ]?shaped\b",
    ]
    if any(re.search(pattern, text) for pattern in abs_patterns):
        return "absolute_value"

    linear_patterns = [
        r"\by\s*=\s*m\s*x\s*\+\s*b\b",
        r"\blinear\b",
        r"\bslope\b",
        r"\bstraight line\b",
        r"\by-intercept\b",
    ]
    if any(re.search(pattern, text) for pattern in linear_patterns):
        return "linear"

    circle_patterns = [
        r"\(x\s*-\s*h\)\^2\s*\+\s*\(y\s*-\s*k\)\^2\s*=\s*r\^2",
        r"\bcircle\b",
        r"\bradius\b",
        r"\bcenter\b",
        r"\bcircumference\b",
        r"\barea\b",
    ]
    if any(re.search(pattern, text) for pattern in circle_patterns):
        return "circle"

    tri_patterns = [
        r"\btriangle\b",
        r"\bcongruence\b",
        r"\bsimilarity\b",
        r"\bsss\b",
        r"\bsas\b",
        r"\basa\b",
        r"\baas\b",
        r"\bhl\b",
        r"\binterior angles\b",
    ]
    if any(re.search(pattern, text) for pattern in tri_patterns):
        return "triangle"

    coord_patterns = [
        r"\bdistance formula\b",
        r"\bmidpoint\b",
        r"\bsqrt\(",
        r"\b\((x1|x_1)\s*[,;]\s*(y1|y_1)\)\b",
        r"\b\((x2|x_2)\s*[,;]\s*(y2|y_2)\)\b",
    ]
    if any(re.search(pattern, text) for pattern in coord_patterns):
        return "distance_midpoint"

    transformation_patterns = [
        r"\btranslation\b",
        r"\brotation\b",
        r"\breflection\b",
        r"\bdilation\b",
        r"\brigid motion\b",
        r"\bisometry\b",
    ]
    if any(re.search(pattern, text) for pattern in transformation_patterns):
        return "transformations"

    if any(keyword in text for keyword in ["point", "coordinate", "angle", "length", "symmetric"]):
        return "general_geometry"

    return fallback


def build_geometry_context(topic_key: str, include_global: bool = True, max_refs: int = 12) -> str:
    ordered: List[str] = []

    def _append_many(items: List[str]) -> None:
        for item in items or []:
            if item not in ordered:
                ordered.append(item)

    if include_global:
        _append_many(GEOMETRY_KB.get("global", []))

    _append_many(GEOMETRY_KB.get("general_geometry", []))

    topic_items = GEOMETRY_KB.get(topic_key) or []
    _append_many(topic_items)

    if not topic_items and topic_key not in ("general_geometry", "quadratic_parabola"):
        _append_many(GEOMETRY_KB.get("quadratic_parabola", []))

    if len(ordered) > max_refs:
        ordered = ordered[:max_refs]

    return "\n".join(f"- {line}" for line in ordered)


ZERO_SHOT_SUFFIX = """
You must operate in a strict zero-shot, multi-label classification mode with the fixed label set:
[Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].

Use ONLY the provided {context} (if any) plus the student's text. Do NOT invent facts beyond them.

Return a strict JSON object that matches this schema exactly (no preamble, no markdown):

{
  "title": "<dimension name>",
  "aspects": [
    {
      "aspect": "string",
      "labels": ["Know-Know" | "Know-Don't Know" | "False Knowledge" | "Omission" | "Irrelevant Knowledge", ...],
      "explanation": ">=5 sentences tied to student's wording",
      "model_score_hint": 0.0-1.0
    }
  ],
  "most_critical_gap": "one-sentence"
}
"""


def wrap_prompt_for_zero_shot(base_prompt: str) -> PromptTemplate:
    text = base_prompt.strip() + "\n\n" + ZERO_SHOT_SUFFIX.strip()
    return PromptTemplate.from_template(text, template_format="jinja2")


FACTS_PROMPT_TEMPLATE = """
You are a precise geometry evaluator focusing ONLY on the Facts dimension.

Facts (geometry-specific):
- Key features such as coordinates, lengths, angle measures, symmetry, domain/range descriptions, transformations, parallel/perpendicular relationships.
- Required definitions tied to the referenced geometry topic (parabola, circle, line, absolute value graph, etc.).

Label definitions (use consistently):
- Know-Know: relevant fact stated correctly.
- Know-Don't Know: explicit admission of uncertainty or missing fact.
- False Knowledge: relevant fact stated incorrectly.
- Omission: required fact never appears.
- Irrelevant Knowledge: off-topic information that does not help solve the geometry task.

Student self-assessment:
----------------
{{ student_text }}
----------------

Reference context (use cautiously, do not copy verbatim):
----------------
{{ context }}
----------------

PHASE 1 – Reference Facts
- List the essential geometry facts a strong solution must mention for this topic (coordinates, symmetry, measures, etc.).

PHASE 2 – Student Comparison
1) Extract factual aspects the student covered or missed.
2) Assign all applicable labels from [Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].
3) Give ≥5-sentence explanations tied to the student's wording, and provide corrective guidance for False Knowledge/Omission.
4) Finish with: "Most critical factual gap for this student: <gap + next step>"
"""

STRATEGIES_PROMPT_TEMPLATE = """
You are a precise geometry evaluator focusing ONLY on the Strategies dimension.

Strategies (geometry-specific):
- Plans for analyzing shapes or graphs (plot key points, use symmetry, apply similarity/congruence tests, compare slopes, etc.).
- Verifying features (checking against definitions, using transformations, testing key values).

Label definitions (use consistently):
- Know-Know: relevant and effective strategy stated.
- Know-Don't Know: student openly asks for a strategy or notes they lack one.
- False Knowledge: strategy is misleading or counter-productive.
- Omission: needed strategy never appears.
- Irrelevant Knowledge: plan unrelated to solving the geometry question.

Student self-assessment:
----------------
{{ student_text }}
----------------

Reference context:
----------------
{{ context }}
----------------

PHASE 1 – Reference Strategies
- List high-quality strategies a strong response should include for this topic.

PHASE 2 – Student Comparison
1) Extract stated or missing strategies.
2) Label each with [Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].
3) Provide ≥5-sentence explanations grounded in the student's words, with actionable advice for False Knowledge/Omission.
4) Finish with: "Most critical strategy gap for this student: <gap + next step>"
"""

PROCEDURES_PROMPT_TEMPLATE = """
You are a precise geometry evaluator focusing ONLY on the Procedures dimension.

Procedures (geometry-specific):
- Step-by-step constructions or computations (plotting points, applying transformations, solving for lengths/angles, checking slopes, etc.).
- Verification steps (substituting coordinates, confirming distance, checking congruence or similarity criteria).

Label definitions (use consistently):
- Know-Know: procedure described correctly and in useful order.
- Know-Don't Know: student explicitly admits not knowing a procedure.
- False Knowledge: incorrect or misordered procedure.
- Omission: required procedure omitted entirely.
- Irrelevant Knowledge: procedure unrelated to the geometry task.

Student self-assessment:
----------------
{{ student_text }}
----------------

Reference context:
----------------
{{ context }}
----------------

PHASE 1 – Reference Procedures
- Outline the ideal step sequence to address the problem (include verification checks).

PHASE 2 – Student Comparison
1) Extract procedural aspects.
2) Label with [Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].
3) Provide ≥5-sentence explanations, giving corrective guidance for False Knowledge/Omission.
4) Finish with: "Most critical procedural gap for this student: <gap + next step>"
"""

RATIONALES_PROMPT_TEMPLATE = """
You are a precise geometry evaluator focusing ONLY on the Rationales dimension.

Rationales (geometry-specific):
- Conceptual explanations: why symmetry holds, why a slope indicates direction, why distances match congruence rules, why a transformation keeps shape.

Label definitions (use consistently):
- Know-Know: rationale is relevant and correct.
- Know-Don't Know: student explicitly notes conceptual uncertainty.
- False Knowledge: rationale misapplies or misstates geometry principles.
- Omission: necessary rationale never appears.
- Irrelevant Knowledge: unrelated conceptual talk.

Student self-assessment:
----------------
{{ student_text }}
----------------

Reference context:
----------------
{{ context }}
----------------

PHASE 1 – Reference Rationales
- List key principles that justify the correct procedures/facts (symmetry arguments, congruence, similarity, coordinate reasoning).

PHASE 2 – Student Comparison
1) Extract rationale aspects.
2) Label with [Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].
3) Provide ≥5-sentence explanations, giving precise conceptual corrections for False Knowledge/Omission.
4) Finish with: "Most critical rationale gap for this student: <gap + next step>"
"""


GEOMETRY_FACTS_PROMPT = wrap_prompt_for_zero_shot(FACTS_PROMPT_TEMPLATE)
GEOMETRY_STRATEGIES_PROMPT = wrap_prompt_for_zero_shot(STRATEGIES_PROMPT_TEMPLATE)
GEOMETRY_PROCEDURES_PROMPT = wrap_prompt_for_zero_shot(PROCEDURES_PROMPT_TEMPLATE)
GEOMETRY_RATIONALES_PROMPT = wrap_prompt_for_zero_shot(RATIONALES_PROMPT_TEMPLATE)

GEOMETRY_PROMPTS: Dict[str, PromptTemplate] = {
    "Facts": GEOMETRY_FACTS_PROMPT,
    "Strategies": GEOMETRY_STRATEGIES_PROMPT,
    "Procedures": GEOMETRY_PROCEDURES_PROMPT,
    "Rationales": GEOMETRY_RATIONALES_PROMPT,
}
