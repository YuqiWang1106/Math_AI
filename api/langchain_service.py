import json
import os
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from .prompts import (
    FACTS_PROMPT,
    STRATEGIES_PROMPT,
    PROCEDURES_PROMPT,
    RATIONALES_PROMPT,
    TUTOR_PROMPT,
    SUBJECT_CLASSIFIER_PROMPT,
    PREFERENCE_CLASSIFIER_PROMPT,
)
from .priority_report import compute_full_priority_from_report
from .arithmetic_module import ArithmeticSubjectModule
from .geometry_module import GeometrySubjectModule
from .knowledge_hub import build_reasoning_support, enrich_student_text
from .knowledge_base_service import get_or_create_branch_kb


load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_MODEL = os.getenv("GOOGLE_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


PRIMARY_EVALUATOR_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
SUBJECT_CLASSIFIER_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
PRIMARY_CHAT_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
BACKUP_CHAT_LLM = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0)
GEOMETRY_EVALUATOR_LLM = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0)
PREFERENCE_CLASSIFIER_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)


_PREFERENCE_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "mathematics": {
        "algebra": ["algebra", "equation", "linear", "quadratic", "polynomial", "slope"],
        "geometry": ["geometry", "triangle", "circle", "angle", "coordinate", "diagram"],
        "arithmetic": ["arithmetic", "fraction", "percent", "ratio", "addition", "subtraction"],
        "calculus": ["calculus", "derivative", "integral", "limit"],
        "statistics": ["statistics", "probability", "data", "distribution", "mean", "median"],
    },
    "science": {
        "physics": ["physics", "force", "motion", "mechanics", "velocity"],
        "chemistry": ["chemistry", "reaction", "molecule", "atom", "compound"],
        "biology": ["biology", "cell", "genetics", "organism"],
        "earth_science": ["geology", "earth", "climate", "weather", "planet"],
    },
    "engineering": {
        "mechanical": ["mechanical", "machine", "dynamics"],
        "electrical": ["electrical", "circuit", "voltage", "signal"],
        "computer": ["computer engineering", "embedded", "hardware"],
    },
    "finance": {
        "budgeting": ["budget", "expense", "savings", "cost"],
        "personal_finance": ["personal finance", "debt", "loan", "credit"],
        "investing": ["investment", "portfolio", "stocks", "returns"],
    },
    "humanities": {
        "history": ["history", "historical", "ancient", "renaissance"],
        "philosophy": ["philosophy", "ethics", "logic"],
        "literature": ["literature", "novel", "poetry"],
    },
    "wellness": {
        "mental_health": ["mental health", "stress", "anxiety", "mindfulness"],
        "physical_health": ["exercise", "fitness", "workout"],
        "nutrition": ["nutrition", "diet", "meal plan"],
    },
    "general-learning": {
        "career_planning": ["career", "job", "interview"],
        "goal_setting": ["goal", "plan", "roadmap"],
        "study_skills": ["study skills", "productivity", "focus"],
    },
}


def _safe_parse_preference_json(response_text: str) -> Optional[Dict[str, Any]]:
    text = response_text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _fallback_preference_classification(preference_text: str) -> Dict[str, Any]:
    lowered = preference_text.lower()
    for domain, topics in _PREFERENCE_KEYWORDS.items():
        for branch, keywords in topics.items():
            if any(keyword in lowered for keyword in keywords):
                return {
                    "domain": domain,
                    "branch": branch,
                    "confidence": 0.5,
                    "reasoning": f"Keyword match for '{branch}' in {domain}.",
                }
    return {
        "domain": "general-learning",
        "branch": "exploratory",
        "confidence": 0.25,
        "reasoning": "Default fallback classification.",
    }


def classify_preference_query(preference_text: str) -> Dict[str, Any]:
    if not preference_text:
        base = _fallback_preference_classification("")
        entry = get_or_create_branch_kb(base["domain"], base["branch"], preference_text)
        base["knowledge_base_id"] = entry.id
        base["knowledge_base_title"] = entry.title
        return base
    base_result = _fallback_preference_classification(preference_text)
    result = base_result.copy()
    try:
        chain = LLMChain(
            llm=PREFERENCE_CLASSIFIER_LLM,
            prompt=PromptTemplate.from_template(
                PREFERENCE_CLASSIFIER_PROMPT,
                template_format="jinja2",
            ),
        )
        raw_output = chain.run(preference_text=preference_text)
        parsed = _safe_parse_preference_json(raw_output)
        if parsed and parsed.get("domain"):
            result = {
                "domain": parsed.get("domain", base_result["domain"]).lower(),
                "branch": parsed.get("branch", base_result["branch"]).lower(),
                "confidence": float(parsed.get("confidence", base_result["confidence"])),
                "reasoning": parsed.get("reasoning", base_result["reasoning"]),
            }
    except Exception as exc:
        print(f"[PreferenceClassifier] LLM classification failed: {exc}")
    try:
        entry = get_or_create_branch_kb(result["domain"], result["branch"], preference_text)
        result["knowledge_base_id"] = entry.id
        result["knowledge_base_title"] = entry.title
    except Exception as exc:
        print(f"[PreferenceClassifier] Knowledge base ensure failed: {exc}")
    return result


