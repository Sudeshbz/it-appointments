# app/routers/appointments.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

# 🔴 DÜZELTME 1: Testlerin (pytest) çalışması için "app." ile başlayan absolute import kullanıyoruz.
from app import models, schemas
from app.database import get_db
from app.deps import get_current_user
from app.queue import queue  # Sadece kuyruk bağlantısını alıyoruz

# Worker fonksiyonunu import etmeye gerek yok, string olarak vereceğiz (Daha güvenli)
# from app.worker import process_appointment_ai 

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"],
)

# -------------------------------------------------
# 1) RANDEVU OLUŞTUR (PRODUCER - KUYRUĞA ATAR)
# -------------------------------------------------
@router.post("/", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_in: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    # 1. Saat kontrolü (Basit mantık)
    if appointment_in.end_time <= appointment_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitiş zamanı başlangıçtan sonra olmalıdır.",
        )

    # 2. Hizmet kontrolü (Bu hizmet bizim şirkette mi?)
    service = (
        db.query(models.Service)
        .filter(
            models.Service.id == appointment_in.service_id,
            models.Service.company_id == current_user.company_id,
        )
        .first()
    )
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı veya şirketinize ait değil.",
        )

    # 3. Veritabanına Kaydet (Status: Pending)
    appointment = models.Appointment(
        company_id=current_user.company_id,
        user_id=current_user.id,
        it_staff_id=None,
        service_id=appointment_in.service_id,
        start_time=appointment_in.start_time,
        end_time=appointment_in.end_time,
        status=models.AppointmentStatusEnum.pending,
        notes=appointment_in.notes,
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)


    try:
        queue.enqueue(
            "app.queue.process_appointment_ai", 
            appointment_id=appointment.id
        )
    except Exception as e:
        print(f"[QUEUE ERROR] Redis kuyruğuna eklenemedi: {e}")

    return appointment


# -------------------------------------------------
# 2) KULLANICININ KENDİ RANDEVULARI
# -------------------------------------------------
@router.get("/me", response_model=List[schemas.AppointmentOut])
def list_my_appointments(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    appointments = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.company_id == current_user.company_id,
            models.Appointment.user_id == current_user.id,
        )
        .order_by(models.Appointment.start_time.desc())
        .all()
    )
    return appointments


# -------------------------------------------------
# 3) ŞİRKETTEKİ TÜM RANDEVULAR (Admin / IT Staff)
# -------------------------------------------------
@router.get("/", response_model=List[schemas.AppointmentOut])
def list_company_appointments(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    # Yetki Kontrolü (RBAC)
    if current_user.role not in [models.RoleEnum.admin, models.RoleEnum.it_staff]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu listeyi görmeye yetkiniz yok.",
        )

    appointments = (
        db.query(models.Appointment)
        .filter(models.Appointment.company_id == current_user.company_id)
        .order_by(models.Appointment.start_time.desc())
        .all()
    )
    return appointments


# -------------------------------------------------
# 4) RANDEVUYA IT PERSONELİ ATA
# -------------------------------------------------
@router.patch("/{appointment_id}/assign-it", response_model=schemas.AppointmentOut)
def assign_it_staff(
    appointment_id: int,
    data: schemas.AppointmentAssignIT,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    if current_user.role not in [models.RoleEnum.admin, models.RoleEnum.it_staff]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Atama yapmaya yetkiniz yok.",
        )

    appointment = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id,
            models.Appointment.company_id == current_user.company_id,
        )
        .first()
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Randevu bulunamadı.",
        )

    # IT Personeli kontrolü
    it_staff = (
        db.query(models.Employee)
        .filter(
            models.Employee.id == data.it_staff_id,
            models.Employee.company_id == current_user.company_id,
        )
        .first()
    )
    if not it_staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Atanacak personel bulunamadı.",
        )

    appointment.it_staff_id = data.it_staff_id
    db.commit()
    db.refresh(appointment)
    return appointment


# -------------------------------------------------
# 5) RANDEVU DURUMUNU GÜNCELLE
# -------------------------------------------------
@router.patch("/{appointment_id}/status", response_model=schemas.AppointmentOut)
def update_appointment_status(
    appointment_id: int,
    data: schemas.AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    if current_user.role not in [models.RoleEnum.admin, models.RoleEnum.it_staff]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Durum güncellemeye yetkiniz yok.",
        )

    appointment = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.id == appointment_id,
            models.Appointment.company_id == current_user.company_id,
        )
        .first()
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Randevu bulunamadı.",
        )

    # İş Kuralı: Tamamlanan randevu geri alınamaz
    if appointment.status == models.AppointmentStatusEnum.completed and data.status == models.AppointmentStatusEnum.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tamamlanan bir iş tekrar 'bekliyor' durumuna alınamaz.",
        )

    appointment.status = data.status
    if data.notes:
        appointment.notes = data.notes

    db.commit()
    db.refresh(appointment)
    return appointment