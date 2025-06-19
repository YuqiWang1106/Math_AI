import os, json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain

import os

from .prompts import (
    EVALUATOR_SYSTEM_PROMPT,
    REFINER_PROMPT,
    REVIEWER_PROMPT,
    TUTOR_PROMPT
)

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)

# Tools for ReAct agent
CURRENT_ASSESSMENT_TEXT = ""

def get_self_assessment(_):
    """Return the full self-assessment text that must be evaluated."""
    return CURRENT_ASSESSMENT_TEXT

def return_json(data):
    """Ensure valid JSON string is returned"""
    if isinstance(data, str):
        try:
            json.loads(data)
            return data
        except json.JSONDecodeError:
            pass
    return json.dumps(data, ensure_ascii=False)

tools = [
    Tool(
        name="GetSelfAssessment",
        func=get_self_assessment,
        description="Returns the student's self-assessment that the evaluator must grade."
    ),
    Tool(
        name="ReturnJSON",
        func=return_json,
        description="Call this at the FINAL step and pass the full evaluation JSON as the input."
    )
]

# Setup chains
refiner_chain = LLMChain(llm=llm, prompt=REFINER_PROMPT)
reviewer_chain = LLMChain(llm=llm, prompt=REVIEWER_PROMPT)

# Main evaluation logic
def evaluate_self_assessment(student_text: str, student_id: str) -> dict:
    global CURRENT_ASSESSMENT_TEXT
    CURRENT_ASSESSMENT_TEXT = student_text

    evaluator_agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        agent_kwargs={"system_message": EVALUATOR_SYSTEM_PROMPT},
        return_only_outputs=True,
        verbose=True,
        callbacks=None,
    )

    result_str = evaluator_agent.invoke({"input": "Begin evaluation."})
    return_payload = result_str["output"] if isinstance(result_str, dict) else result_str

    if isinstance(return_payload, str):
        draft_eval = json.loads(return_payload)
    elif isinstance(return_payload, dict):
        draft_eval = return_payload
    else:
        raise ValueError("Unexpected ReturnJSON format")

    # Refine
    for i in range(2):
        refinement = refiner_chain.predict(
            student_text=student_text,
            draft=json.dumps(draft_eval, ensure_ascii=False)
        ).strip()
        # print(f"[Refine round {i}] raw refinement =", repr(refinement))
        if refinement == "NO_CHANGE":
            break
        draft_eval = json.loads(refinement)

    # Review
    review_result = reviewer_chain.predict(draft=json.dumps(draft_eval, ensure_ascii=False), callbacks=None).strip()
    if not review_result or review_result.upper() == "NO_CHANGE":
        return draft_eval
    return json.loads(review_result)

# Convert raw assessment dict into evaluable text
def create_self_assessment_text(assessment: dict) -> str:
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

# Generate follow-up answer for student's question
def answer_student_question(question: str, student_id: str, assessment_data: dict) -> str:
    """
    Run full pipeline: evaluate the self-assessment, then use that evaluation
    to answer the student's follow-up question.
    
    Args:
        question: the student's question.
        student_id: for logging (future use, not used in logic now).
        assessment_data: the raw JSON of student's self-assessment.
    
    Returns:
        One short AI-generated tutoring response.
    """
    # Step 1: Create evaluable text
    student_text = create_self_assessment_text(assessment_data)

    # Step 2: Run evaluation using LangChain ReAct agent
    eval_result = evaluate_self_assessment(student_text, student_id)

    # Step 3: Prepare tutor prompt with evaluation result
    eval_json_str = json.dumps(eval_result, ensure_ascii=False, indent=2)

    # Step 4: Use tutoring prompt to generate response
    tutor_chain = LLMChain(llm=llm, prompt=TUTOR_PROMPT)
    response = tutor_chain.invoke({
        "question": question,
        "prior_summary": eval_json_str
    })["text"]

    return response
