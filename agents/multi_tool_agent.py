# FILE: agents/multi_tool_agent.py
import os
import sys
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Union, Optional, Any

from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# ────────────────────────────────────────────────────────────────────────────────
# Environment & Path setup
# ────────────────────────────────────────────────────────────────────────────────
load_dotenv()

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# ────────────────────────────────────────────────────────────────────────────────
# Retriever imports
# ────────────────────────────────────────────────────────────────────────────────
from src.retrievers.sql_retriever import get_sql_agent
from src.retrievers.vector_retriever import get_vector_retriever
from src.retrievers.graph_retriever import get_graph_retriever
from tools.rag_tool import create_rag_tool  # RAG tool factory

# ────────────────────────────────────────────────────────────────────────────────
# Logging setup
# ────────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="ui/agent_debug.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

jsonl_logger = logging.getLogger("jsonl_logger")
jsonl_logger.setLevel(logging.INFO)
jsonl_handler = logging.FileHandler("ui/agent_calls.log")
jsonl_handler.setFormatter(logging.Formatter("%(message)s"))
jsonl_logger.addHandler(jsonl_handler)
jsonl_logger.propagate = False


# ────────────────────────────────────────────────────────────────────────────────
# Retriever singletons
# ────────────────────────────────────────────────────────────────────────────────
sql_agent_executor = get_sql_agent()
vector_retriever_func = get_vector_retriever()
graph_retriever_func = get_graph_retriever()

# ────────────────────────────────────────────────────────────────────────────────
# Helper to strip markdown code fences
# ────────────────────────────────────────────────────────────────────────────────
def _clean_query_input(query: str) -> str:
    match = re.search(r"```(?:\w+\n)?(.*?)```", query, flags=re.DOTALL)
    return match.group(1).strip() if match else query.strip()


# ────────────────────────────────────────────────────────────────────────────────
# Tool factory
# ────────────────────────────────────────────────────────────────────────────────
def create_tools(llm) -> List[Tool]:
    tools: List[Tool] = []

    # SQL tool
    if sql_agent_executor:
        tools.append(
            Tool(
                name="sql_search",
                description=(
                    "**PRIMARY TOOL for detailed questions about CUSTOMERS, ORDERS, or PRODUCTS.** " 
                    "Use this tool to get specific information, lookup details, or answer questions " 
                    "related to individual records or aggregates from the SQL (DuckDB) database." 
                ),
                func=lambda q: sql_agent_executor.invoke(
                    {"input": _clean_query_input(q)}
                )["output"],
            )
        )

    # Vector tool 
    if vector_retriever_func:
        tools.append(
            Tool(
                name="vector_search",
                description=(
                    "**Use this tool to semantically search document content**, especially PDFs or emails "
                    "that have been previously ingested. Ideal for answering questions about text inside documents "
                     "like policies, contracts, or internal emails."
                ),
                func=lambda q: vector_retriever_func(_clean_query_input(q)),
            )
        )

    # Graph tool
    if graph_retriever_func:
        def robust_graph_search(q: str) -> str:
            cleaned = _clean_query_input(q)
            try:
                return str(graph_retriever_func(cleaned))
            except Exception as e:
                logging.warning(f"Graph query failed: {e}")
                if (
                    "UNION" in cleaned.upper()
                    and "same return column names" in str(e)
                ):
                    return (
                        "Please ensure each part of the UNION returns the same "
                        "column names, or ask separate questions."
                    )
                return f"Graph query error: {e}"

        tools.append(
            Tool(
                name="graph_search",
                description=(
                    "Answer questions about relationships among Persons, Projects, "
                    "and Departments in Neo4j. "
                    "Input MUST be a valid Cypher query string (e.g., 'MATCH (a:Person) RETURN a.name')." # Explicit Cypher instruction
                ),
                func=robust_graph_search,
            )
        )

    # # RAG tool
    # rag_tool_func = create_rag_tool(llm)
    # tools.append(
    #     Tool(
    #         name="rag_tool",
    #         description="Answer a question using a specific document. Input must be a dictionary with keys: 'query' and 'filename'.",
    #         func=rag_tool_func,
    #     )
    

    return tools


# ────────────────────────────────────────────────────────────────────────────────
# Agent constructor
# ────────────────────────────────────────────────────────────────────────────────
def create_agent(tools: List[Tool], llm):
    prompt = PromptTemplate.from_template(
        """
You are a helpful AI assistant with access to the following tools:
{tools}

Use this format:

Question: the input question
Thought: reasoning
Action: the tool to use, one of [{tool_names}]
Action Input: input for the tool
Observation: tool result
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original question

Begin!

Question: {input}
{agent_scratchpad}
"""
    )

    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    return AgentExecutor(agent=agent, tools=tools, verbose=True)



