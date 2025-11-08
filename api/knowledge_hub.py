import re
from typing import Dict, List, Optional

# High-level knowledge snippets that stay constant per subject.
SUBJECT_GLOBAL_CONTEXT: Dict[str, List[str]] = {
    "algebra": [
        "Use inverse operations in reverse order (undo addition/subtraction before multiplication/division) when solving ax + b = c.",
        "Fact accuracy anchors the other dimensions: mislabeling coefficients or variables cascades into flawed strategies and procedures.",
        "Procedures should cite the property of equality or structure that justifies each manipulation (e.g., distributive property, zero-product property).",
        "Graph-based reasoning (slope, intercepts, symmetry) can validate symbolic steps and reveal misconceptions.",
        "Confidence grows when students verify solutions by substitution and narrate why each move is legitimate.",
    ],
    "geometry": [
        "Always attach a diagram-based justification: mention coordinates, measures, or congruence criteria explicitly.",
        "Similarity and congruence arguments require matching ratios or angle equalities; name the postulate you rely on.",
        "Coordinate geometry frequently leverages distance, midpoint, and slope formulas—tie them to the actual points.",
        "Transformations (translation/rotation/reflection/dilation) preserve specific invariants; mention which stay fixed.",
        "Precision vocabulary (vertex, axis of symmetry, center, radius, intercept) matters as much as numeric computation.",
    ],
    "arithmetic": [
        "Facts must capture given quantities, units, and conversions before any computation begins.",
        "Strategies describe the global plan (e.g., estimate, work with equivalent fractions, isolate a unit rate) prior to arithmetic steps.",
        "Procedures execute operations with attention to place value, common denominators, and sign handling.",
        "Rationales connect the plan to properties (e.g., why regrouping works, why dividing both numbers in a ratio by the same factor keeps it equivalent).",
        "Checking reasonableness with estimation or inverse operations prevents cascading calculation errors.",
    ],
}

# Lightweight corpus used for retrieval-augmented prompting.
RAG_CORPUS: Dict[str, List[str]] = {
    "algebra": [
        "Linear equations: isolate the variable step-by-step, citing additive then multiplicative inverses; verify with substitution.",
        "Fact vs strategy: correctly naming slope, intercepts, or variable roles prevents applying an irrelevant strategy.",
        "Procedures with negative coefficients must keep track of sign flips when dividing by negatives.",
        "Rationales often cite the distributive property, properties of equality, or function structure such as vertex form.",
    ],
    "geometry": [
        "Quadratic/parabola graphs: vertex (h,k), axis of symmetry x = h, opens based on the sign of a, domain all real numbers, range depending on vertex.",
        "Triangles: similarity (AA, SAS~, SSS~) vs congruence (SSS, SAS, ASA, AAS, HL) distinctions drive the correct reasoning path.",
        "Circles: (x-h)^2 + (y-k)^2 = r^2 ties every point to the center; diameter, circumference, and area formulas depend on r.",
        "Transformations: translations/rotations/reflections preserve distance; dilations scale distances by the same factor from a center.",
    ],
    "arithmetic": [
        "Fractions/decimals/percents conversions allow comparison; remember 3/4 = 0.75 = 75%.",
        "Unit rate strategy: divide total by count to find per-unit comparisons before scaling back up.",
        "Long division and repeated subtraction are equivalent procedures; cite which you choose and why.",
        "Rationales mention properties like distributive, associative, or why you align place values.",
    ],
}

# Few-shot exemplars per subject/dimension.
FEW_SHOT_EXAMPLES: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "algebra": {
        "Facts": [
            {
                "input": "Student listed variables but forgot to name coefficients.",
                "analysis": "They correctly stated x is the unknown (Know-Know) but omitted the role of 2 as a coefficient (Omission).",
            },
            {
                "input": "Student said slope is 'how curvy the line is'.",
                "analysis": "Label this False Knowledge; explain slope measures constant rate of change, not curvature.",
            },
        ],
        "Strategies": [
            {
                "input": "Student plans to factor before isolating terms in a linear equation.",
                "analysis": "Flag as Irrelevant Knowledge; factoring targets polynomials, not simple linear isolation.",
            }
        ],
        "Procedures": [
            {
                "input": "Student uses additive inverse then divides by negative coefficient but keeps sign.",
                "analysis": "Mark the division step as False Knowledge and remind them dividing by a negative flips the sign.",
            }
        ],
        "Rationales": [
            {
                "input": "Student cites 'because that's how you do it' for distributive property.",
                "analysis": "Label as Know-Don't Know; coach them to mention that a(b + c) = ab + ac preserves equality.",
            }
        ],
        "Tutor": [
            {
                "input": "Learner mislabels intercepts but understands inverse operations.",
                "analysis": "Start by validating their inverse-operation plan, then guide them to identify intercepts via substitution.",
            }
        ],
    },
    "geometry": {
        "Facts": [
            {
                "input": "Student says the circle's center is (r, r).",
                "analysis": "Explain why center is (h,k) from (x-h)^2 + (y-k)^2 = r^2 and mark statement False Knowledge.",
            }
        ],
        "Strategies": [
            {
                "input": "Student wants to compare triangles by eyeballing.",
                "analysis": "Guide them toward a similarity or congruence test (AA, SAS, etc.) and label omission.",
            }
        ],
        "Procedures": [
            {
                "input": "Student forgets to square root distance squared.",
                "analysis": "Flag as False Knowledge; remind them distance formula requires the final sqrt.",
            }
        ],
        "Rationales": [
            {
                "input": "Student notes a rotation preserves length but not orientation.",
                "analysis": "Mark Know-Know and connect to rigid motion rationale.",
            }
        ],
        "Tutor": [
            {
                "input": "Learner confuses similarity with congruence.",
                "analysis": "Prompt them to compare side ratios and angles, reinforcing definitions before giving hints.",
            }
        ],
    },
    "arithmetic": {
        "Facts": [
            {
                "input": "Student lists only one price in a comparison problem.",
                "analysis": "Label as Omission and remind them to capture both costs plus units.",
            }
        ],
        "Strategies": [
            {
                "input": "Student plans to subtract percentages when comparing discounts.",
                "analysis": "Mark as False Knowledge; suggest converting both discounts to dollar amounts or equivalent rates.",
            }
        ],
        "Procedures": [
            {
                "input": "Student adds unlike fractions without LCM.",
                "analysis": "Explain the need for common denominators; label as False Knowledge.",
            }
        ],
        "Rationales": [
            {
                "input": "Student explains regrouping by 'borrowing magic'.",
                "analysis": "Reframe as Know-Don't Know and tie to conservation of value when decomposing place value.",
            }
        ],
        "Tutor": [
            {
                "input": "Learner nervous about word problems with mixed numbers.",
                "analysis": "Encourage translating to improper fractions, showing why it keeps value constant before operations.",
            }
        ],
    },
}

