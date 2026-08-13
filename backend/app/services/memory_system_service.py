import time
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.models import ConversationHistory, UserPreference, TaskHistoryLog, LongTermMemoryItem
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.ollama_service import ollama_service
from app.core.logger import logger
from app.core.config import settings

# Ensure database tables exist
Base.metadata.create_all(bind=engine)


class MemorySystemService:
    """Multi-Tiered Memory System for OSPilot.

    Memory Layers:
    1. Short-Term Memory: Active in-memory session cache for recent dialogue turns.
    2. Long-Term Memory: Persistent fact/instruction store in SQLite + FAISS Vector Memory.
    3. Conversation History: Multi-session history log with timestamp/timeframe filtering.
    4. Preference Storage: Key-value user preference settings.
    5. Task History Log: Audit trail of automated desktop/browser/coding actions.
    """

    def __init__(self):
        self._short_term_cache: Dict[str, List[Dict[str, str]]] = {}

    # --- 1. SHORT-TERM MEMORY ---
    def get_short_term_memory(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieves active short-term dialogue turns for a session."""
        if session_id not in self._short_term_cache:
            # Hydrate from SQLite if not in cache
            with SessionLocal() as db:
                records = db.query(ConversationHistory).filter_by(session_id=session_id).order_by(ConversationHistory.id.desc()).limit(limit).all()
                turns = [{"role": r.role, "content": r.content} for r in reversed(records)]
                self._short_term_cache[session_id] = turns

        return self._short_term_cache.get(session_id, [])[-limit:]

    def add_short_term_turn(self, session_id: str, role: str, content: str):
        """Appends a turn to short-term cache and persists to SQLite ConversationHistory."""
        if session_id not in self._short_term_cache:
            self._short_term_cache[session_id] = []

        self._short_term_cache[session_id].append({"role": role, "content": content})

        # Persist to SQLite
        with SessionLocal() as db:
            turn = ConversationHistory(session_id=session_id, role=role, content=content)
            db.add(turn)
            db.commit()

    # --- 2. LONG-TERM MEMORY & VECTOR INDEXING ---
    def remember_fact(self, fact_text: str, category: str = "general") -> Dict[str, Any]:
        """Stores explicit facts/instructions ('Remember this...') into SQLite and FAISS Vector Memory."""
        start_time = time.time()
        clean_fact = fact_text.strip()

        # Remove prefix if present
        clean_fact = re.sub(r'^(remember this:?|remember:?|please remember:?)\s*', '', clean_fact, flags=re.IGNORECASE)
        mem_key = f"mem_{uuid.uuid4().hex[:8]}"

        vector_indexed = False
        vector_id = None

        try:
            # Generate embedding and index into FAISS
            vec = embedding_service.embed_text(clean_fact)
            vector_id = faiss_service.add_vector(vec)
            vector_indexed = True
        except Exception as e:
            logger.warning(f"Vector embedding indexing failed for memory ({e}). Saving SQLite only.")

        with SessionLocal() as db:
            mem = LongTermMemoryItem(
                memory_key=mem_key,
                fact_content=clean_fact,
                category=category,
                vector_id=vector_id
            )
            db.add(mem)
            db.commit()

        elapsed = round((time.time() - start_time) * 1000.0, 2)
        logger.info(f"Stored long-term memory fact: '{clean_fact}' (Key: {mem_key})")

        return {
            "status": "stored",
            "memory_key": mem_key,
            "fact": clean_fact,
            "vector_indexed": vector_indexed,
            "execution_time_ms": elapsed
        }

    # --- 3. CONVERSATION HISTORY & TIMEFRAME QUERIES ---
    def query_conversation_history(self, session_id: Optional[str] = None, timeframe: str = "yesterday", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries past conversation turns by timestamp filter ('yesterday', 'today', 'last week')."""
        now = datetime.now(timezone.utc)

        if "yesterday" in timeframe.lower():
            start_date = now - timedelta(days=1)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif "today" in timeframe.lower():
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif "week" in timeframe.lower():
            start_date = now - timedelta(days=7)
            end_date = now
        else:
            start_date = now - timedelta(days=30)
            end_date = now

        with SessionLocal() as db:
            q = db.query(ConversationHistory)
            if session_id:
                q = q.filter_by(session_id=session_id)

            records = q.filter(ConversationHistory.created_at >= start_date).order_by(ConversationHistory.id.desc()).limit(limit).all()

            results = []
            for r in records:
                results.append({
                    "id": r.id,
                    "session_id": r.session_id,
                    "role": r.role,
                    "content": r.content,
                    "timestamp": r.created_at.isoformat()
                })
            return results

    # --- 4. NATURAL LANGUAGE MEMORY QUERY ("What did I ask yesterday?", "What is my name?") ---
    def query_memory(self, query_text: str, session_id: str = "default-session") -> Dict[str, Any]:
        """Handles natural language questions about conversation history or remembered facts."""
        start_time = time.time()
        q_lower = query_text.lower().strip()

        matched_facts = []
        history_matches = []

        # 1. Fetch relevant long-term memory facts from SQLite & FAISS
        with SessionLocal() as db:
            all_mems = db.query(LongTermMemoryItem).order_by(LongTermMemoryItem.id.desc()).limit(50).all()
            for m in all_mems:
                matched_facts.append(f"- [{m.category.upper()}] {m.fact_content}")

        # 2. Fetch timeframe history if asking about past dialogue
        if any(w in q_lower for w in ["yesterday", "today", "past", "history", "asked", "said", "last week"]):
            history_matches = self.query_conversation_history(session_id=None, timeframe=q_lower)

        # 3. Formulate response via Ollama or structured synthesis
        facts_str = "\n".join(matched_facts[:15]) if matched_facts else "No long-term facts stored yet."
        hist_str = "\n".join([f"[{h['timestamp'][:16]}] {h['role'].upper()}: {h['content']}" for h in history_matches[:10]]) if history_matches else "No matching conversation history found."

        prompt = (
            f"User Query: \"{query_text}\"\n\n"
            f"Stored Long-Term Memories:\n{facts_str}\n\n"
            f"Relevant Conversation History:\n{hist_str}\n\n"
            f"Answer the user query concisely based on the stored memories and history above."
        )

        llm_res = ollama_service.generate_response(
            prompt=prompt,
            model=settings.DEFAULT_CHAT_MODEL,
            system_prompt="You are OSPilot Memory System, providing accurate memory recall."
        )

        elapsed = round((time.time() - start_time) * 1000.0, 2)

        return {
            "query": query_text,
            "answer": llm_res.get("content", "Memory lookup completed."),
            "matched_facts": matched_facts[:10],
            "history_matches": history_matches[:10],
            "execution_time_ms": elapsed
        }

    # --- 5. PREFERENCE STORAGE ---
    def set_preference(self, key: str, value: str) -> Dict[str, str]:
        """Sets a key-value user preference setting in SQLite."""
        with SessionLocal() as db:
            pref = db.query(UserPreference).filter_by(key=key).first()
            if pref:
                pref.value = value
            else:
                pref = UserPreference(key=key, value=value)
                db.add(pref)
            db.commit()

        logger.info(f"Set preference '{key}' = '{value}'")
        return {"key": key, "value": value, "status": "updated"}

    def get_preferences(self) -> Dict[str, str]:
        """Retrieves all stored key-value user preferences from SQLite."""
        with SessionLocal() as db:
            prefs = db.query(UserPreference).all()
            return {p.key: p.value for p in prefs}

    # --- 6. TASK HISTORY LOG ---
    def log_task(self, action: str, status: str, details: Optional[str] = None, session_id: Optional[str] = "default-session"):
        """Logs an automated action to SQLite TaskHistoryLog."""
        with SessionLocal() as db:
            log_item = TaskHistoryLog(
                session_id=session_id,
                action=action,
                status=status,
                details=details
            )
            db.add(log_item)
            db.commit()

    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recorded task execution history from SQLite."""
        with SessionLocal() as db:
            tasks = db.query(TaskHistoryLog).order_by(TaskHistoryLog.id.desc()).limit(limit).all()
            return [
                {
                    "id": t.id,
                    "session_id": t.session_id,
                    "action": t.action,
                    "status": t.status,
                    "details": t.details,
                    "created_at": t.created_at.isoformat()
                }
                for t in tasks
            ]


memory_system_service = MemorySystemService()