# ────────────────────────────────────────────────────────────────────────────────
# Driver with logging for UI
# ────────────────────────────────────────────────────────────────────────────────
def run_agent_with_logging(
    agent: AgentExecutor,
    query: str,
    domain: str,
    source: str, # THIS IS THE KEY PARAMETER FOR ROUTING
    unstructured_data: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    unstructured_data = unstructured_data or []
    start = datetime.now()
    final_output = "No output generated."
    agent_response: Optional[dict] = None
    agent_input: Optional[dict] = None
    source_highlights: List[Dict[str, str]] = []
    tool_counts: Dict[str, int] = {}
    used_tool = None

    try:
        # (ROUTING LOGIC) 
        # Centralized  tool routing logic based on 'source' parameter
        if source in {"Customers", "Orders", "Products"}:
            agent_input = {"input": query, "tool": "sql_search"}
            used_tool = "sql_search"
        elif source.endswith(".eml") or source.endswith(".pdf"):
            agent_input = {"input": {"query": query, "filename": source}}
            used_tool = "vector_search"
        elif source == "All": # Handle 'All' source with keyword check for structured data
            lower_query = query.lower()
            if "customer" in lower_query or "customers" in lower_query or \
               "order" in lower_query or "orders" in lower_query or \
               "product" in lower_query or "products" in lower_query:
                agent_input = {"input": query, "tool": "sql_search"}
                used_tool = "sql_search"
            else:
                agent_input = {"input": query} # Fallback to general agent decision for other queries
        else: # Original default fallback for any other unexpected 'source' value
            agent_input = {"input": query}

        # --- END MODIFICATION IN MULTI_TOOL_AGENT.PY (ROUTING LOGIC) ---

        # Safe execution
        agent_response = agent.invoke(agent_input)
        final_output = agent_response.get("output", final_output)

        # ── DEBUG: Print agent_response ──
        print("--- DEBUG: agent_response ---")
        print(json.dumps(agent_response, indent=2, default=str))

        # ── TOOL USAGE TRACKING ──
        # If intermediate_steps are present, extract tool usage from them
        # if "intermediate_steps" in agent_response:
        #     for step in agent_response["intermediate_steps"]:
        #         if len(step) >= 2:
        #             agent_action = step[0]
        #             observation = step[1]
        #             tool_name = None
        #             if hasattr(agent_action, 'tool'):
        #                 tool_name = agent_action.tool
        #                 print("tool_name",tool_name)
        #             if tool_name:
        #                 # used_tool=tool_name
        #                 tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        # # Otherwise, log the tool we *think* was used based on source
        # elif used_tool:
        #     tool_counts[used_tool] = 1

        tool_used = None
        if "intermediate_steps" in agent_response:
            for step in agent_response["intermediate_steps"]:
                if isinstance(step, (list, tuple)) and len(step) > 0 and hasattr(step[0], 'tool'):
                    tool_used = step[0].tool
                    tool_counts[tool_used] = tool_counts.get(tool_used, 0) + 1
                    logging.info(f"Tool extracted from intermediate_steps: {tool_used}")
                    break

        # Fallback to routing logic
        if not tool_used and used_tool:
            if used_tool not in ["sql_search", "vector_search"]:
                used_tool = "graph_search"
            tool_used = used_tool
            tool_counts[tool_used] = tool_counts.get(tool_used, 0) + 1
            logging.info(f"Tool inferred from routing logic: {tool_used}")

        # Fallback from ReAct-style output
        if not tool_used and isinstance(agent_response.get("output"), str):
            match = re.search(r"Action:\s*(\w+)", agent_response["output"])
            if match:
                tool_used = match.group(1)
                tool_counts[tool_used] = tool_counts.get(tool_used, 0) + 1
                logging.info(f"Tool parsed from output: {tool_used}")

        # ── SOURCE HIGHLIGHTS ──
        if "intermediate_steps" in agent_response:
            for step in agent_response["intermediate_steps"]:
                if len(step) > 0:
                    tool_name = step[0].tool_name if hasattr(step[0], 'tool_name') else None
                    observation = step[1]
                    if isinstance(observation, str) and "Source:" in observation:
                        source_text = observation.split("Source:")[1].strip()
                        relevant_text_in_answer = _extract_relevant_text(
                            final_output, observation
                        )
                        source_highlights.append({
                            "text": relevant_text_in_answer,
                            "source": source_text
                        })

    except Exception as e:
        final_output = f"Agent failed to answer: {e}"
        logging.error(f"Agent execution error: {e}")

    # ── JSONL logging ──
    log_entry: Dict[str, Union[str, float, Dict[str, int]]] = {
        "timestamp": start.isoformat(),
        "query": query,
        "domain": domain,
        "source": source,
        "final_answer": final_output,
        "response_time": (datetime.now() - start).total_seconds(),
        "agent_raw_response": agent_response,
        "tool_usage": tool_counts,
    }
    jsonl_logger.info(json.dumps(log_entry, ensure_ascii=False))

    # print("DEBUG source_highlights:", source_highlights)

    return {"answer": final_output, "source_highlights": source_highlights}

def _extract_relevant_text(answer: str, observation: str) -> str:
    """
    Extract the most similar sentence from the answer based on RAG observation text.
    """
    from difflib import SequenceMatcher
    import re

    # Extract source sentence (after "Source:")
    content_part = observation.split("Source:")[-1].strip()

    # Split answer into sentences
    sentences = re.split(r'(?<=[.!?]) +', answer.strip())

    best_score = 0.0
    best_match = ""
    for sentence in sentences:
        score = SequenceMatcher(None, sentence.lower(), content_part.lower()).ratio()
        print(f"[MATCH DEBUG] Score: {score:.3f} | Sentence: {sentence}")
        if score > best_score:
            best_score = score
            best_match = sentence

    if best_score < 0.4:
        print("[WARNING] No good match found for source highlight.")

    return best_match.strip()



# ────────────────────────────────────────────────────────────────────────────────
# Quick CLI test
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    rag = create_rag_tool(llm)

    test_input = {
        "query": "Summarize the risks associated with commercial real estate markets.",
        "filename": "finance.pdf"
    }

    print(rag(test_input))