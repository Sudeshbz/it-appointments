
from redis import Redis
from rq import Worker, Queue, Connection
from .config import settings
from .database import SessionLocal
from . import models


listen = ["default"]
redis_conn = Redis.from_url(settings.REDIS_URL)


def process_appointment_ai(appointment_id: int):
    print(f"🤖 [AI WORKER] İş alındı. Randevu ID: {appointment_id} analiz ediliyor...")
    
    
    db = SessionLocal()
    
    try:
        appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
        
        if not appointment:
            print(f"[AI WORKER] Hata: Randevu {appointment_id} bulunamadı.")
            return

       
        
        original_note = appointment.notes.lower() if appointment.notes else ""
        predicted_category = "[GENEL]" 

        if any(word in original_note for word in ["ekran", "klavye", "mouse", "kırık", "kablo", "ısınma", "bilgisayar"]):
            predicted_category = "[DONANIM]"
        elif any(word in original_note for word in ["yazılım", "format", "lisans", "office", "virüs", "hata", "yavaş"]):
            predicted_category = "[YAZILIM]"
        elif any(word in original_note for word in ["internet", "wifi", "modem", "ağ", "bağlantı"]):
            predicted_category = "[AĞ/NETWORK]"

       
        if not appointment.notes.startswith("["):
            appointment.notes = f"{predicted_category} {appointment.notes}"
            db.commit()
            print(f"[AI WORKER] Başarılı! Kategori atandı: {predicted_category}")
        else:
            print("[AI WORKER] Zaten etiketlenmiş, işlem yapılmadı.")

    except Exception as e:
        print(f"💥 [AI WORKER] Beklenmedik hata: {e}")
        db.rollback() 
    finally:
        db.close() 


if __name__ == "__main__":
    print("🚀 Worker başlatılıyor... Redis dinleniyor...")
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        worker.work()