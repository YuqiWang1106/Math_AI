import re
from typing import Any, Dict, List, Optional, Tuple

from .knowledge_base_service import get_or_create_branch_kb

DEFAULT_DOMAIN = "mathematics"
DEFAULT_BRANCH = "general_math"
DIMENSION_KEYS = ["facts", "strategies", "procedures", "rationales", "tutor"]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _score(snippet: str, query: str) -> float:
    query_tokens = set(_tokenize(query))
    snippet_tokens = set(_tokenize(snippet))
    if not query_tokens or not snippet_tokens:
        return 0.0
    overlap = len(query_tokens & snippet_tokens)
    return overlap / (len(query_tokens) + 1e-9)


def _derive_domain_branch(subject: str, preference_meta: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    domain = (preference_meta or {}).get("domain") or DEFAULT_DOMAIN
    branch = (preference_meta or {}).get("branch") or subject or DEFAULT_BRANCH
    return domain.lower(), branch.lower()


def _pick_relevant(snippets: List[str], query: str, top_k: int = 4) -> List[str]:
    if not snippets:
        return []
    scored = sorted(
        snippets,
        key=lambda text: _score(text, query),
        reverse=True,
    )
    return scored[:top_k]


def _format_block(title: str, lines: List[str]) -> str:
    if not lines:
        return f"{title}:\n- (no data)"
    bullet_lines = "\n".join(f"- {line}" for line in lines if line.strip())
    return f"{title}:\n{bullet_lines}"


def format_few_shot_examples(kb_content: Dict[str, Any], dimension: str, max_examples: int = 2) -> str:
    few_shots = (kb_content or {}).get("few_shot_examples") or {}
    raw_examples = few_shots.get(dimension.lower()) or few_shots.get(dimension.capitalize()) or []
    chosen = raw_examples[:max_examples]
    if not chosen:
        return "- (no exemplars configured)"
    lines = []
    for idx, item in enumerate(chosen, start=1):
        lines.append(f"Example {idx}:")
        lines.append(f"  Input: {item.get('input', 'N/A')}")
        lines.append(f"  Reasoning: {item.get('analysis', 'N/A')}")
    return "\n".join(lines)


def _format_cot_checklist(kb_content: Dict[str, Any]) -> str:
    steps = kb_content.get("cot_checklist", [])
    if not steps:
        steps = [
            "Clarify the student's goal.",
            "List relevant facts and strategies.",
            "Plan reasoning steps before responding.",
            "Validate each step with evidence.",
            "Summarize a focused, actionable nudge.",
        ]
    return "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))


def build_reasoning_support(
    subject: str,
    dimension: str,
    query: str,
    rag_context: Optional[str] = None,
    preference_meta: Optional[Dict[str, Any]] = None,
) -> str:
    domain, branch = _derive_domain_branch(subject, preference_meta)
    preference_text = (preference_meta or {}).get("preference", "")
    entry = get_or_create_branch_kb(domain, branch, preference_text)
    kb_content = entry.content or {}

    global_highlights = kb_content.get("global_highlights", [])
    rag_snippets = kb_content.get("rag_snippets", [])

    rag_hits: List[str] = []
    if rag_context and rag_context.strip():
        rag_hits.append(rag_context.strip())
    rag_hits.extend(_pick_relevant(rag_snippets, query, top_k=4))

    kb_block = _format_block("Knowledge Base Highlights", global_highlights)
    rag_block = _format_block("RAG Evidence", rag_hits)
    few_shot_block = format_few_shot_examples(kb_content, dimension, max_examples=2)
    cot_block = _format_cot_checklist(kb_content)

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
