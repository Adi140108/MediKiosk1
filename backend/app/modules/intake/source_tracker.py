from typing import Dict, Any, Optional
from app.core.security import SourceType

class SourceTracker:
    @staticmethod
    def tag_source(
        source_type: SourceType,
        attendant_id: Optional[str] = None,
        document_id: Optional[str] = None,
        physician_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates source attribution metadata ensuring full clinical provenance.
        """
        attribution = {
            "source_type": source_type.value if isinstance(source_type, SourceType) else str(source_type)
        }
        if attendant_id:
            attribution["attendant_id"] = attendant_id
        if document_id:
            attribution["document_id"] = document_id
        if physician_id:
            attribution["physician_id"] = physician_id
        return attribution
