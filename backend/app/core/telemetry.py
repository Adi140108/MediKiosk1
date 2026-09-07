import time
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger("medikiosk.telemetry")

class PerformanceContext:
    def __init__(self, endpoint: str = "", method: str = ""):
        self.endpoint = endpoint
        self.method = method
        self.request_start = datetime.now(timezone.utc).isoformat()
        self.request_start_perf = time.perf_counter()
        self.request_end: Optional[str] = None
        self.total_duration_ms: float = 0.0
        
        # Sub-duration timers (in milliseconds)
        self.database_duration_ms: float = 0.0
        self.storage_duration_ms: float = 0.0
        self.ocr_duration_ms: float = 0.0
        self.ai_duration_ms: float = 0.0
        self.translation_duration_ms: float = 0.0
        self.status_code: int = 200

    def finish(self, status_code: int = 200) -> Dict[str, Any]:
        self.status_code = status_code
        self.request_end = datetime.now(timezone.utc).isoformat()
        self.total_duration_ms = round((time.perf_counter() - self.request_start_perf) * 1000, 2)
        
        # Round sub-durations
        self.database_duration_ms = round(self.database_duration_ms, 2)
        self.storage_duration_ms = round(self.storage_duration_ms, 2)
        self.ocr_duration_ms = round(self.ocr_duration_ms, 2)
        self.ai_duration_ms = round(self.ai_duration_ms, 2)
        self.translation_duration_ms = round(self.translation_duration_ms, 2)

        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "status_code": self.status_code,
            "request_start": self.request_start,
            "request_end": self.request_end,
            "total_duration_ms": self.total_duration_ms,
            "database_duration_ms": self.database_duration_ms,
            "storage_duration_ms": self.storage_duration_ms,
            "ocr_duration_ms": self.ocr_duration_ms,
            "ai_duration_ms": self.ai_duration_ms,
            "translation_duration_ms": self.translation_duration_ms
        }

class SubTimer:
    def __init__(self, tracker: 'PerformanceTracker', subsystem: str):
        self.tracker = tracker
        self.subsystem = subsystem
        self.start = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.perf_counter() - self.start) * 1000
        ctx = self.tracker.get_current_context()
        if ctx:
            if self.subsystem == "database":
                ctx.database_duration_ms += elapsed_ms
            elif self.subsystem == "storage":
                ctx.storage_duration_ms += elapsed_ms
            elif self.subsystem == "ocr":
                ctx.ocr_duration_ms += elapsed_ms
            elif self.subsystem == "ai":
                ctx.ai_duration_ms += elapsed_ms
            elif self.subsystem == "translation":
                ctx.translation_duration_ms += elapsed_ms

class PerformanceTracker:
    _current_context: ContextVar[Optional[PerformanceContext]] = ContextVar("medikiosk_perf_ctx", default=None)
    _recent_traces: deque = deque(maxlen=100)

    @classmethod
    def start_request(cls, endpoint: str, method: str) -> PerformanceContext:
        ctx = PerformanceContext(endpoint=endpoint, method=method)
        cls._current_context.set(ctx)
        return ctx

    @classmethod
    def get_current_context(cls) -> Optional[PerformanceContext]:
        return cls._current_context.get()

    @classmethod
    def end_request(cls, status_code: int = 200) -> Optional[Dict[str, Any]]:
        ctx = cls.get_current_context()
        if ctx:
            data = ctx.finish(status_code=status_code)
            cls._recent_traces.append(data)
            cls._current_context.set(None)
            return data
        return None

    @classmethod
    def measure(cls, subsystem: str) -> SubTimer:
        return SubTimer(cls, subsystem)

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        traces = list(cls._recent_traces)
        if not traces:
            return {
                "total_requests_recorded": 0,
                "p50_duration_ms": 0.0,
                "p95_duration_ms": 0.0,
                "p99_duration_ms": 0.0,
                "avg_duration_ms": 0.0,
                "subsystem_averages_ms": {
                    "database": 0.0,
                    "storage": 0.0,
                    "ocr": 0.0,
                    "ai": 0.0,
                    "translation": 0.0
                },
                "slowest_endpoints": [],
                "recent_traces": []
            }

        durations = sorted([t["total_duration_ms"] for t in traces])
        n = len(durations)
        p50 = durations[int(n * 0.50)]
        p95 = durations[min(int(n * 0.95), n - 1)]
        p99 = durations[min(int(n * 0.99), n - 1)]
        avg_total = round(sum(durations) / n, 2)

        avg_db = round(sum(t["database_duration_ms"] for t in traces) / n, 2)
        avg_storage = round(sum(t["storage_duration_ms"] for t in traces) / n, 2)
        avg_ocr = round(sum(t["ocr_duration_ms"] for t in traces) / n, 2)
        avg_ai = round(sum(t["ai_duration_ms"] for t in traces) / n, 2)
        avg_trans = round(sum(t["translation_duration_ms"] for t in traces) / n, 2)

        # Group by endpoint
        endpoint_groups: Dict[str, List[float]] = {}
        for t in traces:
            ep = f"{t['method']} {t['endpoint']}"
            endpoint_groups.setdefault(ep, []).append(t["total_duration_ms"])

        slowest = [
            {
                "endpoint": ep,
                "count": len(durs),
                "avg_duration_ms": round(sum(durs) / len(durs), 2),
                "max_duration_ms": max(durs)
            }
            for ep, durs in endpoint_groups.items()
        ]
        slowest.sort(key=lambda x: x["avg_duration_ms"], reverse=True)

        return {
            "total_requests_recorded": n,
            "p50_duration_ms": p50,
            "p95_duration_ms": p95,
            "p99_duration_ms": p99,
            "avg_duration_ms": avg_total,
            "subsystem_averages_ms": {
                "database": avg_db,
                "storage": avg_storage,
                "ocr": avg_ocr,
                "ai": avg_ai,
                "translation": avg_trans
            },
            "slowest_endpoints": slowest[:5],
            "recent_traces": traces[-20:]
        }

# Global singleton
telemetry = PerformanceTracker
