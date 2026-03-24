from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class ParentCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr


class ParentOut(BaseModel):
    id: int
    name: str
    phone: str
    email: EmailStr

    class Config:
        from_attributes = True


class StudentCreate(BaseModel):
    name: str
    dob: date
    gender: str
    current_grade: str
    parent_id: int


class StudentOut(BaseModel):
    id: int
    name: str
    dob: datetime
    gender: str
    current_grade: str
    parent_id: int

    class Config:
        from_attributes = True


class StudentDetailOut(StudentOut):
    parent: ParentOut


class ClassCreate(BaseModel):
    name: str
    subject: str
    day_of_week: int | str
    time_slot: str
    teacher_name: str
    max_students: int = Field(gt=0)


class ClassOut(BaseModel):
    id: int
    name: str
    subject: str
    day_of_week: int
    time_slot: str
    teacher_name: str
    max_students: int

    class Config:
        from_attributes = True


class RegistrationCreate(BaseModel):
    student_id: int


class RegistrationOut(BaseModel):
    id: int
    class_id: int
    student_id: int

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    student_id: int
    package_name: str
    start_date: date
    end_date: date
    total_sessions: int = Field(gt=0)
    used_sessions: int = Field(default=0, ge=0)


class SubscriptionOut(BaseModel):
    id: int
    student_id: int
    package_name: str
    start_date: datetime
    end_date: datetime
    total_sessions: int
    used_sessions: int

    class Config:
        from_attributes = True


class SubscriptionStatusOut(SubscriptionOut):
    remaining_sessions: int
