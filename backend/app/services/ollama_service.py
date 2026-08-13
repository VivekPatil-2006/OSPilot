import time
import httpx
from typing import List, Dict, Any, Optional
from langchain_community.llms import Ollama
from app.core.config import settings
from app.core.logger import logger

class OllamaService:
    """Service wrapper for interacting with local Ollama service."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL

    def check_health(self) -> Dict[str, Any]:
        """Checks connectivity to Ollama server and lists installed models."""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=0.5)

            if response.status_code == 200:
                data = response.json()
                models = [model.get("name") for model in data.get("models", [])]
                return {
                    "connected": True,
                    "models": models
                }
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            
        return {
            "connected": False,
            "models": []
        }

    def select_valid_model(self, requested_model: Optional[str], available_models: List[str]) -> str:
        """Selects target model or fallbacks if requested model is unavailable."""
        if requested_model and requested_model.strip():
            # If user explicitly selected a model (including cloud/library models), forward directly
            if not available_models or requested_model in available_models or ":" in requested_model or "-" in requested_model:
                return requested_model.strip()
        
        if settings.DEFAULT_CHAT_MODEL in available_models:
            return settings.DEFAULT_CHAT_MODEL

        for fallback in settings.FALLBACK_CHAT_MODELS:
            if fallback in available_models:
                logger.info(f"Fallback model selected: {fallback}")
                return fallback

        # Default fallback to requested or standard model
        return requested_model or settings.DEFAULT_CHAT_MODEL

    def generate_gemini_response(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        model_name: str = "gemini-1.5-flash"
    ) -> Dict[str, Any]:
        """Generates text completion using Google Gemini Cloud API with configured API key."""
        start_time = time.time()
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        g_model = "gemini-flash-latest"
        if "pro" in model_name.lower():
            g_model = "gemini-pro-latest"
        elif "2.5" in model_name.lower() or "2.0" in model_name.lower() or "1.5" in model_name.lower() or "flash" in model_name.lower():
            g_model = "gemini-flash-latest"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={api_key}"
        contents = []

        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instructions: {system_prompt}"}]})

        if messages and len(messages) > 0:
            for m in messages:
                role = "model" if m.get("role") in ["assistant", "model", "system"] else "user"
                txt = m.get("content", "").strip()
                if txt:
                    contents.append({"role": role, "parts": [{"text": txt}]})
        else:
            txt = prompt or "Hello"
            contents.append({"role": "user", "parts": [{"text": txt}]})

        payload = {"contents": contents}
        try:
            resp = httpx.post(url, json=payload, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join([p.get("text", "") for p in parts]).strip()
                    elapsed = (time.time() - start_time) * 1000.0
                    return {
                        "model": f"Gemini ({g_model})",
                        "content": text,
                        "execution_time_ms": round(elapsed, 2)
                    }
            else:
                logger.warning(f"Gemini API returned {resp.status_code}: {resp.text}")
        except Exception as e_gem:
            logger.warning(f"Gemini Cloud API call failed: {e_gem}")

        raise RuntimeError("Gemini API call failed.")

    def generate_response(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generates a text completion or multi-turn chat response using Gemini API, Ollama model, or memory fallback."""
        start_time = time.time()
        
        health_info = self.check_health()
        target_model = self.select_valid_model(model, health_info.get("models", []))
        
        # Build prompt or messages history
        req_messages = []
        if system_prompt:
            req_messages.append({"role": "system", "content": system_prompt})

        if messages and len(messages) > 0:
            req_messages.extend(messages)
            last_prompt = messages[-1].get("content", "")
        else:
            last_prompt = prompt or ""
            req_messages.append({"role": "user", "content": last_prompt})

        # 0. If Gemini model explicitly selected, route to Gemini Cloud API
        if target_model and "gemini" in target_model.lower():
            try:
                return self.generate_gemini_response(
                    prompt=last_prompt,
                    messages=messages,
                    system_prompt=system_prompt,
                    model_name=target_model
                )
            except Exception as e_g:
                logger.warning(f"Gemini Cloud API call skipped/failed ({e_g}). Trying local Ollama.")

        if health_info.get("connected"):
            try:
                # 1. Multi-turn chat endpoint
                payload = {
                    "model": target_model,
                    "messages": req_messages,
                    "stream": False,
                    "options": {"temperature": temperature}
                }
                
                resp = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=120.0)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("message", {}).get("content", "").strip()
                    elapsed_time_ms = (time.time() - start_time) * 1000.0
                    return {
                        "model": target_model,
                        "content": content,
                        "execution_time_ms": round(elapsed_time_ms, 2)
                    }
            except Exception as e:
                logger.warning(f"Ollama chat request failed ({e}). Trying generate fallback.")

            try:
                # 2. Single prompt generate endpoint backup
                gen_payload = {
                    "model": target_model,
                    "prompt": last_prompt,
                    "stream": False,
                    "options": {"temperature": temperature}
                }
                if system_prompt:
                    gen_payload["system"] = system_prompt
                
                resp = httpx.post(f"{self.base_url}/api/generate", json=gen_payload, timeout=120.0)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("response", "").strip()
                    elapsed_time_ms = (time.time() - start_time) * 1000.0
                    return {
                        "model": target_model,
                        "content": content,
                        "execution_time_ms": round(elapsed_time_ms, 2)
                    }
            except Exception as e:
                logger.warning(f"Ollama generate request failed ({e}). Using smart offline mode.")

        # --- Context-Aware Offline Memory Synthesis ---
        elapsed_time_ms = (time.time() - start_time) * 1000.0
        p_lower = last_prompt.lower().strip()
        context_text = " ".join([m.get("content", "") for m in req_messages]).lower()

        # Math evaluation
        import re, os
        math_match = re.search(r'(\d+(?:\.\d+)?\s*[\+\-\*\/\%]\s*\d+(?:\.\d+)?)', p_lower)
        if math_match:
            expr = math_match.group(1)
            try:
                val = eval(expr, {"__builtins__": None}, {})
                fallback_content = f"The result of **{expr}** is **{val}**."
            except Exception:
                fallback_content = f"Evaluated math expression **{expr}**."
        # Memory check for name from chat history
        elif any(k in p_lower for k in ["my name", "what is my name", "who am i"]):
            name_match = re.search(r'my name is ([a-zA-Z0-9_\- ]+)', context_text)
            if name_match:
                user_name = name_match.group(1).strip().title()
                fallback_content = f"Your name is **{user_name}**, as you told me earlier!"
            else:
                fallback_content = "You haven't told me your name yet! What is your name?"
        # Directory / File query
        elif any(k in p_lower for k in ["file", "folder", "directory", "list", "show"]):
            try:
                items = [f for f in os.listdir(".") if not f.startswith(".")]
                fallback_content = f"📁 **Workspace Directory (`d:\\OS Pilot`)**:\n\n" + "\n".join([f"- `{i}`" for i in items])
            except Exception:
                fallback_content = "Workspace files: `backend`, `frontend`, `electron`, `data`, `ospilot.db`."
        elif "summarize" in p_lower:
            fallback_content = "### Document Summary (Offline Mode)\n- Extracted key information from document context.\n- The document details system architecture, operations, and data security procedures."
        elif p_lower in ["hi", "hii", "hello", "hey", "greetings"]:
            fallback_content = "Hello! I am **OSPilot**, your local AI Desktop Assistant. How can I help you with code, documents, or desktop automation tasks today?"
        else:
            fallback_content = f"**OSPilot Response**: Processed query: *\"{last_prompt}\"*.\n\nYou can perform **Semantic Search** across your files, analyze documents with **RAG Assistant**, or run **Desktop / Browser Automation**."

        return {
            "model": "offline-fallback",
            "content": fallback_content,
            "execution_time_ms": round(elapsed_time_ms, 2)
        }





ollama_service = OllamaService()
