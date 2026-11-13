"""健康检查：db / redis / worker 心跳。"""
from __future__ import annotations

from fastapi import APIRouter

from src.config.database import ping_db
from src.config.settings import settings

router = APIRouter(tags=["health"])


def _redis_state() -> tuple[bool, float | None]:
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)
        alive = bool(client.ping())
        raw = client.get("sampleaqp:worker:heartbeat")
        return alive, float(raw) if raw else None
    except Exception:
        return False, None


@router.get("/health")
def health() -> dict:
    db_ok = ping_db()
    redis_ok, heartbeat = _redis_state()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": db_ok,
        "redis": redis_ok,
        "worker_heartbeat": heartbeat,
        "brand": "sampleaqp",
    }
