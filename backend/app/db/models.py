from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.db.base import Base

class FileDocument(Base):
    """SQLAlchemy model for indexing document metadata."""
    __tablename__ = "file_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filepath = Column(String, index=True, nullable=False)
    filename = Column(String, index=True, nullable=False)
    file_extension = Column(String, index=True, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    content_snippet = Column(Text, nullable=True)
    section_title = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, default=0, nullable=False)
    vector_id = Column(Integer, unique=True, index=True, nullable=False)
    last_modified_time = Column(Float, nullable=True)
    indexed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)



class ConversationHistory(Base):
    """SQLAlchemy model for storing multi-turn session conversation history."""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class UserPreference(Base):
    """SQLAlchemy model for key-value user preference settings."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class TaskHistoryLog(Base):
    """SQLAlchemy model for logging automated task executions."""
    __tablename__ = "task_history_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True, nullable=True)
    action = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class LongTermMemoryItem(Base):
    """SQLAlchemy model for long-term facts and instructions."""
    __tablename__ = "long_term_memories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    memory_key = Column(String, index=True, nullable=False)
    fact_content = Column(Text, nullable=False)
    category = Column(String, default="general", nullable=False)
    vector_id = Column(Integer, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


