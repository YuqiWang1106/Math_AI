import json
from typing import Any, Callable, Dict, Optional, Tuple

from langchain.chains import LLMChain, ConversationChain
from langchain.memory import ConversationBufferMemory

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from .arithmetic_prompts import (
    ARITHMETIC_PROMPTS,
    ARITHMETIC_TUTOR_PROMPT,
    DEFAULT_ARITHMETIC_CORPUS,
    build_retriever,
)
from .priority_report import compute_full_priority_from_report
from .knowledge_hub import build_reasoning_support


class ArithmeticSubjectModule:
    """Arithmetic-specific evaluation using RAG plus tutoring."""

    def __init__(
        self,
        evaluator_llm: ChatOpenAI,
        primary_chat_llm: ChatOpenAI,
        backup_chat_llm: ChatGoogleGenerativeAI,
        assessment_text_fn: Callable[[Dict[str, Any]], str],
        retriever=None,
    ):
        self.subject_name = "arithmetic"
        self._evaluator_llm = evaluator_llm
        self._primary_chat_llm = primary_chat_llm
        self._backup_chat_llm = backup_chat_llm
        self._assessment_text_fn = assessment_text_fn
        self._dimension_prompts = ARITHMETIC_PROMPTS
        if retriever is not None:
            self._retriever = retriever
        else:
            try:
                self._retriever = build_retriever(DEFAULT_ARITHMETIC_CORPUS)
            except Exception as err:
                print(f"[ArithmeticSubjectModule] Failed to initialize retriever: {err}")
                self._retriever = None

    def evaluate(self, student_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        student_text = self._assessment_text_fn(assessment_data)
        results = []
        structured_dimensions: Dict[str, Dict[str, Any]] = {}

        for name, prompt in self._dimension_prompts.items():
            rag_context = self._get_context(f"{name}: {student_text}")
            enriched_context = build_reasoning_support(
                "arithmetic",
                name,
                student_text,
                rag_context=rag_context,
            )
            chain = LLMChain(
                llm=self._evaluator_llm,
                prompt=prompt,
            )
            raw_output = chain.run(student_text=student_text, context=enriched_context)
            print(f"--- Arithmetic {name} Chain Result ---\n{raw_output}\n")
            parsed_json = self._safe_parse_json(raw_output)
            if isinstance(parsed_json, dict):
                structured_dimensions[name] = parsed_json
            formatted_section = self._format_dimension_output(name, parsed_json)
            print(f"--- Arithmetic {name} Dimension Result ---\n{formatted_section}\n")
            results.append(formatted_section)

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
        agent, first_time = self._ensure_chat_agent(state, question)

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
        first_question: str,
    ) -> Tuple[ConversationChain, bool]:
        existing_agent: Optional[ConversationChain] = state.get("agent")
        if existing_agent:
            return existing_agent, False

        system_prompt = ARITHMETIC_TUTOR_PROMPT.format(
            prior_summary=state["evaluation"],
            raw_json=state["raw_json_str"],
        )
        tutor_support = build_reasoning_support(
            "arithmetic",
            "Tutor",
            state.get("student_text", ""),
            rag_context=self._get_context(state.get("student_text", "")),
        )
        system_prompt = (
            f"{system_prompt}\n\n{tutor_support}\n\n"
            "Deliberate with the checklist above before responding concisely."
        )

        memory = ConversationBufferMemory(return_messages=True)
        memory.chat_memory.add_message({"role": "system", "content": system_prompt})
        memory.chat_memory.add_message({"role": "user", "content": first_question})

        chat_chain = ConversationChain(llm=self._primary_chat_llm, memory=memory)
        state["agent"] = chat_chain
        state["backend"] = "gpt"
        return chat_chain, True

    def _get_context(self, query: str) -> str:
        if not self._retriever:
            return ""
        documents = self._retriever.get_relevant_documents(query)
        if not documents:
            return ""
        return "\n\n".join(doc.page_content for doc in documents)

    @staticmethod
    def _safe_parse_json(response_text: str) -> Dict[str, Any]:
        text = response_text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"raw": text}
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {"raw": text}

    @staticmethod
    def _format_dimension_output(name: str, data: Dict[str, Any]) -> str:
        if "raw" in data:
            return f"--- {name} Dimension ---\n{data['raw']}"

        title = data.get("title", f"{name} Dimension")
        aspects = data.get("aspects", [])
        gap = data.get("most_critical_gap", "")

        lines = [f"Title: {title}"]
        for aspect in aspects:
            aspect_name = aspect.get("aspect", "Unknown aspect")
            labels = aspect.get("labels", [])
            explanation = aspect.get("explanation", "")
            score_hint = aspect.get("model_score_hint")
            lines.append(f"- Aspect: {aspect_name}")
            lines.append(f"  Labels: [{', '.join(labels)}]")
            if score_hint is not None:
                lines.append(f"  Model Score Hint: {score_hint}")
            lines.append(f"  Explanation: {explanation}")
        if gap:
            lines.append(f"Most critical gap: {gap}")
        return "\n".join(lines)

    @staticmethod
    def _log_priority(priority_result: Dict[str, Any]) -> None:
        """Print priority outcome for quick verification."""
        if not isinstance(priority_result, dict):
            print("[Priority] 未能计算出优先级结果。")
            return
        top_dim = priority_result.get("top_dimension")
        top_label = priority_result.get("top_label_in_top_dimension")
        print("[Priority] ===== PRIORITY CHECK =====")
        print(f"[Priority] Top dimension: {top_dim}")
        print(f"[Priority] Top label in top dimension: {top_label}")
