# app/queue.py
from redis import Redis
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from . import models
from .ai import predict_category  # 👈 Yazdığımız AI modülünü çağırdık

# Redis Bağlantısı
redis_conn = Redis.from_url(settings.REDIS_URL)
queue = Queue("default", connection=redis_conn)

# Worker'ın veritabanına erişmesi için ayrı bağlantı (Session) kuruyoruz
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def process_appointment_ai(appointment_id: int):
    """
    Bu fonksiyon Worker tarafından arka planda çalıştırılır.
    1. Randevuyu bulur.
    2. Notları AI'a okutur.
    3. Notların başına [AI: Kategori] ekler.
    """
    db = SessionLocal()
    try:
        appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
        if not appointment or not appointment.notes:
            print(f"[AI WORKER] Randevu {appointment_id} için not bulunamadı.")
            return

        # Yapay Zeka Tahmini Yap
        category = predict_category(appointment.notes)
        print(f"[AI WORKER] Randevu: {appointment_id} -> Tahmin: {category}")

        # Veritabanını güncelle
        # Notun başına tahmini ekliyoruz: "[DONANIM] Bilgisayarım bozuldu..."
        appointment.notes = f"[{category.upper()}] {appointment.notes}"
        db.commit()
        
    except Exception as e:
        print(f"[AI WORKER ERROR] Hata: {e}")
    finally:
        db.close()