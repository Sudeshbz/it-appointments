# app/queue.py

from redis import Redis
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app import models


from app.ai import predict_category 


redis_conn = Redis.from_url(settings.REDIS_URL)
queue = Queue("default", connection=redis_conn)

engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def process_appointment_ai(appointment_id: int):
    print(f"🤖 [AI WORKER] İşleme başlandı. ID: {appointment_id}")
    
    db = SessionLocal()
    
    try:
        appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
        
        if not appointment:
            print(f"[AI WORKER] Randevu bulunamadı: {appointment_id}")
            return

      
        if not appointment.notes:
            print("[AI WORKER] Not boş, analiz yapılmadı.")
            return

        
        category_prediction = predict_category(appointment.notes)
        
        
        category_tag = f"[{category_prediction.upper()}]"

       
        if not appointment.notes.startswith("["):
            appointment.notes = f"{category_tag} {appointment.notes}"
            db.commit()
            print(f"[AI WORKER] Tamamlandı. Tahmin: {category_prediction}")
        else:
            print(f"AI WORKER] Zaten etiketli: {appointment.notes[:10]}...")
            
    except Exception as e:
        print(f"[AI WORKER ERROR] Beklenmedik hata: {e}")
        db.rollback()
    finally:
        db.close()