def create_self_assessment_text(assessment: Dict[str, Any]) -> str:
    """Convert a structured self-assessment payload into plain text for evaluation."""
    sa = assessment.get("self_assessment", {})
    se = assessment.get("self_evaluation", {})
    text = ""

    problem = sa.get("problem", "")
    if problem:
        text += f"Example Problem: {problem}\n\n"

    for kt in sa.get("knowledge_types", []):
        k_type = kt.get("type", "Unknown").capitalize()
        text += f"{k_type}:\n"

        examples = kt.get("examples", {})
        if isinstance(examples, dict):
            for key, value in examples.items():
                text += f"  - {key}: {value}\n"
        elif isinstance(examples, str):
            text += f"  - Example: {examples}\n"

        uncertainties = kt.get("uncertainties", "")
        if uncertainties:
            text += f"  - Uncertainties: {uncertainties}\n"
        text += "\n"

    text += "Self-Evaluation:\n"
    for key, value in se.items():
        text += f"  - {key.capitalize()}: {value}\n"

    return text.strip()


class BaseSubjectModule:
    """Abstract interface for a math subject module."""

    subject_name: str

    def evaluate(self, student_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def ask(self, state: Dict[str, Any], assessment_data: Dict[str, Any], question: str) -> str:
        raise NotImplementedError


class PlaceholderSubjectModule(BaseSubjectModule):
    """Temporary module that signals pending implementation."""

    def __init__(self, subject_name: str):
        self.subject_name = subject_name

    def evaluate(self, student_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError(
            f"{self.subject_name.capitalize()} evaluation module is not yet implemented."
        )

    def ask(self, state: Dict[str, Any], assessment_data: Dict[str, Any], question: str) -> str:
        raise NotImplementedError(
            f"{self.subject_name.capitalize()} tutor module is not yet implemented."
        )


class AlgebraSubjectModule(BaseSubjectModule):
    """Algebra-specific evaluation and tutoring pipeline."""

    def __init__(
        self,
        evaluator_llm: ChatOpenAI,
        primary_chat_llm: ChatOpenAI,
        backup_chat_llm: ChatGoogleGenerativeAI,
    ):
        self.subject_name = "algebra"
        self._evaluator_llm = evaluator_llm
        self._primary_chat_llm = primary_chat_llm
        self._backup_chat_llm = backup_chat_llm
        self._dimension_prompts = {
            "Facts": FACTS_PROMPT,
            "Strategies": STRATEGIES_PROMPT,
            "Procedures": PROCEDURES_PROMPT,
            "Rationales": RATIONALES_PROMPT,
        }

    @staticmethod
    def _extract_public_response(text: str) -> str:
        if not text:
            return ""
        start_tag = "<final>"
        end_tag = "</final>"
        start = text.find(start_tag)
        end = text.find(end_tag, start + len(start_tag)) if start != -1 else -1
        if start != -1 and end != -1:
            return text[start + len(start_tag):end].strip()
        return text.strip()

    def evaluate(self, student_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        student_text = create_self_assessment_text(assessment_data)
        results = []
        structured_dimensions: Dict[str, Dict[str, Any]] = {}

        preference_meta = assessment_data.get("preference_meta")
        for name, prompt_template in self._dimension_prompts.items():
            chain = LLMChain(
                llm=self._evaluator_llm,
                prompt=PromptTemplate.from_template(prompt_template, template_format="jinja2"),
            )
            support_block = build_reasoning_support(
                "algebra",
                name,
                student_text,
                preference_meta=preference_meta,
            )
            enriched_student_text = enrich_student_text(student_text, support_block)
            output = chain.run(student_text=enriched_student_text)
            print(f"--- {name} Chain Result ---\n{output}\n")
            final_output = self._extract_public_response(output)
            print(f"--- {name} Dimension Result ---\n{final_output}\n")
            results.append(f"--- {name} Dimension ---\n{final_output}\n")
            parsed_dimension = self._parse_dimension_output(name, final_output)
            if parsed_dimension:
                structured_dimensions[name] = parsed_dimension

        evaluation_report = "\n\n".join(results)
        priority_result = compute_full_priority_from_report(structured_dimensions)
        self._log_priority(priority_result)
        return {
            "report": evaluation_report,
            "student_text": student_text,
            "priority": priority_result,
            "structured_report": structured_dimensions,
        }

    def ask(self, state: Dict[str, Any], assessment_data: Dict[str, Any], question: str) -> str:
        agent, first_time = self._ensure_chat_agent(state, assessment_data, question)

        def _run(agent_chain: ConversationChain, user_text: str) -> str:
            return agent_chain.run(user_text).strip()

        try:
            if first_time:
                return _run(agent, "")
            return _run(agent, question)
        except Exception as primary_error:
            try:
                agent.llm = self._backup_chat_llm
                state["backend"] = "gemini"
                if first_time:
                    return _run(agent, "")
                return _run(agent, question)
            except Exception:
                state["backend"] = "gpt"
                raise primary_error

    def _ensure_chat_agent(
        self,
        state: Dict[str, Any],
        assessment_data: Dict[str, Any],
        first_question: str,
    ) -> Tuple[ConversationChain, bool]:
        existing_agent: Optional[ConversationChain] = state.get("agent")
        if existing_agent:
            return existing_agent, False

        system_prompt = TUTOR_PROMPT.format(
            prior_summary=state["evaluation"],
            raw_json=state["raw_json_str"],
        )
        tutor_support = build_reasoning_support(
            "algebra",
            "Tutor",
            state.get("student_text", ""),
            preference_meta=state.get("assessment_data", {}).get("preference_meta"),
        )
        system_prompt = f"{system_prompt}\n\n{tutor_support}\n\nUse the knowledge base, exemplars, and checklist above before crafting each 2-3 sentence reply."

        memory = ConversationBufferMemory(return_messages=True)
        memory.chat_memory.add_message({"role": "system", "content": system_prompt})
        memory.chat_memory.add_message({"role": "user", "content": first_question})

        chat_chain = ConversationChain(llm=self._primary_chat_llm, memory=memory)
        state["agent"] = chat_chain
        state["backend"] = "gpt"
        return chat_chain, True

    @staticmethod
    def _parse_dimension_output(name: str, text: str) -> Optional[Dict[str, Any]]:
        """Parse the formatted dimension text into a structured dict."""
        if not text:
            return None
        title = None
        aspects: List[Dict[str, Any]] = []
        gap = None
        current: Optional[Dict[str, Any]] = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("Title:"):
                title = line.split(":", 1)[1].strip() or title
                continue
            if line.startswith("- Aspect:"):
                aspect_name = line.split(":", 1)[1].strip()
                current = {"aspect": aspect_name, "labels": [], "explanation": ""}
                aspects.append(current)
                continue
            if line.startswith("Labels:"):
                labels_str = line.split(":", 1)[1].strip()
                labels_str = labels_str.strip("[]")
                if current is not None:
                    labels = [label.strip() for label in labels_str.split(",") if label.strip()]
                    current["labels"] = labels
                continue
            if line.startswith("Explanation:"):
                explanation = line.split(":", 1)[1].strip()
                if current is not None:
                    current["explanation"] = explanation
                continue
            if line.lower().startswith("most critical"):
                gap = line.split(":", 1)[1].strip()
                continue
            if current is not None:
                existing = current.get("explanation", "")
                current["explanation"] = (existing + " " + line).strip()

        if not aspects:
            return None
        return {
            "title": title or f"{name} Dimension",
            "aspects": aspects,
            "most_critical_gap": gap or "",
        }

    @staticmethod
    def _log_priority(priority_result: Dict[str, Any]) -> None:
        """Print algebra priority summary for verification."""
        if not isinstance(priority_result, dict):
            print("[Priority] 未能计算出代数维度的优先级结果。")
            return
        top_dim = priority_result.get("top_dimension")
        top_label = priority_result.get("top_label_in_top_dimension")
        print("[Priority] ===== PRIORITY CHECK =====")
        print(f"[Priority] Top dimension: {top_dim}")
        print(f"[Priority] Top label in top dimension: {top_label}")


class MathAgentOrchestrator:
    """Coordinates subject detection and delegates to the appropriate subject module."""

    def __init__(self, modules: Dict[str, Any], classifier_llm: ChatOpenAI):
        self._modules = modules
        self._classifier_llm = classifier_llm
        self._student_states: Dict[str, Dict[str, Any]] = {}

    def evaluate(self, student_id: str, assessment_data: Dict[str, Any]) -> str:
        subject = self._determine_subject(assessment_data)
        module = self._modules[subject]
        evaluation_payload = module.evaluate(student_id, assessment_data)

        self._student_states[student_id] = {
            "subject": subject,
            "evaluation": evaluation_payload["report"],
            "student_text": evaluation_payload.get("student_text", ""),
            "raw_json_str": str(assessment_data),
            "assessment_data": assessment_data,
            "priority": evaluation_payload.get("priority"),
            "structured_report": evaluation_payload.get("structured_report"),
            "agent": None,
            "backend": None,
        }

        return evaluation_payload["report"]

    def ask(self, student_id: str, assessment_data: Dict[str, Any], question: str) -> str:
        state = self._student_states.get(student_id)
        raw_json_str = str(assessment_data)
        if state and state.get("raw_json_str") == raw_json_str:
            subject = state["subject"]
        else:
            subject = self._determine_subject(assessment_data)

        if state is None or state.get("subject") != subject:
            # Fresh student or subject changed: run evaluation anew.
            evaluation_report = self.evaluate(student_id, assessment_data)
            state = self._student_states[student_id]
            state["evaluation"] = evaluation_report

        module = self._modules[subject]
        state["assessment_data"] = assessment_data
        state["raw_json_str"] = raw_json_str
        return module.ask(state, assessment_data, question)

    def _determine_subject(self, assessment_data: Dict[str, Any]) -> str:
        """Determine subject via LLM classifier with heuristic fallback."""
        subject = self._classify_subject_with_llm(assessment_data)
        if subject:
            print(f"[SubjectClassifier] LLM classified subject as '{subject}'.")
            return subject
        subject = self._fallback_subject(assessment_data)
        print(f"[SubjectClassifier] Fallback classified subject as '{subject}'.")
        return subject

    def _classify_subject_with_llm(self, assessment_data: Dict[str, Any]) -> Optional[str]:
        """Use an LLM to classify the subject; return None if classification fails."""
        try:
            student_text = create_self_assessment_text(assessment_data)
            chain = LLMChain(
                llm=self._classifier_llm,
                prompt=PromptTemplate.from_template(
                    SUBJECT_CLASSIFIER_PROMPT,
                    template_format="jinja2",
                ),
            )
            raw_response = chain.run(student_text=student_text)
            if not raw_response:
                return None
            normalized = raw_response.strip().lower()
            token = normalized.split()[0].strip(",.?!")
            if token in self._modules:
                return token
        except Exception:
            return None
        return None

    def _fallback_subject(self, assessment_data: Dict[str, Any]) -> str:
        """Keyword heuristic used if the LLM classifier is unavailable."""
        problem = ""
        self_assessment = assessment_data.get("self_assessment", {})
        if isinstance(self_assessment, dict):
            problem = self_assessment.get("problem", "") or ""

        lowered = problem.lower()

        geometry_keywords = ["triangle", "angle", "polygon", "circle", "area", "perimeter"]
        arithmetic_keywords = ["fraction", "decimal", "integer", "percent", "ratio"]

        if any(keyword in lowered for keyword in geometry_keywords):
            return "geometry"
        if any(keyword in lowered for keyword in arithmetic_keywords):
            return "arithmetic"

        return "algebra"


_ORCHESTRATOR = MathAgentOrchestrator(
    modules={
        "algebra": AlgebraSubjectModule(
            PRIMARY_EVALUATOR_LLM,
            PRIMARY_CHAT_LLM,
            BACKUP_CHAT_LLM,
        ),
        "arithmetic": ArithmeticSubjectModule(
            PRIMARY_EVALUATOR_LLM,
            PRIMARY_CHAT_LLM,
            BACKUP_CHAT_LLM,
            create_self_assessment_text,
        ),
        "geometry": GeometrySubjectModule(
            GEOMETRY_EVALUATOR_LLM,
            PRIMARY_CHAT_LLM,
            BACKUP_CHAT_LLM,
            create_self_assessment_text,
        ),
    },
    classifier_llm=SUBJECT_CLASSIFIER_LLM,
)


def evaluate_assessment(student_id: str, assessment_data: Dict[str, Any]) -> str:
    """Evaluate a student's self-assessment by routing to the correct subject module."""
    return _ORCHESTRATOR.evaluate(student_id, assessment_data)


def ask_with_memory(student_id: str, assessment_data: Dict[str, Any], question: str) -> str:
    """Answer a student's question using the previously selected subject tutor."""
    return _ORCHESTRATOR.ask(student_id, assessment_data, question)
