from redis import Redis
from rq import Worker, Queue
from .config import settings

listen = ["default"]

redis_conn = Redis.from_url(settings.REDIS_URL)


if __name__ == "__main__":
    queues = [Queue(name, connection=redis_conn) for name in listen]

    worker = Worker(queues, connection=redis_conn)
    worker.work()
