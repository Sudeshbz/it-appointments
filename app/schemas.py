from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from .models import RoleEnum, AppointmentStatusEnum


# ---------- AUTH / USER ----------

class EmployeeBase(BaseModel):
    full_name: str
    email: EmailStr
    department: Optional[str] = None
    role: RoleEnum = RoleEnum.employee


class EmployeeCreate(EmployeeBase):
    password: str
    company_name: Optional[str] = None  # ilk kayıt için şirket oluşturmak istersen


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    department: Optional[str]
    role: RoleEnum
    company_id: int

    class Config:
        from_attributes = True


# ---------- COMPANY ----------

class CompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- SERVICE ----------

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceOut(ServiceBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None



# ---------- APPOINTMENT ----------

class AppointmentBase(BaseModel):
    service_id: int
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentOut(BaseModel):
    id: int
    company_id: int
    user_id: int
    it_staff_id: Optional[int]= None
    service_id: int
    start_time: datetime
    end_time: datetime
    status: AppointmentStatusEnum
    notes: Optional[str]= None
    created_at: datetime

    class Config:
        from_attributes = True

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatusEnum
    notes: Optional[str] = None


class AppointmentAssignIT(BaseModel):
    it_staff_id: int



# ---------- AUTH TOKEN ----------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    company_id: Optional[int] = None
    role: Optional[RoleEnum] = None
