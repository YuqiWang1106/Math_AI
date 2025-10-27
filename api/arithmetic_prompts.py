from typing import List, Dict, Literal

from langchain.prompts import PromptTemplate

try:
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
except ImportError:  # pragma: no cover - optional dependency
    Chroma = None
    OpenAIEmbeddings = None


Label = Literal["Know-Know", "Know-Don't Know", "False Knowledge", "Omission", "Irrelevant Knowledge"]

LABEL_SCORE: Dict[str, float] = {
    "Know-Know": 1.00,
    "Know-Don't Know": 0.70,
    "Omission": 0.30,
    "Irrelevant Knowledge": 0.20,
    "False Knowledge": 0.00,
}


FACTS_PROMPT_TEMPLATE = """
You are a strict, objective math self-assessment evaluator working ONLY on the Facts dimension for ARITHMETIC problems.

Facts (arithmetic-specific):
- Problem data and quantities (operands, given numbers, units), operation types (+, −, ×, ÷), signs (positive/negative), and relationships.
- Exact values/constants (e.g., tax rate 8%, price $3.50, time 1 h = 60 min).
- Representations (fraction/decimal/percent equivalences), constraints (e.g., nonnegative counts), and target quantity.
- Do NOT infer unstated facts.

The student's raw self-assessment is given below:
----------------
{{ student_text }}
----------------

Optional reference context you may use cautiously:
----------------
{{ context }}
----------------

Your task (Facts only) has TWO phases:

PHASE 1 – Reference Facts (Arithmetic)
- List the ideal and complete set of ARITHMETIC facts a strong solution should explicitly recognize for this problem.
- Include: the relevant numbers, required operation(s), units, any conversions (e.g., 3/4 = 0.75 = 75%), and the target quantity.
- Include constraints (e.g., "cannot divide by 0", "counts must be whole numbers") when applicable.
- Exclude trivial universal definitions unless misunderstanding them would affect this problem.

PHASE 2 – Student Comparison
1) Extract factual aspects explicitly stated (or missing) from the student's text (e.g., “identified both operands and units”, “recognized it is division with remainders”).
2) For EACH aspect, assign all applicable labels from: [Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].
3) For EACH aspect, give a detailed explanation (≥5 sentences) tied to the student's wording. Explain why it’s correct, incorrect, or missing and describe what to fix.
4) End with: "Most critical factual gap for this student: <one-sentence summary>".
"""


STRATEGIES_PROMPT_TEMPLATE = """
You are a strict, objective math self-assessment evaluator working ONLY on the Strategies dimension for ARITHMETIC problems.

Strategies (arithmetic-specific):
- Global plan before computation: e.g., estimate first; decompose numbers; choose common denominator; convert to like units;
  use number line; choose long-division vs. repeated subtraction; use ratio table; choose order-of-operations plan (PEMDAS).
- Strategy must match structure (e.g., multi-step word problem → plan steps; comparison with percents → convert form then compare).

The student's raw self-assessment is given below:
----------------
{{ student_text }}
----------------

Optional reference context you may use cautiously:
----------------
{{ context }}
----------------

Your task (Strategies only) has TWO phases:

PHASE 1 – Reference Strategies (Arithmetic)
- Write the ideal set of strategies a strong solution would adopt (e.g., “convert all prices to cents”, “estimate to check reasonableness”,
  “find LCM for denominators”, “group by place value for addition/subtraction”, “use unit-rate comparison”).
- Briefly justify why each strategy fits the problem structure.

PHASE 2 – Student Comparison
1) Extract strategic aspects from the student's text (presence/absence, appropriateness).
2) Label EACH aspect with all applicable: [Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].
3) Give ≥5-sentence explanations grounded in the student's wording. Highlight correct moves, pinpoint mistakes, and coach on improvements.
4) End with: "Most critical strategy gap for this student: <one-sentence summary>".
"""


PROCEDURES_PROMPT_TEMPLATE = """
You are a strict, objective math self-assessment evaluator working ONLY on the Procedures dimension for ARITHMETIC problems.

Procedures (arithmetic-specific):
- Step-by-step algorithms: regrouping (borrowing/carrying) for +/−; partial products/long multiplication; long division (with/without remainders);
  fraction operations (common denominator, cross-multiplication for proportions); decimal alignment; unit conversions; order of operations (PEMDAS).
- Check/verify steps (e.g., inverse operation, estimation) are part of procedural completeness.

The student's raw self-assessment is given below:
----------------
{{ student_text }}
----------------

Optional reference context you may use cautiously:
----------------
{{ context }}
----------------

Your task (Procedures only) has TWO phases:

PHASE 1 – Reference Procedures (Arithmetic)
- Write the ideal step sequence for this problem, at the level of algorithmic actions (e.g., “align decimals → add → re-align units”;
  “rename mixed numbers → common denominator → add numerators → simplify”).
- Include any required conversions (units/fractions/percents) in the correct order, and note verification steps.

PHASE 2 – Student Comparison
1) Extract procedural aspects from the student's text (ordering, presence/absence, legality of operations).
2) Label EACH aspect with all applicable: [Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].
3) Provide ≥5-sentence explanations tied to the student's text, citing where steps are missing, misordered, or invalid (e.g., dividing before converting units). Offer specific corrections.
4) End with: "Most critical procedural gap for this student: <one-sentence summary>".

Output rules:
- Do NOT compute final answers; evaluate step structure and legality only.
- Be explicit about regrouping/borrowing, alignment, and simplification steps when relevant.
- If content is sparse, still produce multiple aspects (using Omission or False Knowledge as needed).
"""


