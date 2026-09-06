import logging
import httpx
from typing import Tuple
from app.core.config import settings

logger = logging.getLogger("medikiosk.fallback.health")

async def check_ai4bharat_health() -> Tuple[bool, str]:
    """
    Checks AI4Bharat service availability.
    """
    if not settings.AI4BHARAT_API_KEY:
        return False, "AI4Bharat API key not configured (Development fallback active)"

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(f"{settings.AI4BHARAT_BASE_URL}/health")
            if res.status_code == 200:
                return True, "AI4Bharat operational"
            return False, f"AI4Bharat returned status {res.status_code}"
    except Exception as e:
        logger.info("AI4Bharat health check ping failed: %s", str(e))
        return False, f"AI4Bharat unavailable: {str(e)}"
