# OSPilot - Comprehensive Folder & File Structure Catalog

This document details every directory and file role across the OSPilot codebase.

```text
OSPilot/
├── README.md                      # Main Production README & Mermaid Architecture Diagrams
├── DEPLOYMENT.md                  # Packaging & Deployment Instructions
├── INTERVIEW_GUIDE.md             # System Design & Architecture Interview Guide
├── STRUCTURE.md                   # Complete Folder & File Documentation Catalog
├── package.json                   # Electron Dependencies & electron-builder Config
├── ospilot.db                     # Production SQLite Database (WAL Mode)
│
├── electron/                      # Electron Desktop Application Layer
│   └── main.js                    # Electron Main Process, Window Management, IPC & FastAPI Spawner
│
├── frontend/                      # User Interface Layer (HTML5, Vanilla CSS, JS)
│   ├── index.html                 # 7-Page Desktop App Layout, Sidebar Nav, Modals, Toasts
│   ├── style.css                  # Dark Glassmorphic CSS Design System & Theme Engine
│   └── renderer.js                # Frontend Controller, Theme Switcher, Streaming Reader, API Fetch
│
├── backend/                       # FastAPI Core Backend Engine
│   ├── requirements.txt           # Python Dependencies (FastAPI, LangGraph, FAISS, PyAutoGUI, Playwright)
│   ├── app/
│   │   ├── main.py                # FastAPI Application Factory & Global Exception Handlers
│   │   ├── api/                   # REST API Layer
│   │   │   └── v1/
│   │   │       ├── router.py      # Main API v1 Router Registering All Sub-routers
│   │   │       ├── health.py      # Service Health & System Resource Metrics Endpoints
│   │   │       ├── chat.py        # LLM Chat & SSE Real-time Streaming Response Endpoints
│   │   │       ├── search.py      # Semantic Search & File Indexing Endpoints
│   │   │       ├── rag.py         # Document Indexing & RAG Q&A Endpoints
│   │   │       ├── automation.py  # Desktop Control & Confirmation Endpoints
│   │   │       ├── browser.py     # Playwright Web Search & Agent Endpoints
│   │   │       ├── coding.py      # AI Coding Assistant Endpoints
│   │   │       ├── agents.py      # LangGraph Multi-Agent Execution & State Endpoints
│   │   │       └── memory.py      # Memory System Facts, History, Preferences Endpoints
│   │   ├── core/
│   │   │   ├── config.py          # Application Settings, Paths, Environment Config
│   │   │   └── logger.py          # RotatingFileHandler Structured Logger
│   │   ├── db/
│   │   │   ├── base.py            # SQLAlchemy Declarative Base
│   │   │   ├── session.py         # Database Engine with SQLite WAL Journal Mode
│   │   │   └── models.py          # ORM Models (FileDocument, ConversationHistory, UserPreference, etc.)
│   │   ├── domain/
│   │   │   └── schemas.py         # Pydantic Request & Response Data Transfer Objects
│   │   └── services/              # Business Logic & Service Modules
│   │       ├── ollama_service.py              # Ollama LLM Connection & Fallback Synthesis
│   │       ├── embedding_service.py           # Nomic Text Embeddings Generation
│   │       ├── faiss_service.py               # FAISS Vector Database Index Management
│   │       ├── document_loader.py             # PDF, DOCX, TXT, MD File Text Extractor
│   │       ├── rag_service.py                 # RAG Pipeline Document Assistant
│   │       ├── semantic_search_service.py     # File Semantic Search Engine
│   │       ├── desktop_automation_service.py  # PyAutoGUI & PyWinAuto OS Controls
│   │       ├── browser_automation_service.py  # Playwright Chrome/Edge Web Controls
│   │       ├── browser_agent.py               # Multi-step Autonomous Web Search Agent
│   │       ├── coding_assistant_service.py    # AI Coding Engine (Explain, Generate, Debug)
│   │       ├── multi_agent_service.py         # LangGraph StateGraph Multi-Agent Orchestrator
│   │       └── memory_system_service.py       # Multi-Tier Memory System Engine
│   └── tests/                     # Backend Automated Unit Test Suite
│       ├── test_health.py         # Health Endpoint Unit Tests
│       ├── test_chat.py           # Chat Endpoint Unit Tests
│       ├── test_chat_stream.py    # SSE Chat Streaming & System Metrics Unit Tests
│       ├── test_search.py         # Semantic Search Unit Tests
│       ├── test_rag.py            # RAG Document Assistant Unit Tests
│       ├── test_automation.py     # Desktop Automation Safety Unit Tests
│       ├── test_browser.py        # Playwright Browser Agent Unit Tests
│       ├── test_coding.py         # AI Coding Assistant Unit Tests
│       ├── test_multi_agent.py    # LangGraph Multi-Agent Workflow Unit Tests
│       └── test_memory_system.py  # Memory System Tiers Unit Tests
└── data/                          # Data Directories
    └── logs/
        └── ospilot.log            # Production Rotating Application Log File
```
