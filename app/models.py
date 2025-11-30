from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


# ---------- ENUM TANIMLARI ----------

class RoleEnum(str, enum.Enum):
    employee = "employee"
    it_staff = "it_staff"
    admin = "admin"


class AppointmentStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    cancelled = "cancelled"
    completed = "completed"


# ---------- COMPANY ----------

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, nullable=True)  # abc.com vs.
    created_at = Column(DateTime, default=datetime.utcnow)

    employees = relationship(
        "Employee",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    services = relationship(
        "Service",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    appointments = relationship(
        "Appointment",
        back_populates="company",
        cascade="all, delete-orphan"
    )


# ---------- EMPLOYEE ----------

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.employee, nullable=False)
    department = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="employees")

    created_appointments = relationship(
        "Appointment",
        back_populates="created_by",
        foreign_keys="Appointment.user_id",
    )
    assigned_appointments = relationship(
        "Appointment",
        back_populates="assigned_it",
        foreign_keys="Appointment.it_staff_id",
    )


# ---------- SERVICE ----------

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="services")
    appointments = relationship(
        "Appointment",
        back_populates="service",
        cascade="all, delete-orphan"
    )


# ---------- APPOINTMENT ----------

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    it_staff_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(Enum(AppointmentStatusEnum), default=AppointmentStatusEnum.pending)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="appointments")
    created_by = relationship(
        "Employee",
        foreign_keys=[user_id],
        back_populates="created_appointments",
    )
    assigned_it = relationship(
        "Employee",
        foreign_keys=[it_staff_id],
        back_populates="assigned_appointments",
    )
    service = relationship(
        "Service",
        back_populates="appointments",
    )