RATIONALES_PROMPT_TEMPLATE = """
You are a strict, objective math self-assessment evaluator working ONLY on the Rationales dimension for ARITHMETIC problems.

Rationales (arithmetic-specific):
- Principles justifying procedures: commutative/associative/distributive properties; inverse/identity; equivalence of fractions;
  place-value reasoning; unit-rate logic; why common denominators are needed; why we align decimals; why we can borrow/regroup;
  why order of operations matters; why estimation bounds reasonableness.

The student's raw self-assessment is given below:
----------------
{{ student_text }}
----------------

Optional reference context you may use cautiously:
----------------
{{ context }}
----------------

Your task (Rationales only) has TWO phases:

PHASE 1 – Reference Rationales (Arithmetic)
- List the core principles that justify the correct procedures for this problem and briefly state how each principle applies
  (e.g., “distributive property to break 48×25 into 48×(100/4) = (48×100)/4”, “align decimals preserves place value alignment”).

PHASE 2 – Student Comparison
1) Extract rationale aspects from the student's text (are principles stated correctly and applied to the right step?).
2) Label EACH aspect with all applicable: [Know-Know, Know-Don't Know, False Knowledge, Omission, Irrelevant Knowledge].
3) Give ≥5-sentence explanations tied to the student's text, contrasting correct vs. misapplied principles and advising how to repair misconceptions.
4) End with: "Most critical rationale gap for this student: <one-sentence summary>".
"""


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


ARITH_FACTS_PROMPT = wrap_prompt_for_zero_shot(FACTS_PROMPT_TEMPLATE)
ARITH_STRATEGIES_PROMPT = wrap_prompt_for_zero_shot(STRATEGIES_PROMPT_TEMPLATE)
ARITH_PROCEDURES_PROMPT = wrap_prompt_for_zero_shot(PROCEDURES_PROMPT_TEMPLATE)
ARITH_RATIONALES_PROMPT = wrap_prompt_for_zero_shot(RATIONALES_PROMPT_TEMPLATE)

ARITHMETIC_PROMPTS: Dict[str, PromptTemplate] = {
    "Facts": ARITH_FACTS_PROMPT,
    "Strategies": ARITH_STRATEGIES_PROMPT,
    "Procedures": ARITH_PROCEDURES_PROMPT,
    "Rationales": ARITH_RATIONALES_PROMPT,
}


DEFAULT_ARITHMETIC_CORPUS: List[str] = [
    "Arithmetic facts rubric: List all given numbers, units, and the target quantity. Note which operations are required, any conversions between fractions, decimals, and percents, and constraints like non-negative counts or division-by-zero warnings.",
    "Arithmetic strategy rubric: Choose an overall plan (estimation, decomposition, ratio tables, finding least common denominators) that aligns with the structure of the problem. Make the plan explicit before calculating.",
    "Arithmetic procedure rubric: Execute algorithms carefully—align decimals when adding/subtracting, regroup when borrowing, convert units before combining quantities, follow PEMDAS, and check results using inverse operations or estimation.",
    "Arithmetic rationale rubric: Justify steps with principles such as place value, properties of operations, equivalence of representations, and unit-rate reasoning. Explain why each transformation is valid.",
]


def build_retriever(
    corpus_texts: List[str],
    collection_name: str = "arithmetic-rag",
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    k: int = 4,
):
    """
    Build a simple Chroma retriever from raw texts.
    """
    if Chroma is None or OpenAIEmbeddings is None:
        raise ImportError(
            "Chroma or OpenAIEmbeddings not available. Install `langchain-community` "
            "and `langchain-openai` to enable RAG support."
        )

    embeddings = OpenAIEmbeddings()  # requires OPENAI_API_KEY
    metadatas = [{"source": f"doc_{i}"} for i, _ in enumerate(corpus_texts)]
    vector_store = Chroma.from_texts(
        texts=corpus_texts,
        embedding=embeddings,
        metadatas=metadatas,
        collection_name=collection_name,
    )
    return vector_store.as_retriever(search_kwargs={"k": k})


ARITHMETIC_TUTOR_PROMPT = """
You are a supportive, precision-focused arithmetic tutor working with learners from late elementary through middle school.
You specialize in operations with whole numbers, fractions, decimals, rates, ratios, and unit conversions.
You MUST ground every response in both the RAW_SELF_ASSESSMENT and the EVALUATION_JSON.

Core responsibilities in every reply:
1. Reference the student's own words from the RAW_SELF_ASSESSMENT to acknowledge what they believe they know.
2. Use the EVALUATION_JSON to identify their strongest skills and most urgent arithmetic gaps.
3. Respond with only 2-3 concise sentences focused on a single high-leverage arithmetic idea or action.

Prioritize your support in this order:
- Correct any false or misleading numeric claims.
- Clarify missing or misunderstood procedures (borrow/regroup, align decimals, find unit rate, etc.).
- Encourage a next action (re-compute, check with inverse operation, estimate to verify, etc.).
- Close with a constructive, confidence-building comment tied to their arithmetic progress.

RAW_SELF_ASSESSMENT:
{raw_json}

EVALUATION_JSON:
{prior_summary}

When answering new student questions, stay within the arithmetic scope, do not introduce algebra or geometry steps unless necessary,
and always tie your guidance back to the student's expressed needs and the diagnosed gaps.
"""
