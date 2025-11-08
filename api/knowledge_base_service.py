import copy
import json
from typing import Any, Dict, Optional

from django.db import transaction
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .models import KnowledgeBaseEntry

load_dotenv()

DEFAULT_KB_TITLE = "Adaptive Knowledge Base"
KB_GENERATOR_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
KB_AUDITOR_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
MAX_GENERATION_ATTEMPTS = 3


def _debug(message: str) -> None:
    try:
        print(f"[KnowledgeBase] {message}")
    except Exception:
        pass


class FewShotExample(BaseModel):
    input: str = Field(..., min_length=8, description="Example scenario or learner statement.")
    analysis: str = Field(
        ...,
        min_length=12,
        description="Detailed analysis or coaching response in bilingual-friendly tone.",
    )


class FewShotSet(BaseModel):
    facts: list[FewShotExample] = Field(..., min_length=2)
    strategies: list[FewShotExample] = Field(..., min_length=2)
    procedures: list[FewShotExample] = Field(..., min_length=2)
    rationales: list[FewShotExample] = Field(..., min_length=2)
    tutor: list[FewShotExample] = Field(..., min_length=2)


class KnowledgeBasePayload(BaseModel):
    title: str = Field(..., min_length=10)
    global_highlights: list[str] = Field(..., min_length=8)
    rag_snippets: list[str] = Field(..., min_length=8)
    few_shot_examples: FewShotSet
    cot_checklist: list[str] = Field(..., min_length=5)

KNOWLEDGE_BASE_PROMPT = PromptTemplate.from_template(
    """
You are an interdisciplinary curriculum architect generating a reusable knowledge base for a tutoring agent.

Focus domain  : {domain}
Focus branch  : {branch}
Learner intent: {preference_text}

Populate EVERY field defined in the provided schema with precise, multi-sentence content.
Blend English terminology with succinct Chinese explanations where it aids clarity.
Avoid placeholders such as "TBD" or "示例缺失".
"""
)


KB_GENERATOR_STRUCTURED = KNOWLEDGE_BASE_PROMPT | KB_GENERATOR_LLM.with_structured_output(KnowledgeBasePayload)


KNOWLEDGE_BASE_AUDIT_PROMPT = PromptTemplate.from_template(
    """
You are a strict reviewer for knowledge base JSON used in an adaptive tutor.

Evaluate the following JSON for completeness, specificity, and absence of placeholders.
Return strict JSON with keys:
{
  "status": "ok" or "regenerate",
  "issues": ["issue1", ...],
  "recommendation": "one sentence summary"
}

Criteria for "regenerate":
- Title is generic or missing.
- global_highlights fewer than 5 concrete items.
- rag_snippets fewer than 5 multi-sentence references.
- Any few_shot_examples entry contains placeholder text like "示例缺失" or "暂未生成".
- cot_checklist fewer than 5 steps or contains placeholders.

Knowledge Base JSON:
{kb_json}
"""
)


def _safe_parse_json(response_text: str) -> Optional[Dict[str, Any]]:
    text = response_text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
        if not isinstance(parsed, dict):
            return None
        return parsed
    except json.JSONDecodeError:
        return None


