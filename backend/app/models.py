from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Parent(Base):
    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    students: Mapped[list["Student"]] = relationship(back_populates="parent", cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    current_grade: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parents.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent: Mapped[Parent] = relationship(back_populates="students")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    registrations: Mapped[list["ClassRegistration"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    time_slot: Mapped[str] = mapped_column(String(20), nullable=False)
    teacher_name: Mapped[str] = mapped_column(String(255), nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations: Mapped[list["ClassRegistration"]] = relationship(back_populates="class_ref", cascade="all, delete-orphan")


class ClassRegistration(Base):
    __tablename__ = "class_registrations"
    __table_args__ = (UniqueConstraint("class_id", "student_id", name="uq_class_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    class_ref: Mapped[Class] = relationship(back_populates="registrations")
    student: Mapped[Student] = relationship(back_populates="registrations")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    used_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student: Mapped[Student] = relationship(back_populates="subscriptions")
