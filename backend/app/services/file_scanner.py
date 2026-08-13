import os
from typing import List, Dict, Any
from app.core.logger import logger

IGNORED_DIRS = {
    'node_modules', '.git', 'venv', '.next', 'target', 'bin', 'obj', 'build',
    '.idea', '.vscode', 'dist', '__pycache__', '.pytest_cache', 'env', '.env',
    '$recycle.bin', 'system volume information', 'windows', 'programdata', 'appdata',
    'program files', 'program files (x86)', 'msocache', '$windows.~bt'
}

from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

class FileScannerService:
    """Service scanning file directories recursively and indexing file names and paths without reading file descriptions."""

    def scan_all_drives(self, drives: Optional[List[str]] = None, recursive: bool = True) -> List[Dict[str, Any]]:
        """Scans C: and D: drives (and available drive letters) concurrently using ThreadPoolExecutor."""
        if not drives:
            drives = []
            for letter in ['C', 'D', 'E', 'F']:
                d_path = f"{letter}:\\"
                if os.path.exists(d_path):
                    drives.append(d_path)
            if not drives:
                drives = [os.getcwd()]

        all_documents = []
        with ThreadPoolExecutor(max_workers=max(1, len(drives))) as executor:
            future_to_drive = {executor.submit(self.scan_directory, drive, recursive): drive for drive in drives}
            for future in future_to_drive:
                drive = future_to_drive[future]
                try:
                    docs = future.result()
                    all_documents.extend(docs)
                except Exception as e:
                    logger.warning(f"Drive scan warning for '{drive}': {e}")

        return all_documents

    def scan_directory(self, folder_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """Recursively scans directory and extracts metadata & filename/path chunks without opening or reading file contents."""
        norm_path = os.path.abspath(os.path.normpath(folder_path))
        if not os.path.exists(norm_path):
            raise ValueError(f"Directory path '{folder_path}' does not exist.")

        documents = []
        
        for root, dirs, files in os.walk(norm_path):
            # Prune ignored dependency directories in-place for fast scanning
            dirs[:] = [d for d in dirs if d.lower() not in IGNORED_DIRS]

            for file in files:
                full_path = os.path.abspath(os.path.join(root, file))
                try:
                    file_stat = os.stat(full_path)
                    ext = os.path.splitext(file)[1].lower().lstrip(".") or "file"
                    rel_path = os.path.relpath(full_path, norm_path)

                    chunk_text = f"Filename: {file} | Extension: {ext} | Relative Path: {rel_path} | Full Location: {full_path}"
                    snippet = f"Filename: {file}\nPath: {rel_path}"

                    documents.append({
                        "filepath": full_path,
                        "filename": file,
                        "file_extension": ext,
                        "file_size_bytes": file_stat.st_size,
                        "last_modified_time": file_stat.st_mtime,
                        "content_snippet": snippet,
                        "chunk_text": chunk_text,
                        "chunk_index": 0
                    })

                except Exception as e:
                    logger.warning(f"Skipping file '{full_path}': {e}")
            
            if not recursive:
                break

        return documents

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Splits a text string into overlapping word chunks."""
        if not text:
            return []
        words = text.split()
        if not words:
            return []
        
        chunks = []
        start = 0
        while start < len(words):
            end = min(len(words), start + chunk_size)
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end == len(words):
                break
            start = max(start + 1, end - overlap)
        return chunks

file_scanner = FileScannerService()
