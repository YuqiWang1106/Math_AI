import json
from typing import Any, Callable, Dict, Optional, Tuple

from langchain.chains import ConversationChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from .geometry_prompts import (
    GEOMETRY_PROMPTS,
    build_geometry_context,
    route_geometry_topic,
)


GEOMETRY_TUTOR_PROMPT = """
You are a supportive, precision-focused geometry tutor for middle and early high school learners.
You specialize in coordinate geometry, transformations, similarity/congruence, measurement, and graph interpretation.
You MUST ground every response in BOTH the RAW_SELF_ASSESSMENT and the EVALUATION_JSON.
Always respond in 2-3 concise sentences tailored to the student's own wording and diagnosed needs.

Label glossary inside EVALUATION_JSON:
- Know-Know: student stated something relevant and correct.
- Know-Don't Know: student openly noted a relevant gap they need help with.
- False Knowledge: student claimed a relevant idea that is wrong or misleading.
- Omission: student skipped a required geometric idea entirely.
- Irrelevant Knowledge: student brought up off-topic information.

Priorities for each reply:
1. Redirect Irrelevant Knowledge back to the geometric goal.
2. Correct False Knowledge with a clear explanation or counterexample.
3. Fill an Omission with a concise explanation or probing question.
4. Reinforce Know-Know ideas to build confidence.
5. Close with encouragement tied to their geometry progress.

RAW_SELF_ASSESSMENT:
{raw_json}

EVALUATION_JSON:
{prior_summary}

Use geometry-specific language, stay focused on a single high-leverage idea per response, and do not solve the entire problem outright.
"""


class GeometrySubjectModule:
    """Geometry evaluation pipeline mirroring algebra/arithmetic structure."""

    def __init__(
        self,
        evaluator_llm: ChatGoogleGenerativeAI,
        primary_chat_llm,
        backup_chat_llm,
        assessment_text_fn: Callable[[Dict[str, Any]], str],
    ):
        self.subject_name = "geometry"
        self._evaluator_llm = evaluator_llm
        self._primary_chat_llm = primary_chat_llm
        self._backup_chat_llm = backup_chat_llm
        self._assessment_text_fn = assessment_text_fn
        self._dimension_prompts: Dict[str, PromptTemplate] = GEOMETRY_PROMPTS

    def evaluate(self, student_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        problem = (
            assessment_data.get("self_assessment", {}).get("problem")
            or assessment_data.get("self_evaluation", {}).get("problem")
            or ""
        )
        student_text = self._assessment_text_fn(assessment_data)
        topic_key = route_geometry_topic(problem, student_text)
        context = build_geometry_context(topic_key, include_global=True)

        results = []
        for name, prompt_template in self._dimension_prompts.items():
            chain = LLMChain(
                llm=self._evaluator_llm,
                prompt=prompt_template,
            )
            raw_output = chain.run(student_text=student_text, context=context)
            print(f"--- Geometry {name} Chain Result ---\n{raw_output}\n")
            parsed = self._safe_parse_json(raw_output)
            formatted = self._format_dimension_output(name, parsed)
            print(f"--- Geometry {name} Dimension Result ---\n{formatted}\n")
            results.append(f"--- {name} Dimension ---\n{formatted}\n")

        evaluation_report = "\n".join(results)
        return {
            "report": evaluation_report,
            "student_text": student_text,
        }

    def ask(self, state: Dict[str, Any], assessment_data: Dict[str, Any], question: str) -> str:
        agent, first_time = self._ensure_chat_agent(state, question)

        def _run(chain: ConversationChain, text: str) -> str:
            return chain.run(text).strip()

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

        system_prompt = GEOMETRY_TUTOR_PROMPT.format(
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
            return data["raw"]

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