COT_CHECKLIST: Dict[str, List[str]] = {
    "algebra": [
        "Parse the student's claims dimension-by-dimension.",
        "Align each claim with knowledge base facts and retrieved evidence.",
        "Label with justification before producing the concise final answer.",
    ],
    "geometry": [
        "Identify which geometric objects or relationships the student references.",
        "Validate them against formulas/postulates from the knowledge base.",
        "State the critical misconception or next step before final output.",
    ],
    "arithmetic": [
        "List all given quantities/units and missing pieces.",
        "Connect strategies to procedures and rationales explicitly.",
        "Prioritize the single highest-leverage fix.",
    ],
    "default": [
        "Summarize evidence.",
        "Reason step-by-step.",
        "Only then present the final answer.",
    ],
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _score(snippet: str, query: str) -> float:
    query_tokens = set(_tokenize(query))
    snippet_tokens = set(_tokenize(snippet))
    if not query_tokens or not snippet_tokens:
        return 0.0
    overlap = len(query_tokens & snippet_tokens)
    return overlap / (len(query_tokens) + 1e-9)


def retrieve_kb_snippets(subject: str, query: str, top_k: int = 4) -> List[str]:
    corpus = RAG_CORPUS.get(subject, [])
    scored = sorted(
        corpus,
        key=lambda text: _score(text, query),
        reverse=True,
    )
    return scored[:top_k]


def _format_block(title: str, lines: List[str]) -> str:
    if not lines:
        return f"{title}:\n- (no data)"
    bullet_lines = "\n".join(f"- {line}" for line in lines if line.strip())
    return f"{title}:\n{bullet_lines}"


def format_few_shot_examples(subject: str, dimension: str, max_examples: int = 2) -> str:
    raw_examples = FEW_SHOT_EXAMPLES.get(subject, {}).get(dimension, [])
    chosen = raw_examples[:max_examples]
    if not chosen:
        return "- (no exemplars configured)"
    lines = []
    for idx, item in enumerate(chosen, start=1):
        lines.append(f"Example {idx}:")
        lines.append(f"  Input: {item['input']}")
        lines.append(f"  Reasoning: {item['analysis']}")
    return "\n".join(lines)


def _format_cot_checklist(subject: str) -> str:
    steps = COT_CHECKLIST.get(subject) or COT_CHECKLIST["default"]
    return "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))


def build_reasoning_support(
    subject: str,
    dimension: str,
    query: str,
    rag_context: Optional[str] = None,
) -> str:
    global_context = SUBJECT_GLOBAL_CONTEXT.get(subject, [])
    rag_hits = [rag_context.strip()] if rag_context and rag_context.strip() else []
    rag_hits.extend(retrieve_kb_snippets(subject, query, top_k=4))

    kb_block = _format_block("Knowledge Base Highlights", global_context)
    rag_block = _format_block("RAG Evidence", rag_hits)
    few_shot_block = format_few_shot_examples(subject, dimension, max_examples=2)
    cot_block = _format_cot_checklist(subject)

    return (
        f"{kb_block}\n\n"
        f"{rag_block}\n\n"
        "Few-Shot Exemplars:\n"
        f"{few_shot_block}\n\n"
        "Chain-of-Thought Checklist:\n"
        f"{cot_block}"
    )


def enrich_student_text(student_text: str, support_block: str) -> str:
    student_section = f"[STUDENT SELF-ASSESSMENT]\n{student_text.strip()}"
    support_section = f"[INTEGRATED PEDAGOGICAL SUPPORT]\n{support_block.strip()}"
    return f"{student_section}\n\n{support_section}"


__all__ = [
    "build_reasoning_support",
    "enrich_student_text",
]
