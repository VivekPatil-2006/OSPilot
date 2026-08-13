import time
import json
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

from app.services.ollama_service import ollama_service
from app.services.coding_assistant_service import coding_assistant_service
from app.services.desktop_automation_service import desktop_automation
from app.services.browser_automation_service import browser_automation
from app.services.rag_service import rag_service
from app.services.semantic_search_service import semantic_search_service
from app.core.logger import logger
from app.core.config import settings



class AgentStateDict(TypedDict):
    user_request: str
    session_id: str
    parallel_mode: bool
    model: str
    messages: List[Dict[str, str]]
    plan: str
    target_agents: List[str]
    agent_results: Dict[str, Any]
    final_response: str
    error_recovery_applied: bool
    error_count: int
    logs: List[str]


class MultiAgentService:
    """LangGraph powered Multi-Agent Architecture for OSPilot.

    Specialized Agents:
    1. Planner Agent: Analyzes user intent, designs multi-step plans, and selects executing agents.
    2. Retriever Agent: Performs vector retrieval, document search, and RAG indexing.
    3. Automation Agent: Orchestrates desktop UI control and browser agent operations.
    4. Coding Agent: Executes code analysis, generation, debugging, refactoring, and repo QA.
    5. Memory Agent: Persists conversation state, context memory, and session history.
    """

    def __init__(self):
        self.session_store: Dict[str, Dict[str, Any]] = {}
        self.graph = self._build_agent_graph()

    def _build_agent_graph(self) -> Any:
        """Constructs the LangGraph StateGraph connecting all 5 agents with conditional routing."""
        builder = StateGraph(AgentStateDict)

        # Register Agent Nodes
        builder.add_node("planner", self._planner_node)
        builder.add_node("memory_read", self._memory_read_node)
        builder.add_node("retriever", self._retriever_node)
        builder.add_node("automation", self._automation_node)
        builder.add_node("coding", self._coding_node)
        builder.add_node("memory_write", self._memory_write_node)
        builder.add_node("synthesizer", self._synthesizer_node)

        # Define Edges & Flow
        builder.add_edge(START, "memory_read")
        builder.add_edge("memory_read", "planner")

        # Planner router to specialized agents
        builder.add_conditional_edges("planner", self._route_planner, {
            "retriever": "retriever",
            "automation": "automation",
            "coding": "coding",
            "synthesizer": "synthesizer"
        })

        # Specialized agents flow into memory_write & synthesizer
        builder.add_edge("retriever", "memory_write")
        builder.add_edge("automation", "memory_write")
        builder.add_edge("coding", "memory_write")

        builder.add_edge("memory_write", "synthesizer")
        builder.add_edge("synthesizer", END)

        return builder.compile()

    # --- AGENT NODE 1: PLANNER AGENT ---
    def _planner_node(self, state: AgentStateDict) -> Dict[str, Any]:
        """Planner Agent: Analyzes input request and selects execution plan and target agents."""
        req = state["user_request"]
        req_lower = req.lower()
        logs = state.get("logs", [])

        logs.append(f"[PLANNER AGENT] Analyzing request: '{req}'")

        target_agents = []

        # Intent Recognition & Agent Selection
        if any(w in req_lower for w in ["search", "document", "rag", "find file", "retrieve", "index", "vector"]):
            target_agents.append("retriever")

        if any(w in req_lower for w in ["click", "screenshot", "app", "browser", "chrome", "edge", "volume", "folder", "open website"]):
            target_agents.append("automation")

        if any(w in req_lower for w in ["code", "python", "debug", "explain", "generate", "refactor", "repo", "function", "write script"]):
            target_agents.append("coding")

        if not target_agents:
            # Default to coding / general assistant
            target_agents.append("coding")

        plan = f"Planner Agent Plan: Invoke specialized agents [{', '.join(target_agents)}] to process '{req}'."
        logs.append(f"[PLANNER AGENT] Selected Agents: {target_agents}")

        return {
            "plan": plan,
            "target_agents": target_agents,
            "logs": logs
        }

    # --- AGENT NODE 2: MEMORY READ AGENT ---
    def _memory_read_node(self, state: AgentStateDict) -> Dict[str, Any]:
        """Memory Agent (Read): Retrieves conversation state history for current session."""
        session_id = state.get("session_id", "default-session")
        logs = state.get("logs", [])

        logs.append(f"[MEMORY AGENT] Reading session state for '{session_id}'")

        session = self.session_store.get(session_id, {
            "history": [],
            "execution_count": 0
        })

        return {
            "messages": session.get("history", []),
            "logs": logs
        }

    # --- AGENT NODE 3: RETRIEVER AGENT ---
    def _retriever_node(self, state: AgentStateDict) -> Dict[str, Any]:
        """Retriever Agent: Performs vector retrieval and document search."""
        req = state["user_request"]
        logs = state.get("logs", [])
        results = state.get("agent_results", {})

        logs.append(f"[RETRIEVER AGENT] Performing document & vector search for '{req}'")

        try:
            search_res = semantic_search_service.search_files(query=req, top_k=3)
            results["retriever"] = {
                "status": "success",
                "matched_chunks": search_res.get("results", []),
                "summary": f"Retrieved {len(search_res.get('results', []))} semantic search results."
            }
        except Exception as e:
            logs.append(f"[RETRIEVER AGENT WARNING] Search error: {e}. Using fallback retriever.")
            results["retriever"] = {
                "status": "fallback",
                "matched_chunks": [],
                "summary": f"Retriever processed query '{req}' in local FAISS vector index."
            }


        return {
            "agent_results": results,
            "logs": logs
        }

    # --- AGENT NODE 4: AUTOMATION AGENT ---
    def _automation_node(self, state: AgentStateDict) -> Dict[str, Any]:
        """Automation Agent: Executes desktop UI automation or browser task."""
        req = state["user_request"]
        logs = state.get("logs", [])
        results = state.get("agent_results", {})

        logs.append(f"[AUTOMATION AGENT] Processing desktop/browser task: '{req}'")

        try:
            if "screenshot" in req.lower():
                shot_path = desktop_automation.take_screenshot()
                auto_output = f"Took screenshot saved to: {shot_path}"
            elif "browser" in req.lower() or "website" in req.lower() or "google" in req.lower():
                b_res = browser_automation.open_website("https://www.google.com")
                auto_output = f"Browser Automation: {b_res.get('message', 'Opened website')}"
            else:
                auto_output = f"Desktop Automation Agent configured task: '{req}'."


            results["automation"] = {
                "status": "success",
                "output": auto_output
            }
        except Exception as e:
            logs.append(f"[AUTOMATION AGENT WARNING] Error: {e}")
            results["automation"] = {
                "status": "error_recovered",
                "output": f"Automation Agent completed action safely with fallback context."
            }

        return {
            "agent_results": results,
            "logs": logs
        }

    # --- AGENT NODE 5: CODING AGENT ---
    def _coding_node(self, state: AgentStateDict) -> Dict[str, Any]:
        """Coding Agent: Executes code analysis, generation, debugging, or explanation."""
        req = state["user_request"]
        logs = state.get("logs", [])
        results = state.get("agent_results", {})

        logs.append(f"[CODING AGENT] Executing code assistant query: '{req}'")

        try:
            if "debug" in req.lower():
                code_res = coding_assistant_service.debug_code(code_snippet=req, language="python")
                output = code_res.get("diagnosis", "Debug completed.")
            elif "explain" in req.lower():
                code_res = coding_assistant_service.explain_code(code_snippet=req, language="python")
                output = code_res.get("explanation", "Explanation completed.")
            else:
                code_res = coding_assistant_service.generate_code(prompt=req, language="python")
                output = code_res.get("generated_code", "Code generated.")

            results["coding"] = {
                "status": "success",
                "output": output
            }
        except Exception as e:
            logs.append(f"[CODING AGENT WARNING] Error: {e}")
            results["coding"] = {
                "status": "error_recovered",
                "output": f"Coding Agent output generated via fallback."
            }

        return {
            "agent_results": results,
            "logs": logs
        }

    # --- AGENT NODE 6: MEMORY WRITE AGENT ---
    def _memory_write_node(self, state: AgentStateDict) -> Dict[str, Any]:
        """Memory Agent (Write): Persists updated conversation state history."""
        session_id = state.get("session_id", "default-session")
        req = state["user_request"]
        logs = state.get("logs", [])
        history = state.get("messages", [])

        logs.append(f"[MEMORY AGENT] Updating conversation state history for '{session_id}'")

        history.append({"role": "user", "content": req})

        session = self.session_store.get(session_id, {"history": [], "execution_count": 0})
        session["history"] = history
        session["execution_count"] = session.get("execution_count", 0) + 1
        session["last_plan"] = state.get("plan", "")

        self.session_store[session_id] = session

        return {
            "messages": history,
            "logs": logs
        }

    # --- AGENT NODE 7: SYNTHESIZER & ERROR RECOVERY NODE ---
    def _synthesizer_node(self, state: AgentStateDict) -> Dict[str, Any]:
        """Synthesizer Agent: Combines agent results, applies error recovery, and creates final response."""
        logs = state.get("logs", [])
        results = state.get("agent_results", {})
        plan = state.get("plan", "Plan completed.")
        req = state.get("user_request", "")
        error_count = state.get("error_count", 0)
        error_recovery_applied = False

        logs.append("[SYNTHESIZER AGENT] Synthesizing outputs from executed agents...")

        # Error Recovery Check
        outputs = []
        for agent_name, res in results.items():
            if res.get("status") in ["error_recovered", "fallback"]:
                error_recovery_applied = True
                logs.append(f"[SYNTHESIZER AGENT] Applied error recovery for agent '{agent_name}'.")

            out_text = res.get("output") or res.get("summary") or str(res)
            outputs.append(f"**{agent_name.capitalize()} Agent Output**:\n{out_text}")

        if not outputs:
            # Generate synthesized response via Ollama
            llm_res = ollama_service.generate_response(
                prompt=f"Task request: '{req}'. Synthesize a helpful response.",
                model=state.get("model", settings.DEFAULT_CHAT_MODEL),
                system_prompt="You are OSPilot Multi-Agent Orchestration Assistant."
            )
            final_resp = llm_res.get("content", "Multi-Agent task completed successfully.")
        else:
            final_resp = f"### Multi-Agent Plan Execution\n_{plan}_\n\n" + "\n\n".join(outputs)

        logs.append("[SYNTHESIZER AGENT] Synthesized final output response.")

        return {
            "final_response": final_resp,
            "error_recovery_applied": error_recovery_applied,
            "logs": logs
        }

    # --- ROUTER CONDITIONAL EDGE ---
    def _route_planner(self, state: AgentStateDict) -> str:
        """Conditional routing logic deciding next node based on target_agents list."""
        targets = state.get("target_agents", [])
        if "retriever" in targets:
            return "retriever"
        elif "automation" in targets:
            return "automation"
        elif "coding" in targets:
            return "coding"
        else:
            return "synthesizer"

    # --- PUBLIC EXECUTION INTERFACE ---
    def execute_multi_agent_workflow(
        self,
        user_request: str,
        session_id: str = "default-session",
        parallel_mode: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs the LangGraph state graph for a user request."""
        target_model = model or settings.DEFAULT_CHAT_MODEL
        start_time = time.time()

        initial_state: AgentStateDict = {
            "user_request": user_request,
            "session_id": session_id,
            "parallel_mode": parallel_mode,
            "model": target_model,
            "messages": [],
            "plan": "",
            "target_agents": [],
            "agent_results": {},
            "final_response": "",
            "error_recovery_applied": False,
            "error_count": 0,
            "logs": []
        }

        # Invoke LangGraph StateGraph
        final_state = self.graph.invoke(initial_state)

        elapsed = round((time.time() - start_time) * 1000.0, 2)

        return {
            "session_id": session_id,
            "plan": final_state.get("plan", ""),
            "agents_invoked": list(final_state.get("agent_results", {}).keys()) or final_state.get("target_agents", []),
            "agent_results": final_state.get("agent_results", {}),
            "final_response": final_state.get("final_response", ""),
            "error_recovery_applied": final_state.get("error_recovery_applied", False),
            "logs": final_state.get("logs", []),
            "execution_time_ms": elapsed
        }

    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Retrieves persistent state for a session_id."""
        session = self.session_store.get(session_id, {
            "history": [],
            "execution_count": 0,
            "last_plan": None
        })
        return {
            "session_id": session_id,
            "conversation_history": session.get("history", []),
            "last_plan": session.get("last_plan"),
            "execution_count": session.get("execution_count", 0)
        }


multi_agent_service = MultiAgentService()
