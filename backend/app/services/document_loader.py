import os
import re
from typing import List, Dict, Any, Optional
from app.core.logger import logger

# Try importing LangChain text splitters
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        RecursiveCharacterTextSplitter = None

# Try importing PDF reader
try:
    import pypdf
except ImportError:
    pypdf = None

# Try importing DOCX reader
try:
    import docx
except ImportError:
    docx = None


class DocumentLoaderService:
    """Service to extract text content and sections from PDF, DOCX, TXT, and Markdown files,
    and split them into structured document chunks using LangChain splitters.
    """

    def __init__(self, chunk_size: int = 450, chunk_overlap: int = 80):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Cache RecursiveCharacterTextSplitter instance at initialization
        if RecursiveCharacterTextSplitter is not None:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
            )
        else:
            self.splitter = None


    def load_and_chunk_document(self, filepath: str) -> List[Dict[str, Any]]:
        """Loads a document file (PDF, DOCX, TXT, MD), extracts text & structure, and returns chunks with metadata."""
        norm_path = os.path.abspath(os.path.normpath(filepath))
        if not os.path.exists(norm_path):
            raise FileNotFoundError(f"File not found: '{filepath}'")

        filename = os.path.basename(norm_path)
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            raw_sections = self._read_pdf(norm_path)
        elif ext in [".docx", ".doc"]:
            raw_sections = self._read_docx(norm_path)
        elif ext == ".md":
            raw_sections = self._read_markdown(norm_path)
        elif ext == ".txt" or ext == "":
            raw_sections = self._read_txt(norm_path)
        else:
            # Fallback text reading
            raw_sections = self._read_txt(norm_path)

        file_stat = os.stat(norm_path)
        chunks = []
        global_chunk_idx = 0

        for sec in raw_sections:
            sec_title = sec.get("section_title", "")
            page_num = sec.get("page_number")
            sec_text = sec.get("text", "").strip()

            if not sec_text:
                continue

            sub_chunks = self._chunk_text(sec_text)
            for sub_text in sub_chunks:
                chunks.append({
                    "filepath": norm_path,
                    "filename": filename,
                    "file_extension": ext.lstrip(".") or "txt",
                    "file_size_bytes": file_stat.st_size,
                    "section_title": sec_title,
                    "page_number": page_num,
                    "chunk_index": global_chunk_idx,
                    "content_snippet": sub_text[:300],
                    "chunk_text": sub_text
                })
                global_chunk_idx += 1

        logger.info(f"Loaded '{filename}' ({ext}): extracted {len(chunks)} chunks across {len(raw_sections)} sections/pages.")
        return chunks

    def _read_pdf(self, filepath: str) -> List[Dict[str, Any]]:
        """Extracts text from PDF page by page."""
        sections = []
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(filepath)
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        sections.append({
                            "section_title": f"Page {idx + 1}",
                            "page_number": idx + 1,
                            "text": text
                        })
                if sections:
                    return sections
            except Exception as e:
                logger.warning(f"Error extracting PDF via pypdf '{filepath}': {e}")

        # Fallback reading
        raw_text = self._read_raw_file(filepath)
        return [{"section_title": "Document Content", "page_number": 1, "text": raw_text}]

    def _read_docx(self, filepath: str) -> List[Dict[str, Any]]:
        """Extracts text from DOCX preserving headings as section titles."""
        sections = []
        if docx is not None:
            try:
                doc = docx.Document(filepath)
                current_heading = "Main Content"
                current_text_lines = []
                section_count = 1

                for para in doc.paragraphs:
                    text = para.text.strip()
                    if not text:
                        continue

                    # Check if paragraph is a heading
                    if para.style and para.style.name.startswith("Heading"):
                        if current_text_lines:
                            sections.append({
                                "section_title": current_heading,
                                "page_number": None,
                                "text": "\n".join(current_text_lines)
                            })
                            current_text_lines = []
                        current_heading = text
                        section_count += 1
                    else:
                        current_text_lines.append(text)

                if current_text_lines:
                    sections.append({
                        "section_title": current_heading,
                        "page_number": None,
                        "text": "\n".join(current_text_lines)
                    })

                if sections:
                    return sections
            except Exception as e:
                logger.warning(f"Error reading docx '{filepath}': {e}")

        raw_text = self._read_raw_file(filepath)
        return [{"section_title": "Document Content", "page_number": None, "text": raw_text}]

    def _read_markdown(self, filepath: str) -> List[Dict[str, Any]]:
        """Extracts sections from Markdown based on header tags (# Header)."""
        content = self._read_raw_file(filepath)
        if not content:
            return []

        lines = content.splitlines()
        sections = []
        current_section = "Introduction"
        current_lines = []

        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

        for line in lines:
            match = header_pattern.match(line.strip())
            if match:
                if current_lines:
                    sections.append({
                        "section_title": current_section,
                        "page_number": None,
                        "text": "\n".join(current_lines)
                    })
                    current_lines = []
                current_section = match.group(2).strip()
            else:
                current_lines.append(line)

        if current_lines:
            sections.append({
                "section_title": current_section,
                "page_number": None,
                "text": "\n".join(current_lines)
            })

        return sections or [{"section_title": "Document Content", "page_number": None, "text": content}]

    def _read_txt(self, filepath: str) -> List[Dict[str, Any]]:
        """Reads plain text document and splits into sections if section headings are present."""
        content = self._read_raw_file(filepath)
        if not content:
            return []

        lines = content.splitlines()
        sections = []
        current_section = "Overview"
        current_lines = []

        for line in lines:
            trimmed = line.strip()
            # Detect section heading candidates: e.g. "=== Section ===", "[SECTION]", "Section 1:", "REQUIREMENTS:"
            if (trimmed.isupper() and len(trimmed) > 3 and len(trimmed) < 60) or \
               (trimmed.startswith(('[', '===', '---')) and len(trimmed) < 60) or \
               (re.match(r'^(?:Section|Chapter|Part|Step)\s+\d+[:\s]?', trimmed, re.IGNORECASE)):
                if current_lines:
                    sections.append({
                        "section_title": current_section,
                        "page_number": None,
                        "text": "\n".join(current_lines)
                    })
                    current_lines = []
                current_section = trimmed.strip("=[]- ")
            else:
                current_lines.append(line)

        if current_lines:
            sections.append({
                "section_title": current_section,
                "page_number": None,
                "text": "\n".join(current_lines)
            })

        return sections or [{"section_title": "Document Content", "page_number": None, "text": content}]

    def _read_raw_file(self, filepath: str) -> str:
        """Safely reads raw text from file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read file '{filepath}': {e}")
            return ""

    def _chunk_text(self, text: str) -> List[str]:
        """Chunks text using cached LangChain RecursiveCharacterTextSplitter or fallback word chunker."""
        if not text or not text.strip():
            return []

        if self.splitter is not None:
            try:
                return self.splitter.split_text(text)
            except Exception as e:
                logger.warning(f"Cached RecursiveCharacterTextSplitter failed ({e}), using fallback.")


        # Fallback word-based chunker
        words = text.split()
        if len(words) <= 100:
            return [text]

        chunks = []
        chunk_words = 100
        overlap_words = 20
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_words])
            chunks.append(chunk)
            i += (chunk_words - overlap_words)

        return chunks


document_loader = DocumentLoaderService()
