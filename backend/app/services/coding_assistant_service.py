import os
import time
import re
from typing import List, Dict, Any, Optional
from app.services.ollama_service import ollama_service
from app.core.logger import logger

class CodingAssistantService:
    """Service providing local offline AI Coding Assistant capabilities powered by Ollama.

    Features:
    - Read Project
    - Explain Code
    - Generate Code
    - Debug Code
    - Suggest Improvements
    - Generate Documentation
    - Answer Repository Questions
    """

    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json',
        '.md', '.sql', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.sh', '.ps1'
    }

    def read_project(self, project_path: str, max_files: int = 200, include_summary: bool = False) -> Dict[str, Any]:
        """Scans project repository directory, collects file structures, file types, and returns file tree instantly."""
        start_time = time.time()
        abs_path = os.path.abspath(project_path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Project directory '{project_path}' does not exist.")

        file_tree = []
        file_types = {}
        total_files = 0
        file_summaries = []

        ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__', '.pytest_cache', 'dist', 'build', '.idea', '.vscode'}

        for root, dirs, files in os.walk(abs_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                ext = os.path.splitext(file)[1].lower() or '.file'
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, abs_path).replace("\\", "/")

                file_tree.append(rel_p)
                file_types[ext] = file_types.get(ext, 0) + 1
                total_files += 1

                if len(file_summaries) < max_files:
                    try:
                        size = os.path.getsize(full_p)
                        file_summaries.append(f"- `{rel_p}` ({size} bytes)")
                    except Exception:
                        pass

        type_summary = ", ".join([f"{ext}: {count}" for ext, count in file_types.items()])
        summary = f"Scanned {total_files} files across directory '{os.path.basename(abs_path)}'. Types: {type_summary}."

        if include_summary:
            try:
                tree_preview = "\n".join(file_summaries[:25])
                prompt = (
                    f"Analyze this codebase structure:\n"
                    f"Root Path: {abs_path}\n"
                    f"Total Files Scanned: {total_files}\n"
                    f"File Types Breakdown: {type_summary}\n\n"
                    f"Top Repository Files:\n{tree_preview}\n\n"
                    f"Provide a 3-bullet point architectural overview summary of this repository."
                )
                llm_res = ollama_service.generate_response(
                    prompt=prompt,
                    model="qwen2.5-coder:7b",
                    system_prompt="You are a Senior Software Architect inspecting a project codebase."
                )
                summary = llm_res.get("content", summary)
            except Exception as e:
                logger.warning(f"Ollama architectural summary skipped: {e}")

        elapsed = round((time.time() - start_time) * 1000.0, 2)

        return {
            "project_path": abs_path,
            "total_files": total_files,
            "file_types": file_types,
            "summary": summary,
            "file_tree": file_tree,
            "execution_time_ms": elapsed
        }

    def read_file_content(self, project_path: str, filepath: str) -> Dict[str, Any]:
        """Reads raw text content of a target file inside a project directory."""
        abs_base = os.path.abspath(project_path)

        # Smart multi-stage path resolution
        if os.path.isabs(filepath) and os.path.exists(filepath):
            full_path = os.path.abspath(filepath)
        elif os.path.exists(os.path.join(abs_base, filepath)):
            full_path = os.path.abspath(os.path.join(abs_base, filepath))
        elif os.path.exists(filepath):
            full_path = os.path.abspath(filepath)
        else:
            # Fallback search inside abs_base
            target_name = os.path.basename(filepath)
            matched = None
            for root, _, files in os.walk(abs_base):
                if target_name in files:
                    candidate = os.path.join(root, target_name)
                    norm_cand = candidate.replace("\\", "/")
                    norm_fp = filepath.replace("\\", "/")
                    if norm_cand.endswith(norm_fp):
                        matched = candidate
                        break
                    elif not matched:
                        matched = candidate
            if matched and os.path.exists(matched):
                full_path = matched
            else:
                full_path = os.path.abspath(os.path.join(abs_base, filepath))

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise FileNotFoundError(f"File '{filepath}' not found at path '{full_path}'.")

        try:
            size = os.path.getsize(full_path)
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(100000)  # Read up to 100KB preview

            lines = content.count('\n') + 1 if content else 0
            return {
                "filepath": filepath,
                "full_path": full_path,
                "content": content if content else "[Empty File]",
                "size_bytes": size,
                "lines_count": lines,
                "status": "success"
            }
        except Exception as e:
            return {
                "filepath": filepath,
                "full_path": full_path,
                "content": f"Could not read file contents: {e}",
                "size_bytes": 0,
                "lines_count": 0,
                "status": "error"
            }

    def explain_code(self, code_snippet: str, filepath: Optional[str] = None, language: Optional[str] = "python") -> Dict[str, Any]:
        """Provides architectural explanation, logic flow, and function breakdowns for a code snippet."""
        start_time = time.time()
        file_ctx = f" (File: {filepath})" if filepath else ""

        prompt = (
            f"Explain the following {language} code snippet{file_ctx}:\n\n"
            f"```{language}\n{code_snippet}\n```\n\n"
            f"Provide:\n"
            f"1. Overall Purpose\n"
            f"2. Step-by-step logic breakdown\n"
            f"3. Key functions / algorithms used"
        )

        res = ollama_service.generate_response(
            prompt=prompt,
            model="qwen2.5-coder:7b",
            system_prompt="You are an expert AI Code Explainer and Technical Educator."
        )

        elapsed = round((time.time() - start_time) * 1000.0, 2)

        return {
            "language": language or "python",
            "explanation": res.get("content", "Code snippet explained successfully."),
            "model_used": res.get("model", "qwen2.5-coder:7b"),
            "execution_time_ms": elapsed
        }

    def generate_code(self, prompt: str, language: str = "python", context: Optional[str] = None) -> Dict[str, Any]:
        """Generates production-ready code snippets or modules adhering to specification."""
        start_time = time.time()
        ctx_block = f"\nContext:\n```{language}\n{context}\n```\n" if context else ""

        full_prompt = (
            f"Write clean, production-ready {language} code for the following request:\n"
            f"\"{prompt}\"\n{ctx_block}\n"
            f"Return ONLY valid code inside fenced code blocks ```{language} ... ``` with clear comments."
        )

        res = ollama_service.generate_response(
            prompt=full_prompt,
            model="qwen2.5-coder:7b",
            system_prompt=f"You are a Senior Principal Engineer writing high quality {language} code."
        )

        elapsed = round((time.time() - start_time) * 1000.0, 2)
        content = res.get("content", "")

        # Extract code block if wrapped in markdown
        code_match = re.search(rf'```{language}\n(.*?)```', content, re.DOTALL | re.IGNORECASE)
        if not code_match:
            code_match = re.search(r'```\n(.*?)```', content, re.DOTALL)
        
        extracted_code = code_match.group(1).strip() if code_match else content

        return {
            "language": language,
            "generated_code": extracted_code,
            "model_used": res.get("model", "qwen2.5-coder:7b"),
            "execution_time_ms": elapsed
        }

    def debug_code(self, code_snippet: str, error_log: Optional[str] = None, language: str = "python") -> Dict[str, Any]:
        """Diagnoses runtime errors and stack traces, identifies root cause, and generates fixed code."""
        start_time = time.time()
        err_block = f"\nError Traceback / Log:\n```\n{error_log}\n```\n" if error_log else ""

        prompt = (
            f"Debug the following {language} code snippet:\n"
            f"```{language}\n{code_snippet}\n```\n{err_block}\n"
            f"Identify:\n"
            f"1. **Root Cause Diagnosis**: Why the error occurs.\n"
            f"2. **Corrected Code**: Provide the full fixed code block in ```{language} ... ```."
        )

        res = ollama_service.generate_response(
            prompt=prompt,
            model="qwen2.5-coder:7b",
            system_prompt="You are an expert Automated Software Debugging System."
        )

        elapsed = round((time.time() - start_time) * 1000.0, 2)
        content = res.get("content", "")

        code_match = re.search(rf'```{language}\n(.*?)```', content, re.DOTALL | re.IGNORECASE)
        if not code_match:
            code_match = re.search(r'```\n(.*?)```', content, re.DOTALL)

        fixed_code = code_match.group(1).strip() if code_match else code_snippet

        return {
            "language": language,
            "diagnosis": content,
            "fixed_code": fixed_code,
            "model_used": res.get("model", "qwen2.5-coder:7b"),
            "execution_time_ms": elapsed
        }

    def suggest_improvements(self, code_snippet: str, aspect: str = "all", language: str = "python") -> Dict[str, Any]:
        """Evaluates code quality, performance, security, and returns refactored optimized code."""
        start_time = time.time()

        prompt = (
            f"Analyze and suggest code improvements for aspect '{aspect}' on this {language} code:\n"
            f"```{language}\n{code_snippet}\n```\n\n"
            f"Provide:\n"
            f"1. **Code Review & Recommendations** (Performance, Security, Clean Code)\n"
            f"2. **Refactored Code** in ```{language} ... ```."
        )

        res = ollama_service.generate_response(
            prompt=prompt,
            model="qwen2.5-coder:7b",
            system_prompt="You are a Lead Software Architect conducting code reviews and refactoring."
        )

        elapsed = round((time.time() - start_time) * 1000.0, 2)
        content = res.get("content", "")

        code_match = re.search(rf'```{language}\n(.*?)```', content, re.DOTALL | re.IGNORECASE)
        if not code_match:
            code_match = re.search(r'```\n(.*?)```', content, re.DOTALL)

        improved_code = code_match.group(1).strip() if code_match else code_snippet

        return {
            "language": language,
            "aspect": aspect,
            "suggestions": content,
            "improved_code": improved_code,
            "model_used": res.get("model", "qwen2.5-coder:7b"),
            "execution_time_ms": elapsed
        }

    def generate_documentation(self, code_snippet: str, doc_format: str = "docstring", filepath: Optional[str] = None) -> Dict[str, Any]:
        """Generates docstrings, JSDoc, Markdown API specifications, or README content for code."""
        start_time = time.time()

        prompt = (
            f"Generate comprehensive '{doc_format}' documentation for the following code snippet:\n\n"
            f"```\n{code_snippet}\n```\n\n"
            f"Format requirement: Provide clear, professional {doc_format} formatted text."
        )

        res = ollama_service.generate_response(
            prompt=prompt,
            model="qwen2.5-coder:7b",
            system_prompt="You are a Technical Writer specializing in software documentation."
        )

        elapsed = round((time.time() - start_time) * 1000.0, 2)

        return {
            "doc_format": doc_format,
            "documentation": res.get("content", "Documentation generated successfully."),
            "model_used": res.get("model", "qwen2.5-coder:7b"),
            "execution_time_ms": elapsed
        }

    def answer_repo_question(self, question: str, project_path: Optional[str] = None) -> Dict[str, Any]:
        """Answers natural language questions about the codebase grounded in project code structure."""
        start_time = time.time()
        path_to_scan = project_path or os.getcwd()

        read_res = self.read_project(path_to_scan, max_files=30)
        tree_str = ", ".join(read_res.get("file_tree", [])[:20])

        prompt = (
            f"Question about codebase: \"{question}\"\n"
            f"Repository Path: {path_to_scan}\n"
            f"Key Code Files: {tree_str}\n\n"
            f"Answer the question accurately based on the codebase structure and standard architecture."
        )

        res = ollama_service.generate_response(
            prompt=prompt,
            model="qwen2.5-coder:7b",
            system_prompt="You are an expert AI Principal Engineer answering repository questions."
        )

        elapsed = round((time.time() - start_time) * 1000.0, 2)

        return {
            "question": question,
            "answer": res.get("content", "Answer generated based on repository structure."),
            "relevant_files": read_res.get("file_tree", [])[:10],
            "model_used": res.get("model", "qwen2.5-coder:7b"),
            "execution_time_ms": elapsed
        }


coding_assistant_service = CodingAssistantService()
