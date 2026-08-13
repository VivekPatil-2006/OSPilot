import re
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import FileDocument
from app.services.document_loader import document_loader
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.services.ollama_service import ollama_service
from app.core.logger import logger


class RAGService:
    """Service providing local Retrieval-Augmented Generation (RAG) capabilities,

    supporting PDF, DOCX, TXT, and Markdown document indexing, summarization, Q&A, and section explanations.
    """

    def index_document(self, db: Session, filepath: str) -> Dict[str, Any]:
        """Loads, parses, chunks, embeds, and indexes a single document file."""
        start_time = time.time()

        chunks = document_loader.load_and_chunk_document(filepath)
        if not chunks:
            return {
                "filepath": filepath,
                "status": "empty",
                "chunks_indexed": 0,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }

        texts = [c["chunk_text"] for c in chunks]
        embeddings = embedding_service.get_embeddings_batch(texts)
        vector_ids = faiss_service.add_vectors(embeddings)

        db_records = []
        for chunk_data, vec_id in zip(chunks, vector_ids):
            record = FileDocument(
                filepath=chunk_data["filepath"],
                filename=chunk_data["filename"],
                file_extension=chunk_data["file_extension"],
                file_size_bytes=chunk_data["file_size_bytes"],
                section_title=chunk_data.get("section_title"),
                page_number=chunk_data.get("page_number"),
                content_snippet=chunk_data["chunk_text"],
                chunk_index=chunk_data["chunk_index"],
                vector_id=vec_id
            )
            db_records.append(record)

        db.add_all(db_records)
        db.commit()

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Indexed document '{filepath}' ({len(chunks)} chunks) in {elapsed_ms}ms.")

        return {
            "filepath": filepath,
            "filename": chunks[0]["filename"],
            "file_extension": chunks[0]["file_extension"],
            "chunks_indexed": len(chunks),
            "execution_time_ms": elapsed_ms
        }

    def summarize_document(self, db: Session, filepath: Optional[str] = None, filename: Optional[str] = None) -> Dict[str, Any]:
        """Generates a comprehensive summary for an indexed document using local Ollama LLM."""
        start_time = time.time()

        query_builder = db.query(FileDocument)
        if filepath:
            query_builder = query_builder.filter(FileDocument.filepath == filepath)
        elif filename:
            query_builder = query_builder.filter(FileDocument.filename == filename)

        records = query_builder.order_by(FileDocument.chunk_index.asc()).all()

        if not records:
            # If document not indexed yet, load and index first if filepath given
            if filepath:
                self.index_document(db, filepath)
                records = db.query(FileDocument).filter(FileDocument.filepath == filepath).order_by(FileDocument.chunk_index.asc()).all()

        if not records:
            raise ValueError(f"No indexed document found matching filepath='{filepath}' or filename='{filename}'")

        doc_filename = records[0].filename
        
        # Sample chunks for summary prompt (take up to top 10 representative chunks across document)
        total_chunks = len(records)
        if total_chunks <= 10:
            sampled_records = records
        else:
            step = total_chunks // 10
            sampled_records = records[::step][:10]

        context_blocks = []
        for rec in sampled_records:
            sec_info = f" [{rec.section_title}]" if rec.section_title else ""
            context_blocks.append(f"--- Section/Chunk {rec.chunk_index + 1}{sec_info} ---\n{rec.content_snippet}")

        doc_text = "\n\n".join(context_blocks)

        prompt = (
            f"Please summarize the following document titled '{doc_filename}'.\n\n"
            f"DOCUMENT CONTENT EXTRACTS:\n{doc_text}\n\n"
            "INSTRUCTIONS:\n"
            "1. Provide a concise Executive Summary (2-3 sentences).\n"
            "2. List Key Takeaways / Main Points.\n"
            "3. Outline the main sections discussed in the document.\n"
            "Format your response clearly using Markdown headings and bullet points."
        )

        sys_prompt = "You are OSPilot Document Assistant, an expert offline RAG system. Provide accurate, clear, and structured document summaries based on provided context."

        result = ollama_service.generate_response(
            prompt=prompt,
            system_prompt=sys_prompt,
            temperature=0.3
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "filename": doc_filename,
            "filepath": records[0].filepath,
            "total_chunks": total_chunks,
            "summary": result["content"],
            "model_used": result["model"],
            "execution_time_ms": elapsed_ms
        }

    def query_document(
        self,
        db: Session,
        query: str,
        filepath: Optional[str] = None,
        filename: Optional[str] = None,
        top_k: int = 5,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Answers questions or explains specific sections of an indexed document using fast Hybrid RAG."""
        start_time = time.time()

        import os
        norm_filepath = None
        target_filename = None
        if filepath and filepath.strip():
            filepath = filepath.strip()
            norm_filepath = os.path.abspath(os.path.normpath(filepath)) if os.path.exists(filepath) else os.path.normpath(filepath)
            target_filename = os.path.basename(norm_filepath)
        elif filename and filename.strip():
            target_filename = filename.strip()

        # Helper function for matching target document
        def is_target_doc(rec: FileDocument) -> bool:
            if not norm_filepath and not target_filename:
                return True
            if norm_filepath:
                if rec.filepath == norm_filepath or rec.filepath.lower() == norm_filepath.lower():
                    return True
                rec_norm = os.path.normpath(rec.filepath)
                if rec_norm.lower() == norm_filepath.lower():
                    return True
            if target_filename:
                if rec.filename.lower() == target_filename.lower():
                    return True
            return False

        # Auto-index if specified filepath/filename is NOT in DB yet, but exists on disk
        if norm_filepath or target_filename:
            q_existing = db.query(FileDocument).all()
            has_indexed_records = any(is_target_doc(rec) for rec in q_existing)

            if not has_indexed_records and filepath and os.path.exists(filepath):
                logger.info(f"Target document '{filepath}' not found in index. Auto-indexing now...")
                try:
                    self.index_document(db, filepath)
                except Exception as e:
                    logger.error(f"Auto-indexing failed for '{filepath}': {e}")

        # Extract query search terms for BM25/keyword scoring
        query_terms = [t.lower() for t in re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', query)]

        # Check if query is asking to "Explain section X"
        section_match = re.search(r'\b(?:section|chapter|part|page)\s+([a-zA-Z0-9.\-]+)\b', query, re.IGNORECASE)
        target_section_keyword = section_match.group(0) if section_match else None

        # Perform FAISS similarity search
        query_vector = embedding_service.get_embedding(query)
        scores, vector_ids = faiss_service.search(query_vector, top_k=top_k * 4)

        candidate_records = []
        retrieved_vec_ids = set()

        for score, vec_id in zip(scores, vector_ids):
            if vec_id == -1:
                continue
            doc = db.query(FileDocument).filter(FileDocument.vector_id == vec_id).first()
            if doc and is_target_doc(doc) and doc.vector_id not in retrieved_vec_ids:
                retrieved_vec_ids.add(doc.vector_id)

                # Compute keyword term score
                content_lower = doc.content_snippet.lower()
                sec_lower = (doc.section_title or "").lower()
                matches = sum(1 for term in query_terms if term in content_lower or term in sec_lower)
                kw_score = min(matches / max(len(query_terms), 1), 1.0)

                # Hybrid score: 0.65 * vector_score + 0.35 * keyword_score
                vec_score = float(score)
                hybrid_score = round(0.65 * vec_score + 0.35 * kw_score, 4)
                candidate_records.append((doc, hybrid_score))

        # If user explicitly specified a section (e.g., Section 4), match section titles directly
        if target_section_keyword:
            all_sec_docs = db.query(FileDocument).filter(
                FileDocument.section_title.ilike(f"%{target_section_keyword}%")
            ).all()
            for s_doc in all_sec_docs:
                if is_target_doc(s_doc) and s_doc.vector_id not in retrieved_vec_ids:
                    retrieved_vec_ids.add(s_doc.vector_id)
                    candidate_records.append((s_doc, 0.99))

        # Fallback if no vector candidates matched
        if not candidate_records and (norm_filepath or target_filename):
            all_docs = db.query(FileDocument).all()
            target_docs = [d for d in all_docs if is_target_doc(d)]
            if target_docs:
                target_docs.sort(key=lambda x: x.chunk_index)
                candidate_records = [(r, 0.5) for r in target_docs[:top_k]]

        if not candidate_records:
            if filepath or filename:
                doc_name = target_filename or filepath
                return {
                    "query": query,
                    "answer": f"Could not find indexed content for document '{doc_name}'. Please verify the filepath.",
                    "model_used": "none",
                    "sources": [],
                    "execution_time_ms": round((time.time() - start_time) * 1000, 2)
                }
            else:
                all_docs = db.query(FileDocument).limit(top_k).all()
                candidate_records = [(r, 0.5) for r in all_docs]

        if not candidate_records:
            return {
                "query": query,
                "answer": "No indexed documents found in database. Please specify or index a document first.",
                "model_used": "none",
                "sources": [],
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }

        # Rank by hybrid score descending and pick top 3 highest-quality chunks
        candidate_records.sort(key=lambda x: x[1], reverse=True)
        top_records = candidate_records[:3]

        context_snippets = []
        sources = []

        for doc, score in top_records:
            sec_label = f" [Section: {doc.section_title}]" if doc.section_title else ""
            page_label = f" [Page {doc.page_number}]" if doc.page_number else ""
            context_snippets.append(f"--- Context (Match: {int(score * 100)}%){sec_label}{page_label} ---\n{doc.content_snippet}")

            sources.append({
                "filename": doc.filename,
                "filepath": doc.filepath,
                "section_title": doc.section_title or "Main Content",
                "page_number": doc.page_number,
                "score": round(score, 4),
                "snippet": doc.content_snippet[:200]
            })

        context_str = "\n\n".join(context_snippets)

        prompt = (
            f"QUESTION: {query}\n\n"
            f"RETRIEVED DOCUMENT CONTEXT:\n{context_str}\n\n"
            "INSTRUCTIONS:\n"
            "Answer concisely and directly using ONLY the retrieved document context above.\n"
            "Be factual, accurate, and do not repeat context text unnecessarily."
        )

        sys_prompt = "You are OSPilot RAG Assistant. Provide immediate, accurate, and concise document answers based on context."

        gen_result = ollama_service.generate_response(
            prompt=prompt,
            model=model,
            system_prompt=sys_prompt,
            temperature=0.2
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "query": query,
            "answer": gen_result["content"],
            "model_used": gen_result["model"],
            "sources": sources,
            "execution_time_ms": elapsed_ms
        }


rag_service = RAGService()
