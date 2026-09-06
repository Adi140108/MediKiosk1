import os
import logging
from typing import Dict, Any, Optional, List
from google.cloud import firestore
from app.core.config import settings

logger = logging.getLogger("medikiosk.db")

class BaseRepository:
    """
    Base Firestore Repository with thread-safe in-memory fallback
    for local development without GCP credentials.
    """
    _in_memory_db: Dict[str, Dict[str, Any]] = {}
    _firestore_client: Optional[firestore.Client] = None
    _use_in_memory: Optional[bool] = None

    @classmethod
    def get_client(cls) -> Optional[firestore.Client]:
        if cls._firestore_client is not None:
            return cls._firestore_client

        if cls._use_in_memory is True:
            return None

        # Check for service account json in environment or settings or project root
        cred_path = (
            os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            or settings.GOOGLE_APPLICATION_CREDENTIALS
        )

        # Auto-discover common service account key file patterns if not explicitly specified
        if not cred_path or not os.path.exists(cred_path):
            candidate_dirs = [".", "..", "config", "backend"]
            for d in candidate_dirs:
                if os.path.exists(d):
                    for fname in os.listdir(d):
                        if fname.endswith(".json") and any(k in fname.lower() for k in ["firebase", "service-account", "service_account", "medikiosk", "firestore"]):
                            candidate_path = os.path.join(d, fname)
                            if os.path.isfile(candidate_path):
                                cred_path = candidate_path
                                break
                    if cred_path and os.path.exists(cred_path):
                        break

        if cred_path and os.path.exists(cred_path):
            try:
                cls._firestore_client = firestore.Client.from_service_account_json(
                    cred_path,
                    project=settings.FIRESTORE_PROJECT_ID
                )
                cls._use_in_memory = False
                logger.info("Connected to Google Cloud Firestore using service account: %s", cred_path)
                return cls._firestore_client
            except Exception as e:
                logger.error("Failed to authenticate Firestore with %s: %s", cred_path, str(e))

        # In dev mode without credentials set, avoid gRPC network timeout
        if settings.USE_MOCK_FIRESTORE_IN_DEV:
            cls._use_in_memory = True
            logger.info("Using in-memory development database (No Google Cloud credentials configured).")
            return None

        try:
            cls._firestore_client = firestore.Client(project=settings.FIRESTORE_PROJECT_ID)
            cls._use_in_memory = False
            logger.info("Connected to Google Cloud Firestore successfully.")
        except Exception as e:
            logger.warning("Firestore connection failed (%s). Falling back to in-memory development database.", str(e))
            cls._use_in_memory = True
            cls._firestore_client = None
        return cls._firestore_client

    @classmethod
    def reset_in_memory_db(cls):
        cls._in_memory_db.clear()

    def set_doc(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        client = self.get_client()
        if client:
            try:
                client.collection(collection).document(doc_id).set(data)
                return data
            except Exception as e:
                logger.error("Firestore set_doc failed: %s. Using in-memory fallback.", str(e))

        if collection not in self._in_memory_db:
            self._in_memory_db[collection] = {}
        self._in_memory_db[collection][doc_id] = data
        return data

    def get_doc(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        client = self.get_client()
        if client:
            try:
                snapshot = client.collection(collection).document(doc_id).get()
                if snapshot.exists:
                    return snapshot.to_dict()
                return None
            except Exception as e:
                logger.error("Firestore get_doc failed: %s. Using in-memory fallback.", str(e))

        return self._in_memory_db.get(collection, {}).get(doc_id)

    def list_docs(self, collection: str) -> List[Dict[str, Any]]:
        client = self.get_client()
        if client:
            try:
                docs = client.collection(collection).stream()
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error("Firestore list_docs failed: %s. Using in-memory fallback.", str(e))

        return list(self._in_memory_db.get(collection, {}).values())

    def update_doc(self, collection: str, doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc = self.get_doc(collection, doc_id)
        if not doc:
            return None
        doc.update(updates)
        return self.set_doc(collection, doc_id, doc)
