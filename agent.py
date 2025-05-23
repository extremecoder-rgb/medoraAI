from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from typing import List, Dict, Any, TypedDict
from config import AppConfig
from constants import GROQ_API_KEY
from logger import setup_logger
from tools import book_appointment, get_next_available_appointment, cancel_appointment

logger = setup_logger(__name__)

load_dotenv()

config = AppConfig()

llm = ChatGroq(model=config.LLM_MODEL, api_key=GROQ_API_KEY)
logger.info(f"LLM initialized with model: {llm}")

class AgentState(TypedDict):
    messages: List[Any]
    current_time: str

CONVERSATION: List[Any] = []

def receive_message_from_caller(message: str) -> None:
    logger.info(f"Received message: {message}")
    CONVERSATION.append(HumanMessage(content=message))
    state: AgentState = {
        "messages": CONVERSATION,
        "current_time": config.get_current_time()
    }
    logger.debug(f"State before invoke: {state}")
    try:
        new_state = caller_app.invoke(state)
        logger.debug(f"New state after invoke: {new_state}")
        CONVERSATION.extend(new_state["messages"][len(CONVERSATION):])
    except Exception as e:
        logger.exception(f"Error in receive_message_from_caller: {str(e)}")
        raise

def should_continue_caller(state: AgentState) -> str:
    logger.debug(f"Entering should_continue_caller with state: {state}")
    messages = state["messages"]
    if not messages:
        logger.warning("No messages in state")
        return "end"
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.content.strip():
        logger.info("Ending conversation")
        return "end"
    else:
        logger.info("Continuing conversation")
        return "continue"

def call_caller_model(state: AgentState) -> AgentState:
    logger.debug(f"Entering call_caller_model with state: {state}")
    messages = state["messages"]
    current_time = state["current_time"]

    try:
        system_message = config.CALLER_PA_PROMPT.format(current_time=current_time)
        logger.debug(f"Formatted system message: {system_message}")

        formatted_messages = [
            SystemMessage(content=system_message)
        ]

        for m in messages:
            if isinstance(m, (HumanMessage, AIMessage)):
                formatted_messages.append(m)
            else:
                logger.warning(f"Unexpected message type: {type(m)}")

        logger.debug(f"Formatted messages: {formatted_messages}")

        llm_response = llm.invoke(formatted_messages)
        logger.info(f"LLM response: {llm_response}")

        new_state = {"messages": messages + [AIMessage(content=llm_response.content)], "current_time": current_time}
        logger.debug(f"New state after LLM response: {new_state}")
        return new_state

    except Exception as e:
        logger.exception(f"Error in call_caller_model: {str(e)}")
        return {"messages": messages + [
            AIMessage(content="I'm sorry, I encountered an error. Could you please try again?")],
                "current_time": current_time}

def preprocess_llm_output(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.content:
        content = last_message.content
        if "<tool_call>" in content:
            tool_call = content.split("<tool_call>")[1].split("</tool_call>")[0].strip()
            try:
                result = eval(tool_call)
                content = result
            except Exception as e:
                content = f"Error processing request: {str(e)}"
        state["messages"][-1] = AIMessage(content=content)
    return state

caller_tools = [book_appointment, get_next_available_appointment, cancel_appointment]
tool_node = ToolNode(caller_tools)
logger.info(f"Tools initialized: {caller_tools}")

# Graph
caller_workflow = StateGraph(AgentState)

# Add Nodes
caller_workflow.add_node("agent", call_caller_model)
caller_workflow.add_node("preprocess", preprocess_llm_output)
caller_workflow.add_node("action", tool_node)

# Add Edges
caller_workflow.add_conditional_edges(
    "agent",
    should_continue_caller,
    {
        "continue": "preprocess",
        "end": END,
    },
)
caller_workflow.add_edge("preprocess", "action")
caller_workflow.add_edge("action", "agent")

# Set Entry Point and build the graph
caller_workflow.set_entry_point("agent")

caller_app = caller_workflow.compile()
logger.info("Caller workflow compiled successfully")