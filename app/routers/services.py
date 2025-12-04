import json
from ..config import settings
from redis import Redis


from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(
    prefix="/services",
    tags=["services"],
)


# -------------------------------------------------
# 1) HİZMET OLUŞTUR
# -------------------------------------------------
@router.post("/", response_model=schemas.ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    service_in: schemas.ServiceCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    # Sadece o şirketin içinde hizmet oluştur
    service = models.Service(
        name=service_in.name,
        description=service_in.description,
        company_id=current_user.company_id,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


# Redis bağlantısı (Global olarak bir yerde tanımlamak daha iyi ama hızlı çözüm için buraya alalım)
redis_cache = Redis.from_url(settings.REDIS_URL)

@router.get("/", response_model=List[schemas.ServiceOut])
def list_services(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    # 1. Önce Redis'e bak (Cache Key: company_id'ye özel olmalı!)
    cache_key = f"services_company_{current_user.company_id}"
    cached_data = redis_cache.get(cache_key)

    if cached_data:
        print("[CACHE] Veri Redis'ten geldi ⚡️")
        # Redis'te veri string (JSON) durur, onu listeye çevir
        return json.loads(cached_data)

    # 2. Yoksa Veritabanından Çek
    print("[DB] Veri Veritabanından geldi 🐢")
    services = (
        db.query(models.Service)
        .filter(models.Service.company_id == current_user.company_id)
        .all()
    )

    # 3. Veriyi Redis'e Kaydet (JSON formatında) ve 60 saniye ömür biç
    # Pydantic modellerini dict'e çevirmek için jsonable_encoder gerekebilir ama
    # basitçe manuel serialize edelim:
    services_json = json.dumps([s.dict() for s in services], default=str)
    redis_cache.setex(cache_key, 60, services_json) # 60 saniye cache

    return services


# -------------------------------------------------
# 4) HİZMET GÜNCELLE (PUT)
# -------------------------------------------------
@router.put("/{service_id}", response_model=schemas.ServiceOut)
def update_service(
    service_id: int,
    service_in: schemas.ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    service = (
        db.query(models.Service)
        .filter(
            models.Service.id == service_id,
            models.Service.company_id == current_user.company_id,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı.",
        )

    # Sadece gelen alanları güncelle
    if service_in.name is not None:
        service.name = service_in.name
    if service_in.description is not None:
        service.description = service_in.description

    db.commit()
    db.refresh(service)
    return service


# -------------------------------------------------
# 5) HİZMET SİL (DELETE)
# -------------------------------------------------
@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    service = (
        db.query(models.Service)
        .filter(
            models.Service.id == service_id,
            models.Service.company_id == current_user.company_id,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı.",
        )

    db.delete(service)
    db.commit()
    return None
