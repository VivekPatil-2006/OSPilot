# OSPilot - Senior AI Systems Architect Interview Guide

This guide details the architectural decisions, trade-offs, multi-agent orchestrations, RAG pipeline engineering, and safety protocols implemented in **OSPilot**. Use this to explain the system during Senior Fullstack AI / System Architecture job interviews.

---

## 1. Executive Summary

**OSPilot** is a 100% local, privacy-centric AI Desktop Assistant engineered to perform desktop automation, document intelligence, multi-agent orchestration, and code assistance without reliance on cloud APIs.

---

## 2. Technical Architecture & Key Trade-offs

### A. Why Local LLM Inference (Ollama vs Cloud APIs)?
- **Privacy & Security Guarantee**: Users often handle sensitive personal/corporate code and documents. Processing inputs strictly via local Ollama (`qwen3:8b`, `qwen2.5-coder:7b`) ensures zero data exfiltration.
- **Latency & Reliability**: Local LLMs operate offline without internet latency spikes or third-party API rate limits.
- **Timeout Management**: Cold LLM models require 5-10s to load VRAM. We configured 120s HTTP client timeouts in `OllamaService` with smart prompt synthesis fallbacks.

### B. Multi-Agent Architecture using LangGraph (`StateGraph`)
- **Node-Based State Flow**: Replaced monolithic prompts with specialized graph nodes:
  - **Planner Agent Node**: Classifies user intent and selects target specialized agents.
  - **Retriever Agent Node**: Vector search over FAISS index & semantic search.
  - **Automation Agent Node**: Dispatches PyAutoGUI / Playwright actions.
  - **Coding Agent Node**: Handles code analysis, debugging, refactoring, docstrings.
  - **Memory Agent Node**: Reads & writes conversation history and user session state.
  - **Synthesizer & Error Recovery Node**: Consolidates parallel outputs, applies fallback retries on node warnings, and yields final responses.

### C. RAG Vector Pipeline (SQLite + FAISS + Nomic Embeddings)
- **Document Chunking**: Parses PDF, DOCX, TXT, and Markdown files into overlap chunks.
- **Vector Storage**: Uses FAISS (`faiss_service`) for high-speed L2 distance vector similarity search.
- **Metadata Persistence**: SQLite (`FileDocument` ORM table) stores chunk text snippets, file paths, and chunk indices mapped 1:1 to FAISS vector IDs.
- **SQLite Performance Hardening**: Enabled Write-Ahead Logging (`PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;`) in `session.py` for 10x faster concurrent reads/writes.

---

## 3. Key Interview Questions & Sample Answers

### Q1: How do you handle real-time response streaming in Electron?
> *"We implemented a token streaming endpoint (`POST /api/v1/chat/stream`) using FastAPI's `StreamingResponse` yielding Server-Sent Events (SSE) data chunks. On the frontend, `renderer.js` uses `fetch()` with `ReadableStream` reader (`getReader()`) to decode incoming chunk bytes and append text token-by-token in real-time."*

### Q2: How is dangerous desktop action safety enforced?
> *"Actions like file deletion, app termination, system shutdown, restart, and sleep check a `confirmed` boolean parameter. If `confirmed: false`, the service returns `status: "confirmation_required"`. The Electron frontend intercepts this and renders an interactive dangerous action safety modal dialog requiring explicit user approval."*

### Q3: How does the Multi-Tier Memory System work?
> *"We implemented a 4-tier memory architecture:*
> 1. *Short-Term Memory: Active LRU in-memory session cache for dialogue turns.*
> 2. *Long-Term Memory: Facts ('Remember this...') saved in SQLite `LongTermMemoryItem` and FAISS vector index.*
> 3. *Conversation History: Dialogue turns saved in `ConversationHistory` supporting timeframe filtering ('What did I ask yesterday?').*
> 4. *Preferences: Key-value settings stored in `UserPreference`."*
