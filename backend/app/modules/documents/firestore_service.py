import logging
from typing import Dict, Any, Optional, List
from app.modules.documents.models import DocumentMetadata
from app.db.repositories.base import BaseRepository

logger = logging.getLogger("medikiosk.documents.firestore")

class FirestoreDocumentService(BaseRepository):
    COLLECTION = "documents"

    def __init__(self, project_id: str = None, client: Optional[Any] = None):
        self.project_id = project_id
        if client:
            BaseRepository._firestore_client = client
            BaseRepository._use_in_memory = False

    def save_document_metadata(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        Saves document metadata to Firestore (or in-memory dev store).
        """
        doc_dict = metadata.to_dict()
        doc_id = metadata.document_id
        try:
            self.set_doc(self.COLLECTION, doc_id, doc_dict)
            logger.info("Saved metadata for document %s in storage/firestore", doc_id)
            return doc_dict
        except Exception as e:
            logger.error("Failed to save document metadata: %s", str(e))
            raise RuntimeError(f"Document metadata persistence failed: {str(e)}") from e

    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves document metadata by document_id.
        """
        try:
            return self.get_doc(self.COLLECTION, document_id)
        except Exception as e:
            logger.error("Failed to fetch document metadata for %s: %s", document_id, str(e))
            raise RuntimeError(f"Document fetch failed: {str(e)}") from e

    def get_documents_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all documents associated with an intake session.
        """
        all_docs = self.list_docs(self.COLLECTION)
        return [doc for doc in all_docs if doc.get("session_id") == session_id]

    def get_documents_by_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all documents associated with a patient.
        """
        all_docs = self.list_docs(self.COLLECTION)
        return [doc for doc in all_docs if doc.get("patient_id") == patient_id]

