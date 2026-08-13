from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class HealthStatus(BaseModel):
    status: str = Field(..., description="API operational status ('ok', 'degraded', 'error')")
    db_connected: bool = Field(..., description="Whether SQLite database connection is active")
    details: Dict[str, Any] = Field(default={}, description="System metadata and environment details")

class ChatMessageItem(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")

class ChatRequest(BaseModel):
    prompt: Optional[str] = Field(default=None, description="User chat prompt or instruction")
    messages: Optional[List[ChatMessageItem]] = Field(default=None, description="Multi-turn conversation history")
    model: Optional[str] = Field(default="gemma3:latest", description="Ollama LLM model name")
    system_prompt: Optional[str] = Field(default=None, description="Optional system prompt context")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Sampling temperature")

class ChatResponse(BaseModel):
    model: str = Field(..., description="LLM model used for completion")
    content: str = Field(..., description="Generated message response")
    execution_time_ms: float = Field(..., description="Response latency in milliseconds")



class IndexFolderRequest(BaseModel):
    folder_path: str = Field(default="ALL_DRIVES", description="Absolute directory path or 'ALL_DRIVES'")
    recursive: bool = Field(default=True, description="Whether to scan subdirectories recursively")
    clear_existing: bool = Field(default=False, description="Whether to clear previous index before indexing")

class IndexFolderResponse(BaseModel):
    folder_path: str = Field(..., description="Indexed directory path")
    files_found: int = Field(..., description="Total files discovered during scanning")
    files_scanned: int = Field(default=0, description="Total files scanned")
    chunks_indexed: int = Field(..., description="Total new text chunks embedded and indexed in FAISS")
    skipped_unchanged: int = Field(default=0, description="Files skipped because unchanged")
    total_indexed_in_db: int = Field(default=0, description="Total vectors/files in DB index")
    execution_time_ms: float = Field(..., description="Indexing duration in milliseconds")

class SearchQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language search query e.g. 'Find my Java resume'")
    folder_path: Optional[str] = Field(default=None, description="Optional folder path to filter search results")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top matching documents to return")

class SearchResultItem(BaseModel):
    filename: str = Field(..., description="Name of matching file")
    score: float = Field(..., description="Similarity confidence score (higher is better, range [0, 1])")
    location: str = Field(..., description="Absolute file path location")
    file_type: str = Field(..., description="File extension / category")
    snippet: str = Field(..., description="Matched text snippet context")

class SearchQueryResponse(BaseModel):
    query: str = Field(..., description="Natural language query string")
    results: List[SearchResultItem] = Field(default=[], description="Ranked search results")
    total_found: int = Field(..., description="Count of matched items")
    execution_time_ms: float = Field(..., description="Search duration in milliseconds")


# --- RAG Document Assistant Schemas ---

class RAGIndexRequest(BaseModel):
    filepath: str = Field(..., description="Absolute file path of document (PDF, DOCX, TXT, MD) to index")

class RAGIndexResponse(BaseModel):
    filepath: str = Field(..., description="Indexed document file path")
    filename: str = Field(..., description="Document filename")
    file_extension: str = Field(..., description="Document file extension")
    chunks_indexed: int = Field(..., description="Total text chunks embedded in FAISS")
    execution_time_ms: float = Field(..., description="Indexing duration in milliseconds")

class RAGSummarizeRequest(BaseModel):
    filepath: Optional[str] = Field(default=None, description="Absolute file path of document to summarize")
    filename: Optional[str] = Field(default=None, description="Filename of indexed document to summarize")

class RAGSummarizeResponse(BaseModel):
    filename: str = Field(..., description="Summarized document filename")
    filepath: str = Field(..., description="Summarized document absolute path")
    total_chunks: int = Field(..., description="Total chunks evaluated")
    summary: str = Field(..., description="Generated Markdown document summary")
    model_used: str = Field(..., description="Ollama LLM model used")
    execution_time_ms: float = Field(..., description="Summarization duration in milliseconds")

class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="Question or prompt (e.g. 'Summarize this document', 'Explain section 4', 'What is the conclusion?')")
    filepath: Optional[str] = Field(default=None, description="Optional target document file path")
    filename: Optional[str] = Field(default=None, description="Optional target document filename")
    top_k: int = Field(default=5, ge=1, le=20, description="Top matching context chunks to retrieve")
    model: Optional[str] = Field(default=None, description="Optional target LLM model name")

class RAGSourceItem(BaseModel):
    filename: str = Field(..., description="Source document filename")
    filepath: str = Field(..., description="Source document path")
    section_title: Optional[str] = Field(default=None, description="Matched section title")
    page_number: Optional[int] = Field(default=None, description="Matched page number")
    score: float = Field(..., description="Similarity confidence score")
    snippet: str = Field(..., description="Content snippet")

