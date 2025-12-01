# app/queue.py
from redis import Redis
from rq import Queue
from .config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
queue = Queue("default", connection=redis_conn)


def send_appointment_created_email(appointment_id: int, user_email: str):
    # Buraya şimdilik sadece log atabiliriz, gerçek e-posta sistemi sonra eklenir
    print(f"[QUEUE] Appointment created: id={appointment_id}, email={user_email}")
