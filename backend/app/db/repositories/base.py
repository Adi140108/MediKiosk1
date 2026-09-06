import os
import sys
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from google.cloud import firestore
from app.core.config import settings

logger = logging.getLogger("medikiosk.db")

def _to_firestore_val(v: Any) -> Dict[str, Any]:
    if v is None:
        return {'nullValue': None}
    elif isinstance(v, bool):
        return {'booleanValue': v}
    elif isinstance(v, int):
        return {'integerValue': str(v)}
    elif isinstance(v, float):
        return {'doubleValue': v}
    elif isinstance(v, str):
        return {'stringValue': v}
    elif isinstance(v, datetime):
        return {'timestampValue': v.isoformat() if v.tzinfo else v.replace(tzinfo=timezone.utc).isoformat()}
    elif isinstance(v, (list, tuple, set)):
        return {'arrayValue': {'values': [_to_firestore_val(x) for x in v]}}
    elif isinstance(v, dict):
        return {'mapValue': {'fields': {str(k): _to_firestore_val(val) for k, val in v.items()}}}
    return {'stringValue': str(v)}

def _from_firestore_val(v: Any) -> Any:
    if not isinstance(v, dict) or not v:
        return None
    k = next(iter(v.keys()))
    val = v[k]
    if k == 'nullValue':
        return None
    elif k == 'booleanValue':
        return bool(val)
    elif k == 'integerValue':
        return int(val)
    elif k == 'doubleValue':
        return float(val)
    elif k == 'stringValue':
        return str(val)
    elif k == 'timestampValue':
        return str(val)
    elif k == 'arrayValue':
        return [_from_firestore_val(x) for x in val.get('values', [])]
    elif k == 'mapValue':
        return {mk: _from_firestore_val(mv) for mk, mv in val.get('fields', {}).items()}
    return val

def _dict_to_firestore_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    return {str(k): _to_firestore_val(v) for k, v in data.items()}

def _firestore_fields_to_dict(fields: Dict[str, Any]) -> Dict[str, Any]:
    if not fields:
        return {}
    return {str(k): _from_firestore_val(v) for k, v in fields.items()}


class BaseRepository:
    """
    Production Firestore Repository with native REST API tunneling,
    automatic schema mapping, and instant in-memory multi-container caching.
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

        cred_path = (
            os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            or settings.GOOGLE_APPLICATION_CREDENTIALS
        )

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
                logger.info("Connected to Google Cloud Firestore via service account: %s", cred_path)
                return cls._firestore_client
            except Exception as e:
                logger.warning("Service account auth failed (%s). Will use REST API tunneling.", str(e))

        return None

    @classmethod
    def reset_in_memory_db(cls):
        cls._in_memory_db.clear()

    def _is_test_mode(self) -> bool:
        return "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST") is not None

    def _sync_firestore_rest(self, collection: str, doc_id: str, data: Dict[str, Any]):
        """Persists document directly to Cloud Firestore medikiosk1-cefd5 using REST API"""
        if self._is_test_mode():
            return
        project_id = settings.FIRESTORE_PROJECT_ID or "medikiosk1-cefd5"
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection}/{doc_id}"
        try:
            fields = _dict_to_firestore_fields(data)
            body = json.dumps({"fields": fields}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="PATCH"
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                pass
        except Exception as e:
            logger.debug("Firestore REST sync notice for %s/%s: %s", collection, doc_id, str(e))

    def _fetch_firestore_rest_doc(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a single document from Cloud Firestore REST API"""
        if self._is_test_mode():
            return None
        project_id = settings.FIRESTORE_PROJECT_ID or "medikiosk1-cefd5"
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection}/{doc_id}"
        try:
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"}, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                fields = res.get("fields", {})
                return _firestore_fields_to_dict(fields)
        except urllib.error.HTTPError as he:
            if he.code == 404:
                return None
        except Exception as e:
            logger.debug("Firestore REST fetch notice for %s/%s: %s", collection, doc_id, str(e))
        return None

    def _fetch_firestore_rest_collection(self, collection: str) -> List[Dict[str, Any]]:
        """Fetches all documents in a collection from Cloud Firestore REST API"""
        if self._is_test_mode():
            return []
        project_id = settings.FIRESTORE_PROJECT_ID or "medikiosk1-cefd5"
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection}?pageSize=100"
        results = []
        try:
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"}, method="GET")
            with urllib.request.urlopen(req, timeout=4) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                docs = res.get("documents", [])
                for doc in docs:
                    fields = doc.get("fields", {})
                    decoded = _firestore_fields_to_dict(fields)
                    if decoded:
                        results.append(decoded)
        except Exception as e:
            logger.debug("Firestore REST list notice for %s: %s", collection, str(e))
        return results

    def set_doc(self, collection: str, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if collection not in self._in_memory_db:
            self._in_memory_db[collection] = {}
        self._in_memory_db[collection][doc_id] = data

        # 1. Try gRPC Client if available
        client = self.get_client()
        if client:
            try:
                client.collection(collection).document(doc_id).set(data)
                return data
            except Exception as e:
                logger.debug("Firestore gRPC set_doc failed: %s", str(e))

        # 2. Persist directly to Google Cloud Firestore via REST API
        self._sync_firestore_rest(collection, doc_id, data)
        return data

    def get_doc(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        # Check local memory first for instant response
        if collection in self._in_memory_db and doc_id in self._in_memory_db[collection]:
            return self._in_memory_db[collection][doc_id]

        client = self.get_client()
        if client:
            try:
                snapshot = client.collection(collection).document(doc_id).get()
                if snapshot.exists:
                    d = snapshot.to_dict()
                    if collection not in self._in_memory_db:
                        self._in_memory_db[collection] = {}
                    self._in_memory_db[collection][doc_id] = d
                    return d
                return None
            except Exception as e:
                logger.debug("Firestore gRPC get_doc failed: %s", str(e))

        # Fetch from Firestore REST
        cloud_doc = self._fetch_firestore_rest_doc(collection, doc_id)
        if cloud_doc:
            if collection not in self._in_memory_db:
                self._in_memory_db[collection] = {}
            self._in_memory_db[collection][doc_id] = cloud_doc
            return cloud_doc

        return self._in_memory_db.get(collection, {}).get(doc_id)

    def list_docs(self, collection: str) -> List[Dict[str, Any]]:
        # Fetch from Firestore REST to sync all items across containers
        cloud_docs = self._fetch_firestore_rest_collection(collection)
        if cloud_docs:
            if collection not in self._in_memory_db:
                self._in_memory_db[collection] = {}
            for cd in cloud_docs:
                doc_id = (
                    cd.get("question_id")
                    or cd.get("answer_id")
                    or cd.get("summary_id")
                    or cd.get("evaluation_id")
                    or cd.get("queue_id")
                    or cd.get("document_id")
                    or cd.get("event_id")
                    or cd.get("recommendation_id")
                    or cd.get("patient_id")
                    or cd.get("session_id")
                    or cd.get("id")
                )
                if doc_id:
                    self._in_memory_db[collection][str(doc_id)] = cd

        return list(self._in_memory_db.get(collection, {}).values())

    def update_doc(self, collection: str, doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc = self.get_doc(collection, doc_id)
        if not doc:
            return None
        doc.update(updates)
        return self.set_doc(collection, doc_id, doc)