class RAGQueryResponse(BaseModel):
    query: str = Field(..., description="User query prompt")
    answer: str = Field(..., description="Grounded AI response")
    model_used: str = Field(..., description="Ollama LLM model used")
    sources: List[RAGSourceItem] = Field(default=[], description="Retrieved source chunks")
    execution_time_ms: float = Field(..., description="Query duration in milliseconds")


# --- Desktop Automation Schemas ---

class AppOpenRequest(BaseModel):
    app_name_or_path: str = Field(..., description="Name or executable path of application (e.g. 'notepad', 'calc', 'C:/app.exe')")

class AppCloseRequest(BaseModel):
    app_name: str = Field(..., description="Application name or process executable (e.g. 'notepad.exe', 'calculator')")
    confirmed: bool = Field(default=False, description="Mandatory explicit confirmation for closing applications")
    password: Optional[str] = Field(default=None, description="Laptop/system password for security confirmation")

class CreateFolderRequest(BaseModel):
    folder_path: Optional[str] = Field(default=None, description="Absolute or relative target directory path to create")
    parent_path: Optional[str] = Field(default=None, description="Parent folder location path")
    folder_name: Optional[str] = Field(default=None, description="New directory name to create inside parent_path")

class RenameFileRequest(BaseModel):
    source_path: str = Field(..., description="Path of existing file or folder")
    new_name_or_path: str = Field(..., description="New file/folder name or target destination path")

class MoveFileRequest(BaseModel):
    source_path: str = Field(..., description="Source file or folder path to move")
    destination_path: str = Field(..., description="Destination target file or folder path")

class DeleteFileRequest(BaseModel):
    file_path: str = Field(..., description="Target file or directory path to delete")
    confirmed: bool = Field(default=False, description="Mandatory explicit confirmation for file/folder deletion")
    password: Optional[str] = Field(default=None, description="Laptop/system password for security confirmation")

class OpenBrowserRequest(BaseModel):
    url: str = Field(..., description="URL website destination (e.g. 'google.com', 'https://github.com')")

class VolumeControlRequest(BaseModel):
    action: str = Field(..., description="Volume action: 'mute', 'unmute', 'set', 'up', 'down'")
    level: Optional[int] = Field(default=None, ge=0, le=100, description="Target percentage level (0-100) when action is 'set'")

class ClipboardSetRequest(BaseModel):
    text: str = Field(..., description="Text content to store in system clipboard")

class PowerStateRequest(BaseModel):
    confirmed: bool = Field(default=False, description="Mandatory explicit confirmation for system power state changes")
    delay_seconds: int = Field(default=10, ge=0, le=300, description="Delay before executing power command in seconds")
    password: Optional[str] = Field(default=None, description="Laptop/system password for security confirmation")

class AutomationActionResult(BaseModel):
    status: str = Field(..., description="Execution status ('success', 'confirmation_required', 'completed', 'error')")
    action: str = Field(..., description="Action name")
    requires_confirmation: Optional[bool] = Field(default=None, description="Set to true if action was blocked pending user confirmation")
    warning: Optional[str] = Field(default=None, description="Warning prompt when confirmation is needed")
    details: Dict[str, Any] = Field(default={}, description="Additional action metadata and results")

class VoiceCommandRequest(BaseModel):
    command: str = Field(..., description="Spoken voice command instruction e.g. 'Open Google Chrome', 'Set Laptop Volume to 45'")

class VoiceAudioRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded WAV audio captured from microphone")

class VoiceCommandResponse(BaseModel):
    command: str = Field(..., description="Spoken command text")
    status: str = Field(..., description="Execution status ('success', 'confirmation_required', 'error')")
    action: str = Field(..., description="Executed desktop action")
    response_text: str = Field(..., description="Human-friendly voice feedback message")
    requires_confirmation: Optional[bool] = Field(default=None)
    details: Dict[str, Any] = Field(default={})


# --- Browser Automation & Browser Agent Schemas ---

class BrowserNavRequest(BaseModel):
    url: str = Field(..., description="Target website URL to open")
    browser: str = Field(default="chrome", description="Browser engine: 'chrome' (Google Chrome), 'msedge' (Microsoft Edge), 'chromium'")
    headless: bool = Field(default=True, description="Whether to run browser in headless background mode")

class GoogleSearchRequest(BaseModel):
    query: str = Field(..., description="Search query prompt for Google")
    browser: str = Field(default="chrome", description="Browser engine ('chrome', 'msedge')")
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")

class YouTubeSearchRequest(BaseModel):
    query: str = Field(..., description="Video search query for YouTube")
    browser: str = Field(default="chrome", description="Browser engine ('chrome', 'msedge')")
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")

