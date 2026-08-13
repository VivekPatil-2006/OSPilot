import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and add header/footer on each page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Suppress headers/footers on cover page
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#2563EB"))
            self.drawString(54, 11 * inch - 36, "OSPilot — Complete Beginner's & Interview Handbook")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

            # Footer
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(54, 36, "100% Offline AI Desktop Assistant | Student & Interview Quick Prep")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(8.5 * inch - 54, 36, page_text)
            self.line(54, 46, 8.5 * inch - 54, 46)
            
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#1E3A8A")    # Deep Navy
    SECONDARY = colors.HexColor("#2563EB")  # Electric Blue
    ACCENT = colors.HexColor("#0D9488")     # Teal Accent
    DARK_BG = colors.HexColor("#0F172A")    # Dark Slate
    LIGHT_BG = colors.HexColor("#F8FAFC")   # Soft Off-white
    BORDER = colors.HexColor("#CBD5E1")     # Light Gray Border
    TEXT_DARK = colors.HexColor("#1E293B")  # Charcoal Body Text

    # Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=PRIMARY,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=17,
        textColor=SECONDARY,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    q_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=PRIMARY,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    a_style = ParagraphStyle(
        'AnswerStyle',
        parent=body_style,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )

    elements = []

    # ==================== COVER PAGE ====================
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("OSPilot: Offline Desktop AI Assistant", title_style))
    elements.append(Paragraph("Complete Beginner's Guide & Interview Handbook", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2.5, color=SECONDARY, spaceAfter=15))
    
    cover_desc = (
        "<b>OSPilot</b> is a production-quality, 100% local, offline AI Desktop Assistant engineered with an "
        "Electron frontend, Python FastAPI backend, local Ollama LLMs (<i>Qwen3 / Gemma3 / Qwen2.5-Coder</i>), "
        "FAISS Vector RAG pipeline, LangGraph Multi-Agent Architecture, AI Coding Assistant, Desktop/Browser Automation, "
        "and a Multi-Tier Memory System. Zero cloud dependencies."
    )
    elements.append(Paragraph(cover_desc, body_style))
    elements.append(Spacer(1, 10))

    # Highlights Table
    card_data = [
        [
            Paragraph("<b>🎯 What is OSPilot?</b><br/>An offline AI assistant running on your PC that controls apps, searches local files, writes code, and remembers past interactions.", body_style),
            Paragraph("<b>⚡ Technology Stack</b><br/>Electron (Frontend UI), FastAPI (Python Backend), Local Ollama LLM, FAISS & SQLite (RAG Engine).", body_style)
        ],
        [
            Paragraph("<b>🛡️ Zero Cloud Privacy</b><br/>All processing stays on your device. No user data, files, or prompt text ever leave your computer.", body_style),
            Paragraph("<b>🔒 Action Safety</b><br/>Destructive commands (deleting files, shutting down, closing apps) require interactive user popup confirmation.", body_style)
        ]
    ]
    card_table = Table(card_data, colWidths=[240, 240])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(card_table)
    elements.append(Spacer(1, 15))

    # Table of Contents Summary
    elements.append(Paragraph("<b>Handbook Navigation / Table of Contents</b>", h2_style))
    toc_text = (
        "<b>1. Project Overview & Elevator Pitch</b> — Simple 30-second explanation for recruiters<br/>"
        "<b>2. Technology Stack & Key Libraries</b> — What each library does & why chosen<br/>"
        "<b>3. Folder Structure & Key Files</b> — Easy visual map of frontend, backend, and core modules<br/>"
        "<b>4. Core Subsystem Explanations</b> — RAG, LangGraph Multi-Agent, SSE Streaming & Memory Tiers<br/>"
        "<b>5. Step-by-Step Execution Data Flow</b> — End-to-end execution trace when a user types a prompt<br/>"
        "<b>6. Top 12 Interview Questions & Master Answers</b> — Beginner to Senior level interview Q&A<br/>"
        "<b>7. Quick Setup & Troubleshooting Cheat Sheet</b> — Essential terminal commands & error quick fixes"
    )
    elements.append(Paragraph(toc_text, body_style))
    elements.append(PageBreak())

    # ==================== SECTION 1 ====================
    elements.append(Paragraph("1. Project Overview & Elevator Pitch", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10))
    
    pitch_box = [
        [Paragraph("<b>🗣️ How to explain OSPilot in an interview (Elevator Pitch):</b>", h2_style)],
        [Paragraph(
            "<i>'OSPilot is an open-source, production-ready desktop AI assistant built with Electron and Python FastAPI. "
            "It runs entirely offline on the user's computer using local open-weight LLMs via Ollama. "
            "Unlike simple chatbots, OSPilot features a LangGraph multi-agent orchestrator that routes user requests to specialized nodes "
            "for file search (FAISS vector database), document Q&A (RAG), OS desktop control (PyAutoGUI), automated web browser search (Playwright), "
            "and AI code generation. It also implements token-by-token real-time streaming over SSE and a 4-tier memory system.'</i>",
            body_style
        )]
    ]
    t_pitch = Table(pitch_box, colWidths=[480])
    t_pitch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1, SECONDARY),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_pitch)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Key Value Propositions", h2_style))
    elements.append(Paragraph("• <b>100% Data Privacy & Security:</b> Zero API keys required for core features. Ideal for enterprise codebases and confidential docs.", bullet_style))
    elements.append(Paragraph("• <b>Sub-Second Real-Time UI:</b> Uses Server-Sent Events (SSE) for instant token streaming without visual lag.", bullet_style))
    elements.append(Paragraph("• <b>Resilient Offline Execution:</b> Automatically falls back across local LLM models (`qwen3:8b` -> `gemma3:latest` -> `qwen2.5-coder:7b`).", bullet_style))
    elements.append(Paragraph("• <b>Human-in-the-Loop Safety:</b> Dangerous computer commands (deleting files, shutting down) are trapped until the user confirms via dialog popup.", bullet_style))
    elements.append(Spacer(1, 12))

    # ==================== SECTION 2 ====================
    elements.append(Paragraph("2. Technology Stack Breakdown", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10))

    tech_headers = ["Layer", "Technology", "Role & Purpose"]
    tech_rows = [
        [Paragraph("<b>Frontend Desktop UI</b>", body_style), Paragraph("Electron + JavaScript + HTML5/CSS3", body_style), Paragraph("Renders desktop window, sidebar navigation, real-time SSE stream reader, and safety confirmation modals.", body_style)],
        [Paragraph("<b>Backend API Engine</b>", body_style), Paragraph("Python 3.10+ & FastAPI", body_style), Paragraph("High-performance asynchronous REST API handling endpoints, background tasks, and business services.", body_style)],
        [Paragraph("<b>Local LLM Server</b>", body_style), Paragraph("Ollama (`qwen3`, `gemma3`, `qwen2.5-coder`)", body_style), Paragraph("Serves local GGUF open-weights models with VRAM management and HTTP inference endpoint.", body_style)],
        [Paragraph("<b>Multi-Agent Framework</b>", body_style), Paragraph("LangGraph (`StateGraph`)", body_style), Paragraph("Orchestrates autonomous agent graphs: Planner, Retriever, Automation, Coding, & Memory nodes.", body_style)],
        [Paragraph("<b>Vector Search (RAG)</b>", body_style), Paragraph("FAISS + `nomic-embed-text`", body_style), Paragraph("Generates 768-dim vector embeddings and performs ultra-fast L2 similarity search over local documents.", body_style)],
        [Paragraph("<b>Metadata & Memory DB</b>", body_style), Paragraph("SQLite (Write-Ahead Logging WAL Mode)", body_style), Paragraph("Stores conversation history, file chunk references, explicit remembered facts, and settings.", body_style)],
        [Paragraph("<b>OS & Web Automation</b>", body_style), Paragraph("PyAutoGUI & Playwright", body_style), Paragraph("Simulates keyboard/mouse inputs for desktop control and executes automated browser searches.", body_style)],
    ]
    
    tech_table = Table([tech_headers] + tech_rows, colWidths=[100, 140, 240])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(tech_table)
    elements.append(PageBreak())

    # ==================== SECTION 3 ====================
    elements.append(Paragraph("3. Directory Structure & File Map", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10))

    elements.append(Paragraph("Understand where every single piece of logic resides in the workspace:", body_style))
    
    file_map_data = [
        ["File / Folder Path", "What it does (In simple words)"],
        ["electron/main.js", "Electron root process. Creates window, spawns Python FastAPI subprocess automatically, handles IPC."],
        ["frontend/index.html", "7-page single-page application (Chat, RAG, Coding, Automation, Memory, Settings, Logs)."],
        ["frontend/renderer.js", "Frontend logic. Handles UI tabs, fetch requests, theme toggles, SSE stream parsing."],
        ["backend/app/main.py", "FastAPI entrypoint. Registers router, CORS middleware, global error handlers."],
        ["backend/app/api/v1/router.py", "Central router aggregating chat, search, rag, automation, browser, coding, agent, memory routes."],
        ["backend/app/core/config.py", "Application configuration (Ollama URL, model defaults, DB paths)."],
        ["backend/app/db/session.py", "SQLite database engine hardened with PRAGMA journal_mode=WAL for 10x faster concurrent access."],
        ["backend/app/services/ollama_service.py", "Manages HTTP connection to Ollama LLM with intelligent model fallback retry chain."],
        ["backend/app/services/multi_agent_service.py", "LangGraph StateGraph workflow organizing Planner, Retriever, Coding, Automation, & Memory nodes."],
        ["backend/app/services/rag_service.py", "RAG pipeline. Reads PDF/DOCX/TXT/MD, chunks text, generates embeddings, stores in FAISS."],
        ["backend/app/services/desktop_automation_service.py", "Controls OS desktop (launching apps, volume, screenshots, file operations). Requires safety confirmation."],
        ["backend/app/services/memory_system_service.py", "Manages 4 memory tiers: Short-term cache, Long-term vector facts, History, & User Preferences."]
    ]
    
    t_file = Table([[Paragraph(f"<b>{c}</b>", body_style) for c in row] if i==0 else [Paragraph(row[0], code_style), Paragraph(row[1], body_style)] for i, row in enumerate(file_map_data)], colWidths=[170, 310])
    t_file.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_file)
    elements.append(Spacer(1, 12))

    # ==================== SECTION 4 ====================
    elements.append(Paragraph("4. Core Subsystem Explanations", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10))

    elements.append(Paragraph("A. RAG (Retrieval-Augmented Generation) Pipeline", h2_style))
    elements.append(Paragraph(
        "<b>What is RAG?</b> Standard LLMs don't know your private personal files. RAG injects relevant text snippets from your files into the LLM prompt.<br/>"
        "<b>1. Document Loading:</b> <code>document_loader.py</code> extracts plain text from PDF, DOCX, TXT, and Markdown files.<br/>"
        "<b>2. Text Chunking:</b> Large text is broken into 500-character chunks with 50-character overlaps.<br/>"
        "<b>3. Vector Embeddings:</b> <code>embedding_service.py</code> converts each chunk into a 768-dimensional numerical vector using <code>nomic-embed-text</code>.<br/>"
        "<b>4. FAISS Indexing:</b> <code>faiss_service.py</code> saves vectors in FAISS index for ultra-fast L2 distance similarity matching.<br/>"
        "<b>5. Retrieval Q&A:</b> When you ask a question, your query is embedded, top 5 matching chunks are fetched, and passed to Ollama to answer.",
        body_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("B. LangGraph Multi-Agent Architecture", h2_style))
    elements.append(Paragraph(
        "Instead of asking one LLM to do everything, OSPilot breaks complex queries into a graph of specialized nodes:<br/>"
        "• <b>Planner Node:</b> Decides user intent and selects target worker agents.<br/>"
        "• <b>Retriever Node:</b> Searches local documents and vector memory.<br/>"
        "• <b>Coding Node:</b> Explains, debugs, or writes code modules.<br/>"
        "• <b>Automation Node:</b> Prepares PyAutoGUI or Playwright actions.<br/>"
        "• <b>Synthesizer Node:</b> Combines outputs into a unified answer and handles error retries.",
        body_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("C. Real-Time Token Streaming (SSE)", h2_style))
    elements.append(Paragraph(
        "<b>Server-Sent Events (SSE):</b> Fast HTTP streaming endpoint (<code>POST /api/v1/chat/stream</code>). "
        "FastAPI yields <code>data: {\"token\": \"Hello\"}</code> chunks. "
        "The Electron UI uses JavaScript's <code>fetch()</code> with <code>ReadableStream</code> reader to display tokens word-by-word instantly.",
        body_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("D. Multi-Tier Memory Architecture", h2_style))
    elements.append(Paragraph(
        "1. <b>Short-Term Memory:</b> Active conversation window (LRU cache).<br/>"
        "2. <b>Long-Term Fact Store:</b> Explicit user facts stored in SQLite & FAISS vector memory.<br/>"
        "3. <b>Conversation History:</b> Searchable database of past dialogue turns.<br/>"
        "4. <b>User Preferences:</b> Key-value settings stored in SQLite.",
        body_style
    ))
    elements.append(PageBreak())

    # ==================== SECTION 5 ====================
    elements.append(Paragraph("5. Step-by-Step Execution Data Flow", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10))

    elements.append(Paragraph("What happens under the hood when a user types a prompt in OSPilot?", body_style))
    
    flow_steps = [
        ("Step 1: UI Input", "User types a prompt in Electron frontend and clicks 'Send' or presses Enter."),
        ("Step 2: HTTP Request", "<code>renderer.js</code> sends an HTTP POST request to FastAPI backend (<code>http://127.0.0.1:8000/api/v1/chat/stream</code>)."),
        ("Step 3: Route Handling", "<code>chat.py</code> receives request, extracts prompt, and loads session memory context."),
        ("Step 4: LLM Connection", "<code>ollama_service.py</code> formats prompt with system rules and sends stream request to Ollama on port 11434."),
        ("Step 5: SSE Streaming", "FastAPI yields SSE data stream chunks. <code>renderer.js</code> decodes stream bytes with <code>TextDecoder</code> and appends text to DOM token-by-token."),
        ("Step 6: History Persistence", "Once streaming finishes, full response is saved into SQLite <code>ConversationHistory</code> table.")
    ]

    flow_table_data = []
    for step, desc in flow_steps:
        flow_table_data.append([
            Paragraph(f"<b>{step}</b>", ParagraphStyle('StepTitle', parent=body_style, textColor=PRIMARY)),
            Paragraph(desc, body_style)
        ])

    t_flow = Table(flow_table_data, colWidths=[130, 350])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#EFF6FF")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_flow)
    elements.append(Spacer(1, 15))

    # ==================== SECTION 6 ====================
    elements.append(Paragraph("6. Top 12 Interview Questions & Master Answers", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10))

    qa_list = [
        (
            "Q1: What is OSPilot, and why did you build it as an offline desktop application?",
            "OSPilot is a 100% offline, privacy-first AI desktop assistant. It was built to solve corporate data exfiltration risks when developers and users handle proprietary code, financial documents, or personal data. By serving models locally via Ollama and using Electron + FastAPI, zero user data leaves the machine."
        ),
        (
            "Q2: Why did you choose FastAPI for the backend instead of Node.js express?",
            "FastAPI provides native asynchronous Python support (`async/await`), automatic OpenAPI documentation, high-performance SSE streaming, and direct integration with Python AI ecosystems like LangGraph, FAISS, PyAutoGUI, and Playwright without needing inter-process bridges."
        ),
        (
            "Q3: How does real-time streaming work between FastAPI and Electron?",
            "We implemented a token streaming endpoint using FastAPI's `StreamingResponse` yielding Server-Sent Events (SSE). On the frontend, `renderer.js` uses JavaScript's `fetch()` API with `ReadableStream` reader to decode byte streams and update the UI live token-by-token."
        ),
        (
            "Q4: How do you handle cold-start latency when Ollama loads LLM models into VRAM?",
            "Cold LLM models take 5-10 seconds to load into GPU VRAM. We configured 120-second HTTP client timeouts in `OllamaService` and implemented a fallback model chain (`qwen3:8b` -> `gemma3:latest` -> fallback synthesis) to ensure high system resilience."
        ),
        (
            "Q5: How does the RAG vector indexing pipeline work in OSPilot?",
            "Documents (PDF, DOCX, TXT, MD) are extracted via `document_loader.py`, split into 500-character chunks with 50-character overlap, converted into 768-dim embeddings via `nomic-embed-text`, and stored in FAISS vector index. SQLite stores text snippets and metadata mapped 1:1 to FAISS vector IDs."
        ),
        (
            "Q6: How did you optimize SQLite for high concurrent performance in a desktop app?",
            "We enabled Write-Ahead Logging (`PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;`) in `session.py`. This allows concurrent readers while a writer writes, eliminating database lock errors during streaming chat."
        ),
        (
            "Q7: How is desktop automation safety enforced for dangerous OS actions?",
            "Potentially destructive commands (deleting files, app termination, system shutdown/restart/sleep) require a `confirmed: true` flag. If false, the service returns `confirmation_required`. Electron catches this and displays an interactive modal dialog requiring explicit user approval."
        ),
        (
            "Q8: What is LangGraph and how is it used in OSPilot's Multi-Agent system?",
            "LangGraph is a framework for building stateful multi-agent workflows using graph nodes. In OSPilot, `multi_agent_service.py` defines a `StateGraph` with a Planner Node routing tasks to Retriever, Coding, Automation, and Memory nodes, ending at a Synthesizer node for error recovery."
        ),
        (
            "Q9: How does the AI Coding Assistant analyze and debug code?",
            "The Coding Assistant (`coding_assistant_service.py`) uses specialized system prompts tailored for `qwen2.5-coder:7b`. It can scan workspace project trees, explain logic, debug stack trace errors, refactor code, and generate docstrings."
        ),
        (
            "Q10: What is the 4-tier memory system in OSPilot?",
            "It consists of: 1) Short-Term Memory (active dialogue session cache), 2) Long-Term Memory (fact store saved in SQLite & FAISS vector space), 3) Conversation History (searchable database of past dialogue turns), and 4) User Preferences (key-value UI settings)."
        ),
        (
            "Q11: How does browser automation work in OSPilot?",
            "It uses Playwright (`browser_automation_service.py`) to launch headless or headed browser instances to execute web searches, navigate pages, extract text, click buttons, and fill web forms automatically."
        ),
        (
            "Q12: How do you package and deploy OSPilot for non-technical end-users?",
            "OSPilot uses `electron-builder` (`package.json`) to bundle the Electron frontend and Python environment into standalone Windows installers (`.exe` / NSIS) and portable executables."
        )
    ]

    for q, a in qa_list:
        elements.append(Paragraph(q, q_style))
        elements.append(Paragraph(a, a_style))

    elements.append(PageBreak())

    # ==================== SECTION 7 ====================
    elements.append(Paragraph("7. Quick Setup & Troubleshooting Cheat Sheet", h1_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10))

    elements.append(Paragraph("Essential Terminal Commands", h2_style))
    cmd_data = [
        ["Action / Goal", "Terminal Command"],
        ["1. Navigate to Project", "cd \"D:\\OS Pilot\""],
        ["2. Activate Python Virtual Env", ".\\venv\\Scripts\\Activate.ps1"],
        ["3. Install Python Dependencies", "pip install -r backend/requirements.txt"],
        ["4. Start Local Ollama Server", "ollama serve"],
        ["5. Pull Required Local LLM Model", "ollama pull qwen3:8b"],
        ["6. Run Backend Tests", "venv\\Scripts\\python.exe -m pytest backend/tests"],
        ["7. Launch Desktop Application", "npm start"]
    ]
    t_cmd = Table([[Paragraph(f"<b>{row[0]}</b>", body_style), Paragraph(f"<code>{row[1]}</code>", code_style)] for row in cmd_data], colWidths=[170, 310])
    t_cmd.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_cmd)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Common Interview Troubleshooting Scenarios", h2_style))
    trouble_data = [
        ["Symptom / Error", "Root Cause", "Quick Solution"],
        ["Ollama Connection Refused", "Ollama service is not running on localhost:11434.", "Run `ollama serve` in terminal."],
        ["HTTP 408 / Large Git Push Error", "Committed heavy node_modules or large FAISS binary files to Git.", "Add `node_modules/` and `*.bin` to `.gitignore` and run `git rm --cached`."],
        ["SQLite Database Locked Error", "Multiple database connection handles opening simultaneously.", "Ensure SQLite WAL mode `PRAGMA journal_mode=WAL;` is enabled in `session.py`."],
        ["Playwright Browser Launch Crash", "Chromium binaries are missing.", "Run `playwright install chromium` inside virtual environment."]
    ]
    t_trouble = Table([[Paragraph(f"<b>{c}</b>", body_style) for c in row] if i==0 else [Paragraph(row[0], body_style), Paragraph(row[1], body_style), Paragraph(row[2], body_style)] for i, row in enumerate(trouble_data)], colWidths=[130, 160, 190])
    t_trouble.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_trouble)
    elements.append(Spacer(1, 15))

    # Build PDF
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF at: {filename}")

if __name__ == '__main__':
    target_path = r"d:\OS Pilot\OSPilot - Complete Beginner's Guide & Interview Handbook.pdf"
    build_pdf(target_path)