def _ensure_structure(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    empty_example = {"input": "示例缺失", "analysis": "暂未生成详细解析。"}
    default = {
        "title": DEFAULT_KB_TITLE,
        "global_highlights": [],
        "rag_snippets": [],
        "few_shot_examples": {
            "facts": [empty_example],
            "strategies": [empty_example],
            "procedures": [empty_example],
            "rationales": [empty_example],
            "tutor": [empty_example],
        },
        "cot_checklist": [
            "Clarify the learner's goal and known information.",
            "Map relevant core concepts from the knowledge base.",
            "Plan reasoning steps before calculating or explaining.",
            "Validate each claim against canonical references.",
            "Summarize actionable next steps tailored to the learner.",
        ],
    }
    if not isinstance(payload, dict):
        return default
    result = copy.deepcopy(default)
    result["title"] = payload.get("title") or default["title"]
    result["global_highlights"] = payload.get("global_highlights") or default["global_highlights"]
    result["rag_snippets"] = payload.get("rag_snippets") or default["rag_snippets"]
    few_shots = payload.get("few_shot_examples") or {}
    fs_result = {}
    for key in default["few_shot_examples"]:
        items = few_shots.get(key)
        if not isinstance(items, list) or not items:
            fs_result[key] = default["few_shot_examples"][key]
        else:
            normalized = []
            for entry in items:
                if isinstance(entry, dict):
                    normalized.append(
                        {
                            "input": entry.get("input", "示例缺失"),
                            "analysis": entry.get("analysis", "暂缺解释"),
                        }
                    )
                else:
                    normalized.append({"input": str(entry), "analysis": "暂缺解释"})
            fs_result[key] = normalized
    result["few_shot_examples"] = fs_result
    result["cot_checklist"] = payload.get("cot_checklist") or default["cot_checklist"]
    return result


def generate_knowledge_base_content(domain: str, branch: str, preference_text: str) -> Dict[str, Any]:
    _debug(f"Generating KB for {domain}:{branch} (preference='{(preference_text or '')[:80]}...').")
    structured_payload = KB_GENERATOR_STRUCTURED.invoke(
        {
            "domain": domain,
            "branch": branch,
            "preference_text": preference_text or "N/A",
        }
    )
    return structured_payload.dict()


def audit_knowledge_base_content(content: Dict[str, Any]) -> Dict[str, Any]:
    kb_json = json.dumps(content or {}, ensure_ascii=False)
    try:
        chain = LLMChain(
            llm=KB_AUDITOR_LLM,
            prompt=KNOWLEDGE_BASE_AUDIT_PROMPT,
        )
        raw_output = chain.run(kb_json=kb_json)
        parsed = _safe_parse_json(raw_output)
        if parsed:
            _debug(f"Audit status: {parsed.get('status')} | issues: {parsed.get('issues')}")
            return parsed
    except Exception as exc:
        return {
            "status": "error",
            "issues": [f"Audit failed: {exc}"],
            "recommendation": "Manual review required.",
        }
    return {
        "status": "error",
        "issues": ["Audit returned non-JSON output."],
        "recommendation": "Manual review required.",
    }


def needs_regeneration(content: Dict[str, Any], audit_report: Dict[str, Any]) -> bool:
    if audit_report.get("status") == "regenerate":
        _debug("Audit requested regeneration explicitly.")
        return True
    placeholders = {"示例缺失", "暂未生成详细解析。", "暂缺解释"}
    few_shots = (content or {}).get("few_shot_examples") or {}
    for examples in few_shots.values():
        for entry in examples or []:
            if entry.get("input") in placeholders or entry.get("analysis") in placeholders:
                _debug("Detected placeholder values inside few_shot_examples.")
                return True
    if not (content or {}).get("global_highlights"):
        _debug("Missing global_highlights; will regenerate.")
        return True
    if not (content or {}).get("rag_snippets"):
        _debug("Missing rag_snippets; will regenerate.")
        return True
    return False


def generate_validated_content(domain_key: str, branch_key: str, preference_text: str) -> Dict[str, Any]:
    last_content = _ensure_structure(None)
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            content = generate_knowledge_base_content(domain_key, branch_key, preference_text)
        except Exception as exc:
            print(f"[KnowledgeBase] Generation attempt {attempt} failed for {domain_key}:{branch_key}: {exc}")
            content = _ensure_structure(None)
        report = audit_knowledge_base_content(content)
        if not needs_regeneration(content, report):
            _debug(f"Generation attempt {attempt} passed audit.")
            return content
        _debug(
            f"Generation attempt {attempt} for {domain_key}:{branch_key} did not pass audit; "
            f"issues: {report.get('issues')}"
        )
        last_content = content
    _debug(
        f"All {MAX_GENERATION_ATTEMPTS} attempts failed audit for {domain_key}:{branch_key}; "
        "returning last generated content."
    )
    return last_content


def refresh_branch_kb(domain: str, branch: str, preference_text: str = "") -> KnowledgeBaseEntry:
    domain_key = (domain or "general-learning").lower()
    branch_key = (branch or "exploratory").lower()
    content = generate_validated_content(domain_key, branch_key, preference_text)

    with transaction.atomic():
        entry, _created = KnowledgeBaseEntry.objects.update_or_create(
            domain=domain_key,
            branch=branch_key,
            defaults={
                "title": content.get("title", DEFAULT_KB_TITLE),
                "llm_version": "gpt-4.1-2025-04-14",
                "content": content,
            },
        )
        _debug(f"Stored refreshed KB for {entry.domain}:{entry.branch} (title='{entry.title}').")
        return entry


def get_or_create_branch_kb(domain: str, branch: str, preference_text: str = "") -> KnowledgeBaseEntry:
    domain_key = (domain or "general-learning").lower()
    branch_key = (branch or "exploratory").lower()
    _debug(f"Requesting KB for {domain_key}:{branch_key}.")
    try:
        entry = KnowledgeBaseEntry.objects.get(domain=domain_key, branch=branch_key)
        _debug("KB found in database; returning cached version.")
        return entry
    except KnowledgeBaseEntry.DoesNotExist:
        _debug("KB not found; generating new entry.")

    content = generate_validated_content(domain_key, branch_key, preference_text)

    with transaction.atomic():
        entry, _ = KnowledgeBaseEntry.objects.get_or_create(
            domain=domain_key,
            branch=branch_key,
            defaults={
                "title": content.get("title", DEFAULT_KB_TITLE),
                "llm_version": "gpt-4.1-2025-04-14",
                "content": content,
            },
        )
        return entry