class PortalRequest(BaseModel):
    target: Optional[str] = Field(default=None, description="Repository/User profile for GitHub or Profile name for LinkedIn")
    browser: str = Field(default="chrome", description="Browser engine ('chrome', 'msedge')")
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")

class FormFillRequest(BaseModel):
    url: str = Field(..., description="Target web page containing form")
    form_data: Dict[str, str] = Field(..., description="Key-value mapping of form field names/selectors and input values")
    submit_selector: Optional[str] = Field(default=None, description="Optional CSS selector of submit button to click after filling")
    browser: str = Field(default="chrome", description="Browser engine ('chrome', 'msedge')")
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")

class ButtonClickRequest(BaseModel):
    url: str = Field(..., description="Target web page URL")
    selector_or_text: str = Field(..., description="CSS selector or visible text content of element to click")
    browser: str = Field(default="chrome", description="Browser engine ('chrome', 'msedge')")
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")

class DownloadFileRequest(BaseModel):
    url: str = Field(..., description="Target web page containing download link/button")
    download_selector: str = Field(..., description="CSS selector or text content of download button/link")
    save_dir: Optional[str] = Field(default=None, description="Optional custom directory path to save downloaded file")
    browser: str = Field(default="chrome", description="Browser engine ('chrome', 'msedge')")
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")

class BrowserAgentTaskRequest(BaseModel):
    task: str = Field(..., description="Natural language multi-step browser task (e.g. 'Search YouTube for Python RAG tutorials')")
    browser: str = Field(default="chrome", description="Browser engine ('chrome', 'msedge')")
    headless: bool = Field(default=True, description="Whether to run browser in headless mode")

class BrowserActionResult(BaseModel):
    status: str = Field(..., description="Execution status ('success', 'error')")
    action: str = Field(..., description="Action name")
    data: Dict[str, Any] = Field(default={}, description="Result payload")


# --- AI Coding Assistant Schemas ---

class ReadProjectRequest(BaseModel):
    project_path: str = Field(..., description="Absolute directory path of the project codebase to scan")
    max_files: int = Field(default=50, ge=1, le=500, description="Maximum files to scan")

class ReadProjectResponse(BaseModel):
    project_path: str = Field(..., description="Absolute project path")
    total_files: int = Field(..., description="Total code files scanned")
    file_types: Dict[str, int] = Field(default={}, description="Breakdown of files by extension")
    summary: str = Field(..., description="Generated repository context summary")
    file_tree: List[str] = Field(default=[], description="List of scanned relative file paths")
    execution_time_ms: float = Field(..., description="Scan duration in milliseconds")

class ReadFileContentRequest(BaseModel):
    project_path: str = Field(..., description="Root project path")
    filepath: str = Field(..., description="Relative or full file path to read")

class ReadFileContentResponse(BaseModel):
    filepath: str = Field(..., description="File path")
    full_path: str = Field(..., description="Absolute file path")
    content: str = Field(..., description="Raw text contents of the file")
    size_bytes: int = Field(..., description="File size in bytes")
    lines_count: int = Field(default=0, description="Total line count")
    status: str = Field(..., description="Reading status")

class ExplainCodeRequest(BaseModel):
    code_snippet: str = Field(..., description="Code snippet to explain")
    filepath: Optional[str] = Field(default=None, description="Optional filepath context")
    language: Optional[str] = Field(default="python", description="Programming language")

class ExplainCodeResponse(BaseModel):
    language: str = Field(..., description="Programming language")
    explanation: str = Field(..., description="Generated Markdown explanation")
    model_used: str = Field(..., description="LLM model used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")

class GenerateCodeRequest(BaseModel):
    prompt: str = Field(..., description="Code generation instruction or specification")
    language: str = Field(default="python", description="Target programming language")
    context: Optional[str] = Field(default=None, description="Optional codebase context snippet")

class GenerateCodeResponse(BaseModel):
    language: str = Field(..., description="Target programming language")
    generated_code: str = Field(..., description="Generated code snippet or module")
    model_used: str = Field(..., description="LLM model used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")

class DebugCodeRequest(BaseModel):
    code_snippet: str = Field(..., description="Buggy or failing code snippet")
    error_log: Optional[str] = Field(default=None, description="Error log or stack trace")
    language: str = Field(default="python", description="Programming language")

class DebugCodeResponse(BaseModel):
    language: str = Field(..., description="Programming language")
    diagnosis: str = Field(..., description="Root cause diagnosis explanation")
    fixed_code: str = Field(..., description="Corrected production-ready code")
    model_used: str = Field(..., description="LLM model used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")

