# app/routers/appointments.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

# 🔴 KRİTİK DÜZELTME: Eski mail fonksiyonu yerine AI worker fonksiyonunu çağırıyoruz
from ..queue import queue, process_appointment_ai

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"],
)


# -------------------------------------------------
# 1) RANDEVU OLUŞTUR (AI TETİKLENİR)
# -------------------------------------------------
@router.post("/", response_model=schemas.AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_in: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    # Saat kontrolü
    if appointment_in.end_time <= appointment_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitiş zamanı başlangıçtan sonra olmalıdır.",
        )

    # Hizmet bu şirketin mi?
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
            detail="Hizmet bulunamadı veya sizin şirketinize ait değil.",
        )

    # Randevuyu veritabanına kaydet (Status: Pending)
    appointment = models.Appointment(
        company_id=current_user.company_id,
        user_id=current_user.id,
        it_staff_id=None,  # Henüz kimse atanmadı
        service_id=appointment_in.service_id,
        start_time=appointment_in.start_time,
        end_time=appointment_in.end_time,
        status=models.AppointmentStatusEnum.pending,
        notes=appointment_in.notes,
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # 🔴 AI ENTEGRASYONU: Randevu ID'sini kuyruğa atıyoruz
    # Worker bunu alıp notları okuyacak ve [DONANIM] gibi etiket ekleyecek.
    try:
        queue.enqueue(
            process_appointment_ai,
            appointment_id=appointment.id
        )
    except Exception as e:
        # Kuyruk hatası API'yi çökertmesin, sadece loglasın
        print(f"[QUEUE ERROR] AI Job oluşturulamadı: {e}")

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
# 3) ŞİRKETTEKİ TÜM RANDEVULAR (Sadece Admin / IT Staff)
# -------------------------------------------------
@router.get("/", response_model=List[schemas.AppointmentOut])
def list_company_appointments(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    if current_user.role not in [models.RoleEnum.admin, models.RoleEnum.it_staff]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        )

    appointments = (
        db.query(models.Appointment)
        .filter(models.Appointment.company_id == current_user.company_id)
        .order_by(models.Appointment.start_time.desc())
        .all()
    )
    return appointments


# -------------------------------------------------
# 4) RANDEVUYA IT PERSONELİ ATA (Admin / IT Staff)
# -------------------------------------------------
@router.patch("/{appointment_id}/assign-it", response_model=schemas.AppointmentOut)
def assign_it_staff(
    appointment_id: int,
    data: schemas.AppointmentAssignIT,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    # Yetki Kontrolü
    if current_user.role not in [models.RoleEnum.admin, models.RoleEnum.it_staff]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IT personeli atamak için yetkiniz yok.",
        )

    # Randevuyu Bul
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

    # Atanacak personel bu şirkette mi?
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
            detail="Atanacak IT personeli bulunamadı.",
        )

    appointment.it_staff_id = data.it_staff_id
    db.commit()
    db.refresh(appointment)
    return appointment


# -------------------------------------------------
# 5) RANDEVU DURUMUNU GÜNCELLE (Admin / IT Staff)
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
            detail="Randevu durumunu değiştirmek için yetkiniz yok.",
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

    # Basit iş kuralı: Tamamlanan tekrar pending olamaz
    if appointment.status == models.AppointmentStatusEnum.completed and data.status == models.AppointmentStatusEnum.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tamamlanan bir randevu tekrar 'pending' yapılamaz.",
        )

    appointment.status = data.status
    if data.notes is not None:
        appointment.notes = data.notes

    db.commit()
    db.refresh(appointment)
    return appointment