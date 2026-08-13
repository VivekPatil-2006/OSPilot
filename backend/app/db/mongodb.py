import os
import pymongo
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logger import logger

class MongoDBService:
    """Service managing MongoDB connection, indexes, and document collections for OSPilot."""

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or getattr(settings, "MONGODB_URL", "mongodb://localhost:27017")
        self.db_name = db_name or getattr(settings, "MONGODB_DB_NAME", "OSPilot")
        self.client = None
        self.db = None
        self._connected = False
        self.connect()

    def connect(self) -> bool:
        """Establishes connection to MongoDB server and initializes OSPilot database & collections."""
        try:
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=3000)
            # Test connectivity
            info = self.client.server_info()
            self.db = self.client[self.db_name]
            self._connected = True
            
            # Create collections and indexes if not existing
            self._init_indexes()
            logger.info(f"Connected to MongoDB v{info.get('version')} at '{self.uri}' (Database: '{self.db_name}')")
            return True
        except Exception as e:
            logger.warning(f"MongoDB connection warning ({self.uri}): {e}")
            self._connected = False
            return False

    def _init_indexes(self):
        """Initializes high-performance index keys on collections for sub-10ms queries."""
        if not self._connected or self.db is None:
            return
        try:
            # Collections
            self.db["file_documents"].create_index("filepath", unique=True)
            self.db["file_documents"].create_index("filename")
            self.db["file_documents"].create_index("vector_id")
            try:
                self.db["file_documents"].create_index([("filename", pymongo.TEXT), ("filepath", pymongo.TEXT)])
            except Exception:
                pass
            self.db["chat_messages"].create_index("session_id")
            self.db["user_preferences"].create_index("key", unique=True)
        except Exception as e:
            logger.warning(f"MongoDB index setup warning: {e}")

    def is_connected(self) -> bool:
        """Checks if MongoDB server is active and responding."""
        if not self._connected or self.client is None:
            return self.connect()
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            self._connected = False
            return False

    # --- Collections Accessors ---
    @property
    def file_documents(self):
        return self.db["file_documents"] if self.db is not None else None

    @property
    def chat_sessions(self):
        return self.db["chat_sessions"] if self.db is not None else None

    @property
    def chat_messages(self):
        return self.db["chat_messages"] if self.db is not None else None

    @property
    def user_preferences(self):
        return self.db["user_preferences"] if self.db is not None else None

    def get_server_status(self) -> Dict[str, Any]:
        """Returns MongoDB connection metadata, version, and collection stats."""
        if not self.is_connected():
            return {"connected": False, "version": "N/A", "db_name": self.db_name, "collections": []}

        try:
            info = self.client.server_info()
            cols = self.db.list_collection_names()
            return {
                "connected": True,
                "version": info.get("version", "8.2.7"),
                "db_name": self.db_name,
                "collections": cols,
                "collections_count": len(cols)
            }
        except Exception as e:
            return {"connected": False, "error": str(e), "db_name": self.db_name}

mongo_service = MongoDBService()