class SuggestImprovementsRequest(BaseModel):
    code_snippet: str = Field(..., description="Code snippet to refactor or optimize")
    aspect: str = Field(default="all", description="Aspect: 'all', 'performance', 'security', 'readability', 'refactor'")
    language: str = Field(default="python", description="Programming language")

class SuggestImprovementsResponse(BaseModel):
    language: str = Field(..., description="Programming language")
    aspect: str = Field(..., description="Improvement aspect")
    suggestions: str = Field(..., description="Markdown review & optimization recommendations")
    improved_code: str = Field(..., description="Optimized refactored code")
    model_used: str = Field(..., description="LLM model used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")

class GenerateDocsRequest(BaseModel):
    code_snippet: str = Field(..., description="Code snippet or module to document")
    doc_format: str = Field(default="docstring", description="Doc format: 'docstring', 'markdown', 'readme'")
    filepath: Optional[str] = Field(default=None, description="Optional filepath context")

class GenerateDocsResponse(BaseModel):
    doc_format: str = Field(..., description="Requested documentation format")
    documentation: str = Field(..., description="Generated documentation text/markdown")
    model_used: str = Field(..., description="LLM model used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")

class RepoQuestionRequest(BaseModel):
    question: str = Field(..., description="Question about the codebase (e.g. 'How is authentication handled?')")
    project_path: Optional[str] = Field(default=None, description="Optional project directory path")

class RepoQuestionResponse(BaseModel):
    question: str = Field(..., description="User repository question")
    answer: str = Field(..., description="Grounded AI answer")
    relevant_files: List[str] = Field(default=[], description="Relevant codebase files evaluated")
    model_used: str = Field(..., description="LLM model used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


# --- LangGraph Multi-Agent Architecture Schemas ---

class MultiAgentExecuteRequest(BaseModel):
    user_request: str = Field(..., description="User prompt or task for multi-agent system")
    session_id: Optional[str] = Field(default="default-session", description="Session identifier for state retention")
    parallel_mode: bool = Field(default=True, description="Enable parallel execution for independent agent tasks")
    model: Optional[str] = Field(default="gemma3:latest", description="LLM model to use")

class MultiAgentExecuteResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    plan: str = Field(..., description="Generated execution plan by Planner Agent")
    agents_invoked: List[str] = Field(..., description="List of agent nodes executed")
    agent_results: Dict[str, Any] = Field(default={}, description="Outputs produced by each agent")
    final_response: str = Field(..., description="Synthesized final answer")
    error_recovery_applied: bool = Field(default=False, description="Whether error recovery fallback was triggered")
    logs: List[str] = Field(default=[], description="Execution trace logs")
    execution_time_ms: float = Field(..., description="Total graph execution time in milliseconds")

class AgentStateResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    conversation_history: List[Dict[str, str]] = Field(default=[], description="State conversation history")
    last_plan: Optional[str] = Field(default=None, description="Last plan formulated")
    execution_count: int = Field(default=0, description="Total agent graph executions in this session")


# --- Memory System Schemas ---

class RememberFactRequest(BaseModel):
    fact: str = Field(..., description="Fact or instruction to remember (e.g. 'Remember this: my preferred browser is Chrome')")
    category: Optional[str] = Field(default="general", description="Category label")

class RememberFactResponse(BaseModel):
    status: str = Field(..., description="Status ('stored')")
    memory_key: str = Field(..., description="Unique memory key")
    fact: str = Field(..., description="Stored fact text")
    vector_indexed: bool = Field(..., description="Whether indexed in FAISS vector memory")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")

class QueryMemoryRequest(BaseModel):
    query: str = Field(..., description="Natural language memory query (e.g. 'What did I ask yesterday?' or 'What is my preferred browser?')")
    session_id: Optional[str] = Field(default="default-session", description="Session identifier")

class QueryMemoryResponse(BaseModel):
    query: str = Field(..., description="User memory query")
    answer: str = Field(..., description="Retrieved memory answer")
    matched_facts: List[str] = Field(default=[], description="Relevant facts from long-term memory")
    history_matches: List[Dict[str, Any]] = Field(default=[], description="Relevant conversation history matches")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")

class SetPreferenceRequest(BaseModel):
    key: str = Field(..., description="Preference key (e.g. 'theme', 'default_model')")
    value: str = Field(..., description="Preference value")

class GetPreferencesResponse(BaseModel):
    preferences: Dict[str, str] = Field(default={}, description="Key-value user preferences map")

class TaskHistoryItem(BaseModel):
    id: int
    session_id: Optional[str]
    action: str
    status: str
    details: Optional[str]
    created_at: str

class GetTaskHistoryResponse(BaseModel):
    tasks: List[TaskHistoryItem] = Field(default=[], description="Logged task execution history")





