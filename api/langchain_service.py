import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.chains import LLMChain, ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate


from .prompts import (
    FACTS_PROMPT,
    STRATEGIES_PROMPT,
    PROCEDURES_PROMPT,
    RATIONALES_PROMPT,
    TUTOR_PROMPT,
)

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_API_KEY"]  = os.getenv("GOOGLE_API_KEY")

gpt_llm = ChatOpenAI(model_name="gpt-4.1-2025-04-14", temperature=0)
gemini_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)

llm = gpt_llm

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
    raw_json_str  = str(assessment_data)

    # System Prompt (include Evaluation Report JSON, and store in memory)
    system_prompt = TUTOR_PROMPT.format(
        prior_summary=eval_result,
        raw_json=raw_json_str
        )
    # Initiate LongChain Memory
    memory = ConversationBufferMemory(return_messages=True)

    memory.chat_memory.add_message({"role": "system", "content": system_prompt}) # Manually store system prompt
    memory.chat_memory.add_message({"role": "user", "content": first_question}) # Manuallyh store student's first question

    # Create ConversationChain (Chat Agent)
        # 1. Use chat_chain.run(input_text)
        # 2. Get memory -> Connect with input_text -> Send to LLM -> Get response -> Automatically store back to memory
    chat_chain = ConversationChain(llm=gpt_llm, memory=memory)

    # Write into cache
    CHAT_SESSIONS[student_id] = {"agent": chat_chain, "initialized": True}
    return chat_chain, True 


# Tools for ReAct agent
CURRENT_ASSESSMENT_TEXT = ""

def get_self_assessment(_):
    """Return the full self-assessment text that must be evaluated."""
    return CURRENT_ASSESSMENT_TEXT


tools = [
    Tool(
        name="GetSelfAssessment",
        func=get_self_assessment,
        description="Returns the student's self-assessment that the evaluator must grade."
    )
]

DIMENSIONS = {
    "Facts": FACTS_PROMPT,
    "Strategies": STRATEGIES_PROMPT,
    "Procedures": PROCEDURES_PROMPT,
    "Rationales": RATIONALES_PROMPT,
}

def evaluate_self_assessment(student_text: str, student_id: str) -> str:
    results = []

    for name, prompt_template in DIMENSIONS.items():
        # 把每个维度的 prompt 包装成 PromptTemplate
        chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate.from_template(prompt_template),
        )

        # 执行链
        output = chain.run(student_text=student_text)

        # 打印到 terminal
        print(f"--- {name} Dimension Result ---\n{output}\n")

        # 收集结果
        results.append(f"--- {name} Dimension ---\n{output.strip()}\n")

    return "\n\n".join(results)


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

    def _run(agent, text):
        return agent.run(text).strip()

    try:
        if first_time:
            return _run(agent, "")
        return _run(agent, question)
    except Exception as e_gpt:
        try:
            agent.llm = gemini_llm
            CHAT_SESSIONS[student_id]["backend"] = "gemini"
            if first_time:
                return _run(agent, "")
            return _run(agent, question)
        except Exception as e_gem:
            CHAT_SESSIONS[student_id]["backend"] = "gpt"
            raise e_gpt
         
    # if first_time:
    #     response = agent.run("")  # The first question has manually written into memory, so it is empty of input here
    # else:
    #     response = agent.run(question)
    # return response.strip()