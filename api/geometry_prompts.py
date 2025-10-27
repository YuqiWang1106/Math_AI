from typing import Dict, List

from langchain.prompts import PromptTemplate

Label = str  # kept for parity with arithmetic module

GEOMETRY_KB: Dict[str, List[str]] = {
    "global": [
        "Geometry evaluations focus on describing shapes, graphs, transformations, similarity, congruence, and measurements accurately.",
        "Label definitions: Know-Know = relevant and correct; Know-Don't Know = the student explicitly admits uncertainty or missing knowledge; False Knowledge = relevant but wrong; Omission = required idea never mentioned; Irrelevant Knowledge = off-topic information.",
        "Always ground feedback in concrete geometric features such as coordinates, angles, lengths, slopes, and symmetry.",
    ],
    "quadratic_parabola": [
        "For y = x^2, the vertex is (0,0).",
        "For y = x^2, the axis of symmetry is x = 0 (the y-axis).",
        "For y = x^2, the graph opens upward and is symmetric about x = 0.",
        "For y = x^2, the domain is all real numbers; the range is y ≥ 0.",
        "For y = x^2, the graph decreases on x < 0 and increases on x > 0.",
    ],
    "absolute_value": [
        "For y = |x|, the vertex is (0,0).",
        "For y = |x|, the graph is V-shaped, symmetric about x = 0, and opens upward.",
        "For y = |x|, the domain is all real numbers and the range is y ≥ 0.",
        "For y = |x|, the function decreases on x < 0 and increases on x > 0.",
    ],
    "linear": [
        "For y = mx + b, slope m controls whether the line increases (m > 0), decreases (m < 0), or is constant (m = 0).",
        "For y = mx + b, the y-intercept is the point (0, b).",
        "All non-vertical lines have domain and range equal to all real numbers.",
        "Parallel lines have equal slopes; perpendicular lines have slopes whose product is -1 (when both slopes exist).",
    ],
    "circle": [
        "For (x - h)^2 + (y - k)^2 = r^2, the center is (h, k) and the radius is r > 0.",
        "Points on the circle lie exactly distance r from the center.",
        "A circle is symmetric about horizontal and vertical lines through its center.",
        "The diameter is twice the radius; circumference is 2πr; area is πr^2.",
    ],
}

GEOMETRY_TOPIC_TITLES: Dict[str, str] = {
    "quadratic_parabola": "Quadratic / Parabola (e.g., y = x^2)",
    "absolute_value": "Absolute Value (e.g., y = |x|)",
    "linear": "Linear Function (y = mx + b)",
    "circle": "Circle Geometry",
}


def route_geometry_topic(problem: str, student_text: str, fallback: str = "quadratic_parabola") -> str:
    text = f"{problem} {student_text}".lower()
    if any(k in text for k in ["x^2", "parabola", "quadratic", "vertex", "axis of symmetry"]):
        return "quadratic_parabola"
    if any(k in text for k in ["|x|", "absolute value", "v-shaped"]):
        return "absolute_value"
    if any(k in text for k in ["slope", "linear", "y = mx + b", "straight line"]):
        return "linear"
    if any(k in text for k in ["circle", "radius", "center", "(x-h)^2", "r^2", "circumference"]):
        return "circle"
    return fallback


def build_geometry_context(topic_key: str, include_global: bool = True, max_refs: int = 12) -> str:
    references: List[str] = []
    if include_global:
        references.extend(GEOMETRY_KB.get("global", []))
    references.extend(GEOMETRY_KB.get(topic_key, []))
    if len(references) > max_refs:
        references = references[:max_refs]
    return "\n".join(f"- {line}" for line in references)


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
