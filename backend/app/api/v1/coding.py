from fastapi import APIRouter, HTTPException
from app.domain.schemas import (
    ReadProjectRequest, ReadProjectResponse,
    ReadFileContentRequest, ReadFileContentResponse,
    ExplainCodeRequest, ExplainCodeResponse,
    GenerateCodeRequest, GenerateCodeResponse,
    DebugCodeRequest, DebugCodeResponse,
    SuggestImprovementsRequest, SuggestImprovementsResponse,
    GenerateDocsRequest, GenerateDocsResponse,
    RepoQuestionRequest, RepoQuestionResponse
)
from app.services.coding_assistant_service import coding_assistant_service

router = APIRouter(prefix="/coding", tags=["AI Coding Assistant"])


@router.post("/read-project", response_model=ReadProjectResponse)
def read_project(request: ReadProjectRequest) -> ReadProjectResponse:
    """Scans local project repository directory, collects file tree, and generates summary context."""
    try:
        res = coding_assistant_service.read_project(
            project_path=request.project_path,
            max_files=request.max_files
        )
        return ReadProjectResponse(**res)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/read-file", response_model=ReadFileContentResponse)
def read_file_content(request: ReadFileContentRequest) -> ReadFileContentResponse:
    """Reads raw text content of a file for local preview."""
    try:
        res = coding_assistant_service.read_file_content(
            project_path=request.project_path,
            filepath=request.filepath
        )
        return ReadFileContentResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/explain", response_model=ExplainCodeResponse)
def explain_code(request: ExplainCodeRequest) -> ExplainCodeResponse:
    """Provides clear explanation, logic breakdown, and function roles for a code snippet."""
    try:
        res = coding_assistant_service.explain_code(
            code_snippet=request.code_snippet,
            filepath=request.filepath,
            language=request.language
        )
        return ExplainCodeResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateCodeResponse)
def generate_code(request: GenerateCodeRequest) -> GenerateCodeResponse:
    """Generates production-ready code snippets or modules adhering to specification."""
    try:
        res = coding_assistant_service.generate_code(
            prompt=request.prompt,
            language=request.language,
            context=request.context
        )
        return GenerateCodeResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug", response_model=DebugCodeResponse)
def debug_code(request: DebugCodeRequest) -> DebugCodeResponse:
    """Diagnoses runtime errors and stack traces, identifies root cause, and generates fixed code."""
    try:
        res = coding_assistant_service.debug_code(
            code_snippet=request.code_snippet,
            error_log=request.error_log,
            language=request.language
        )
        return DebugCodeResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-improvements", response_model=SuggestImprovementsResponse)
def suggest_improvements(request: SuggestImprovementsRequest) -> SuggestImprovementsResponse:
    """Evaluates code quality, performance, security, and returns refactored optimized code."""
    try:
        res = coding_assistant_service.suggest_improvements(
            code_snippet=request.code_snippet,
            aspect=request.aspect,
            language=request.language
        )
        return SuggestImprovementsResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-docs", response_model=GenerateDocsResponse)
def generate_docs(request: GenerateDocsRequest) -> GenerateDocsResponse:
    """Generates docstrings, JSDoc, Markdown API specifications, or README content for code."""
    try:
        res = coding_assistant_service.generate_documentation(
            code_snippet=request.code_snippet,
            doc_format=request.doc_format,
            filepath=request.filepath
        )
        return GenerateDocsResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repo-question", response_model=RepoQuestionResponse)
def answer_repo_question(request: RepoQuestionRequest) -> RepoQuestionResponse:
    """Answers natural language questions about the codebase grounded in project code structure."""
    try:
        res = coding_assistant_service.answer_repo_question(
            question=request.question,
            project_path=request.project_path
        )
        return RepoQuestionResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
