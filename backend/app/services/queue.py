from __future__ import annotations

from functools import lru_cache

from redis import Redis

from app.core.config import Settings, get_settings


@lru_cache
def get_redis_connection(redis_url: str | None = None) -> Redis:
    settings = get_settings()
    return Redis.from_url(redis_url or settings.redis_url)


def enqueue_job_pipeline(job_id: str, settings: Settings | None = None) -> str:
    from rq import Queue

    from app.services.enrichment import run_job_pipeline

    active_settings = settings or get_settings()
    redis_connection = get_redis_connection(active_settings.redis_url)
    queue = Queue("enrichment", connection=redis_connection)
    job = queue.enqueue(run_job_pipeline, job_id, active_settings)
    return job.id