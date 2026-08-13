import os
import time
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import FileDocument, UserPreference
from app.db.mongodb import mongo_service
from app.services.file_scanner import file_scanner
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.core.logger import logger

class SemanticSearchService:
    """Service combining MongoDB database storage, nomic-embed-text embeddings, and FAISS vector index."""

    def __init__(self):
        self.active_indexed_folder: Optional[str] = None

    def index_folder(self, db: Session, folder_path: str, recursive: bool = True, clear_existing: bool = False) -> Dict[str, Any]:
        r"""Scans folder or system drives (C:\ & D:\), generates embeddings, and indexes files persistently into MongoDB & FAISS."""
        t_start = time.time()
        is_all_drives = folder_path.upper().strip() in ["ALL_DRIVES", "C:\\;D:\\", "SYSTEM", "C:\\,D:\\", "ALL"]
        norm_folder = "System Drives (C:\\ & D:\\)" if is_all_drives else os.path.abspath(os.path.normpath(folder_path))
        self.active_indexed_folder = norm_folder
        logger.info(f"=== [INDEXING START] Target: '{norm_folder}' ===")

        # Save active indexed folder in DB user preferences
        try:
            if mongo_service.is_connected() and mongo_service.user_preferences is not None:
                mongo_service.user_preferences.update_one(
                    {"key": "active_indexed_folder"},
                    {"$set": {"key": "active_indexed_folder", "value": norm_folder}},
                    upsert=True
                )
            pref = db.query(UserPreference).filter(UserPreference.key == "active_indexed_folder").first()
            if pref:
                pref.value = norm_folder
            else:
                db.add(UserPreference(key="active_indexed_folder", value=norm_folder))
            db.commit()
        except Exception:
            db.rollback()

        # Step 0: Clear previous indexes ONLY if explicitly requested
        if clear_existing:
            logger.info("Clearing previous FAISS index, MongoDB & DB records for fresh index...")
            faiss_service.clear()
            if mongo_service.is_connected() and mongo_service.file_documents is not None:
                try:
                    mongo_service.file_documents.delete_many({})
                except Exception as e_m:
                    logger.warning(f"MongoDB clear warning: {e_m}")
            try:
                db.query(FileDocument).delete()
                db.commit()
            except Exception as e:
                db.rollback()

        # Step 1: Directory Scanning
        t1 = time.time()
        if is_all_drives:
            extracted_docs = file_scanner.scan_all_drives(recursive=recursive)
        else:
            extracted_docs = file_scanner.scan_directory(norm_folder, recursive=recursive)

        scan_ms = round((time.time() - t1) * 1000, 2)
        total_scanned = len(extracted_docs)
        logger.info(f"[Timing Log] 1. Directory Scanning: Scanned {total_scanned} files in {scan_ms}ms")

        if not extracted_docs:
            total_in_db = mongo_service.file_documents.count_documents({}) if (mongo_service.is_connected() and mongo_service.file_documents is not None) else db.query(FileDocument).count()
            return {
                "folder_path": norm_folder,
                "files_found": 0,
                "files_scanned": 0,
                "chunks_indexed": 0,
                "skipped_unchanged": 0,
                "total_indexed_in_db": total_in_db,
                "execution_time_ms": round((time.time() - t_start) * 1000, 2)
            }

        # Step 2: Skip Already Indexed Unchanged Files (Incremental Persistent Cache)
        existing_map = {}
        if not clear_existing:
            if mongo_service.is_connected() and mongo_service.file_documents is not None:
                try:
                    for doc in mongo_service.file_documents.find({}, {"filepath": 1, "last_modified_time": 1}):
                        if "filepath" in doc:
                            existing_map[doc["filepath"]] = doc.get("last_modified_time")
                except Exception:
                    pass
            
            if not existing_map:
                try:
                    existing_records = db.query(FileDocument.filepath, FileDocument.last_modified_time).all()
                    existing_map = {r.filepath: r.last_modified_time for r in existing_records if r.filepath}
                except Exception:
                    existing_map = {}

        docs_to_index = []
        skipped_count = 0

        for doc in extracted_docs:
            fp = doc["filepath"]
            mtime = doc.get("last_modified_time")
            if fp in existing_map and mtime is not None and abs((existing_map[fp] or 0) - mtime) < 1.0:
                skipped_count += 1
            else:
                docs_to_index.append(doc)

        if not docs_to_index:
            total_ms = round((time.time() - t_start) * 1000, 2)
            total_in_db = mongo_service.file_documents.count_documents({}) if (mongo_service.is_connected() and mongo_service.file_documents is not None) else db.query(FileDocument).count()
            return {
                "folder_path": norm_folder,
                "files_found": total_scanned,
                "files_scanned": total_scanned,
                "chunks_indexed": 0,
                "skipped_unchanged": skipped_count,
                "total_indexed_in_db": total_in_db,
                "execution_time_ms": total_ms
            }

        # Step 3: Batch Vector Embedding Generation
        t2 = time.time()
        texts = [doc["chunk_text"] for doc in docs_to_index]
        embeddings = embedding_service.get_embeddings_batch(texts)
        embed_ms = round((time.time() - t2) * 1000, 2)

        # Step 4: FAISS Insertion
        t3 = time.time()
        vector_ids = faiss_service.add_vectors(embeddings)
        faiss_ms = round((time.time() - t3) * 1000, 2)

        # Step 5: MongoDB & SQLite Batch Commit
        t4 = time.time()
        fps_to_update = list(set(doc["filepath"] for doc in docs_to_index))

        # Write into MongoDB Compass
        if mongo_service.is_connected() and mongo_service.file_documents is not None:
            try:
                for doc, vec_id in zip(docs_to_index, vector_ids):
                    mongo_doc = {
                        "filepath": doc["filepath"],
                        "filename": doc["filename"],
                        "file_extension": doc["file_extension"],
                        "file_size_bytes": doc["file_size_bytes"],
                        "last_modified_time": doc.get("last_modified_time"),
                        "content_snippet": doc["content_snippet"],
                        "chunk_index": doc["chunk_index"],
                        "vector_id": vec_id
                    }
                    mongo_service.file_documents.update_one(
                        {"filepath": doc["filepath"]},
                        {"$set": mongo_doc},
                        upsert=True
                    )
            except Exception as e_m:
                logger.warning(f"MongoDB batch write warning: {e_m}")

        # Write into SQLite as backup
        try:
            if fps_to_update:
                db.query(FileDocument).filter(FileDocument.filepath.in_(fps_to_update)).delete(synchronize_session=False)

            db_records = []
            for doc, vec_id in zip(docs_to_index, vector_ids):
                record = FileDocument(
                    filepath=doc["filepath"],
                    filename=doc["filename"],
                    file_extension=doc["file_extension"],
                    file_size_bytes=doc["file_size_bytes"],
                    last_modified_time=doc.get("last_modified_time"),
                    content_snippet=doc["content_snippet"],
                    chunk_index=doc["chunk_index"],
                    vector_id=vec_id
                )
                db_records.append(record)

            db.add_all(db_records)
            db.commit()
        except Exception:
            db.rollback()

        total_ms = round((time.time() - t_start) * 1000, 2)
        total_in_db = mongo_service.file_documents.count_documents({}) if (mongo_service.is_connected() and mongo_service.file_documents is not None) else db.query(FileDocument).count()

        logger.info(f"=== [INDEXING COMPLETE] Indexed {len(docs_to_index)} new/updated files into MongoDB 'OSPilot' in {total_ms}ms ===")

        return {
            "folder_path": norm_folder,
            "files_found": total_scanned,
            "files_scanned": total_scanned,
            "chunks_indexed": len(docs_to_index),
            "skipped_unchanged": skipped_count,
            "total_indexed_in_db": total_in_db,
            "execution_time_ms": total_ms
        }

    def search(self, db: Session, query: str, top_k: int = 10, folder_path: Optional[str] = None) -> Dict[str, Any]:
        """Executes ultra-fast AI vector & MongoDB text index search in sub-50ms."""
        start_time = time.time()
        
        target_folder = folder_path or self.active_indexed_folder
        if not target_folder:
            try:
                if mongo_service.is_connected() and mongo_service.user_preferences is not None:
                    p = mongo_service.user_preferences.find_one({"key": "active_indexed_folder"})
                    if p and p.get("value"):
                        target_folder = p.get("value")
                if not target_folder:
                    pref = db.query(UserPreference).filter(UserPreference.key == "active_indexed_folder").first()
                    if pref and pref.value:
                        target_folder = pref.value
            except Exception:
                pass

        is_all_drives = True
        target_folder_norm = None
        if target_folder:
            tf_upper = str(target_folder).upper().strip()
            if tf_upper not in ["ALL_DRIVES", "C:\\;D:\\", "SYSTEM", "C:\\,D:\\", "ALL", "SYSTEM DRIVES (C:\\ & D:\\)"]:
                is_all_drives = False
                target_folder_norm = os.path.abspath(os.path.normpath(target_folder)).lower()

        # Step 1: FAISS Vector Nearest-Neighbor Search (Capped at 50 candidates max for instant execution)
        query_vector = embedding_service.get_embedding(query)
        candidate_count = min(50, faiss_service.index.ntotal) if faiss_service.index and faiss_service.index.ntotal > 0 else top_k
        scores, vector_ids = faiss_service.search(query_vector, top_k=candidate_count)

        stop_words = {'find', 'my', 'the', 'a', 'an', 'is', 'in', 'of', 'for', 'where', 'get', 'show', 'all'}
        raw_terms = [t.lower() for t in re.findall(r'[a-zA-Z0-9]+', query) if len(t) > 1 and t.lower() not in stop_words]
        
        query_terms = list(raw_terms)
        if "resume" in raw_terms:
            query_terms.extend(["cv", "bio", "profile", "biodata"])

        scored_results = []
        seen_filepaths = set()

        # BATCH FETCH vector candidates from MongoDB in 1 query
        valid_vec_ids = [int(v) for v in vector_ids if v != -1]
        mongo_vec_map = {}
        if valid_vec_ids and mongo_service.is_connected() and mongo_service.file_documents is not None:
            try:
                for doc in mongo_service.file_documents.find({"vector_id": {"$in": valid_vec_ids}}):
                    if "vector_id" in doc:
                        mongo_vec_map[doc["vector_id"]] = doc
            except Exception:
                pass

        # Process vector search candidates
        for score, vec_id in zip(scores, vector_ids):
            if vec_id == -1:
                continue
                
            doc = mongo_vec_map.get(vec_id)
            if not doc:
                try:
                    sqldoc = db.query(FileDocument).filter(FileDocument.vector_id == vec_id).first()
                    if sqldoc:
                        doc = {
                            "filepath": sqldoc.filepath,
                            "filename": sqldoc.filename,
                            "file_extension": sqldoc.file_extension,
                            "content_snippet": sqldoc.content_snippet
                        }
                except Exception:
                    pass

            if doc:
                fp = doc.get("filepath", "")
                if not fp or fp in seen_filepaths:
                    continue

                if not is_all_drives and target_folder_norm:
                    doc_path_norm = os.path.abspath(os.path.normpath(fp)).lower()
                    if not doc_path_norm.startswith(target_folder_norm):
                        continue

                seen_filepaths.add(fp)
                final_score = float(score)
                fname_lower = (doc.get("filename") or "").lower()
                fpath_lower = fp.lower()

                for term in query_terms:
                    if term in fname_lower:
                        final_score += 0.50
                    elif term in fpath_lower:
                        final_score += 0.25

                final_score_clamped = min(1.0, max(0.05, final_score))

                scored_results.append({
                    "filename": doc.get("filename", os.path.basename(fp)),
                    "score": round(final_score_clamped, 4),
                    "location": fp,
                    "file_type": doc.get("file_extension", "file"),
                    "snippet": doc.get("content_snippet") or "",
                    "_raw_score": final_score
                })

        # Step 2: Direct BATCH Keyword Search in MongoDB for instant matches
        if query_terms:
            for term in query_terms:
                if mongo_service.is_connected() and mongo_service.file_documents is not None:
                    try:
                        regex_pat = re.compile(re.escape(term), re.IGNORECASE)
                        cursor = mongo_service.file_documents.find({
                            "$or": [
                                {"filename": regex_pat},
                                {"filepath": regex_pat}
                            ]
                        }).limit(top_k * 3)

                        for mdoc in cursor:
                            fp = mdoc.get("filepath", "")
                            if not fp or fp in seen_filepaths:
                                continue

                            if not is_all_drives and target_folder_norm:
                                doc_path_norm = os.path.abspath(os.path.normpath(fp)).lower()
                                if not doc_path_norm.startswith(target_folder_norm):
                                    continue

                            seen_filepaths.add(fp)
                            scored_results.append({
                                "filename": mdoc.get("filename", os.path.basename(fp)),
                                "score": 0.96,
                                "location": fp,
                                "file_type": mdoc.get("file_extension", "file"),
                                "snippet": mdoc.get("content_snippet") or "",
                                "_raw_score": 0.96
                            })
                    except Exception as e_m:
                        logger.warning(f"MongoDB keyword query warning: {e_m}")

                # SQLite Backup Search
                try:
                    matching_docs = db.query(FileDocument).filter(
                        (FileDocument.filename.ilike(f"%{term}%")) | (FileDocument.filepath.ilike(f"%{term}%"))
                    ).limit(top_k * 3).all()

                    for doc in matching_docs:
                        fp = doc.filepath
                        if not fp or fp in seen_filepaths:
                            continue

                        if not is_all_drives and target_folder_norm:
                            doc_path_norm = os.path.abspath(os.path.normpath(fp)).lower()
                            if not doc_path_norm.startswith(target_folder_norm):
                                continue

                        seen_filepaths.add(fp)
                        scored_results.append({
                            "filename": doc.filename,
                            "score": 0.92,
                            "location": doc.filepath,
                            "file_type": doc.file_extension,
                            "snippet": doc.content_snippet or "",
                            "_raw_score": 0.92
                        })
                except Exception:
                    pass

        # Sort by final score descending
        scored_results.sort(key=lambda x: x["_raw_score"], reverse=True)
        final_results = scored_results[:top_k]

        for r in final_results:
            r.pop("_raw_score", None)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "query": query,
            "results": final_results,
            "total_found": len(final_results),
            "execution_time_ms": elapsed_ms
        }

semantic_search_service = SemanticSearchService()
