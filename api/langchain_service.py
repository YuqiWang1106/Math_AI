import os, json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.chains import LLMChain, ConversationChain
from langchain.memory import ConversationBufferMemory

from .prompts import (
    EVALUATOR_SYSTEM_PROMPT,
    REFINER_PROMPT,
    REVIEWER_PROMPT,
    TUTOR_PROMPT,
)

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)

CHAT_SESSIONS = {} # Global Dictionary (student_id as key, chat history as value)

def get_chat_agent(student_id: str, assessment_data: dict, first_question: str):
    """
    If it is called for the first time: Evaluate first + create the conversation agent with memory;
    Otherwise: Directly return the existing agent
    """
    # Check Existence of Chat History (student_id as condition)
    # ----- Not First Time Situation ----- #
    if student_id in CHAT_SESSIONS:
        return CHAT_SESSIONS[student_id]["agent"], False

    # ----- First Time Situation ----- #

    student_text = create_self_assessment_text(assessment_data) # Convert raw JSON to long text
    eval_result = evaluate_self_assessment(student_text, student_id) # ReAct Loop Evaluation --> Get Structured JSON result
    eval_json_str = json.dumps(eval_result, ensure_ascii=False, indent=2)
    raw_json_str  = json.dumps(assessment_data, ensure_ascii=False, indent=2)

    # System Prompt (include Evaluation Report JSON, and store in memory)
    system_prompt = TUTOR_PROMPT.format(
        prior_summary=eval_json_str,
        raw_json=raw_json_str
        )
    # Initiate LongChain Memory
    memory = ConversationBufferMemory(return_messages=True)

    memory.chat_memory.add_message({"role": "system", "content": system_prompt}) # Manually store system prompt
    memory.chat_memory.add_message({"role": "user", "content": first_question}) # Manuallyh store student's first question

    # Create ConversationChain (Chat Agent)
        # 1. Use chat_chain.run(input_text)
        # 2. Get memory -> Connect with input_text -> Send to LLM -> Get response -> Automatically store back to memory
    chat_chain = ConversationChain(llm=llm, memory=memory)

    # Write into cache
    CHAT_SESSIONS[student_id] = {"agent": chat_chain, "initialized": True}
    return chat_chain, True 


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


def ask_with_memory(student_id: str, assessment_data: dict, question: str) -> str:
    agent, first_time = get_chat_agent(student_id, assessment_data, question)

    if first_time:
        response = agent.run("")  # The first question has manually written into memory, so it is empty of input here
    else:
        response = agent.run(question)
    return response.strip()