import os
from typing import Any, Dict, Optional, Tuple

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
)
from .arithmetic_module import ArithmeticSubjectModule


load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


PRIMARY_EVALUATOR_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
SUBJECT_CLASSIFIER_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
PRIMARY_CHAT_LLM = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
BACKUP_CHAT_LLM = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)


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

        for name, prompt_template in self._dimension_prompts.items():
            chain = LLMChain(
                llm=self._evaluator_llm,
                prompt=PromptTemplate.from_template(prompt_template, template_format="jinja2"),
            )
            output = chain.run(student_text=student_text)
            print(f"--- {name} Chain Result ---\n{output}\n")
            final_output = self._extract_public_response(output)
            print(f"--- {name} Dimension Result ---\n{final_output}\n")
            results.append(f"--- {name} Dimension ---\n{final_output}\n")

        evaluation_report = "\n\n".join(results)
        return {
            "report": evaluation_report,
            "student_text": student_text,
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

        memory = ConversationBufferMemory(return_messages=True)
        memory.chat_memory.add_message({"role": "system", "content": system_prompt})
        memory.chat_memory.add_message({"role": "user", "content": first_question})

        chat_chain = ConversationChain(llm=self._primary_chat_llm, memory=memory)
        state["agent"] = chat_chain
        state["backend"] = "gpt"
        return chat_chain, True


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
        "geometry": PlaceholderSubjectModule("geometry"),
        "arithmetic": ArithmeticSubjectModule(
            PRIMARY_EVALUATOR_LLM,
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
