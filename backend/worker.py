from __future__ import annotations

from rq import Connection, Worker

from app.core.config import get_settings
from app.services.queue import get_redis_connection


def main() -> None:
    settings = get_settings()
    redis_connection = get_redis_connection(settings.redis_url)
    with Connection(redis_connection):
        worker = Worker(["enrichment"])
        worker.work()


if __name__ == "__main__":
    main()