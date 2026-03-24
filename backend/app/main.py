from datetime import datetime, time, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .database import Base, engine, get_db
from .models import Class, ClassRegistration, Parent, Student, Subscription
from .schemas import (
    ClassCreate,
    ClassOut,
    ParentCreate,
    ParentOut,
    RegistrationCreate,
    RegistrationOut,
    StudentCreate,
    StudentDetailOut,
    StudentOut,
    SubscriptionCreate,
    SubscriptionOut,
    SubscriptionStatusOut,
)
from .seed import seed_if_needed

DAY_MAP = {
    "sunday": 0,
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
}

app = FastAPI(title="Mini LMS API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_if_needed()


@app.get("/health")
def health_check():
    return {"ok": True}


def parse_day_value(day_value: str | int | None) -> int | None:
    if day_value is None:
        return None

    if isinstance(day_value, int):
        return day_value if 0 <= day_value <= 6 else None

    normalized = str(day_value).strip().lower()
    if normalized in DAY_MAP:
        return DAY_MAP[normalized]

    if normalized.isdigit():
        value = int(normalized)
        return value if 0 <= value <= 6 else None

    return None


def parse_time_slot(slot: str) -> tuple[time, time] | None:
    parts = [p.strip() for p in slot.split("-")]
    if len(parts) != 2:
        return None

    try:
        start = time.fromisoformat(parts[0])
        end = time.fromisoformat(parts[1])
    except ValueError:
        return None

    if end <= start:
        return None

    return start, end


def is_overlap(a: tuple[time, time], b: tuple[time, time]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def next_class_datetime(day_of_week: int, start: time) -> datetime:
    now = datetime.utcnow()
    target = now.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
    today_api_day = (now.weekday() + 1) % 7
    diff = (day_of_week - today_api_day + 7) % 7
    target = target + timedelta(days=diff)
    if target <= now:
        target = target + timedelta(days=7)
    return target


def get_active_subscription(db: Session, student_id: int) -> Subscription | None:
    now = datetime.utcnow()
    stmt = (
        select(Subscription)
        .where(
            and_(
                Subscription.student_id == student_id,
                Subscription.start_date <= now,
                Subscription.end_date >= now,
                Subscription.used_sessions < Subscription.total_sessions,
            )
        )
        .order_by(Subscription.end_date.asc())
    )
    return db.scalars(stmt).first()


@app.post("/api/parents", response_model=ParentOut, status_code=201)
def create_parent(payload: ParentCreate, db: Session = Depends(get_db)):
    parent = Parent(name=payload.name, phone=payload.phone, email=payload.email)
    db.add(parent)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")
    db.refresh(parent)
    return parent


@app.get("/api/parents/{parent_id}")
def get_parent(parent_id: int, db: Session = Depends(get_db)):
    parent = db.get(Parent, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    students = db.scalars(select(Student).where(Student.parent_id == parent_id)).all()
    return {
        "id": parent.id,
        "name": parent.name,
        "phone": parent.phone,
        "email": parent.email,
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "dob": s.dob,
                "gender": s.gender,
                "current_grade": s.current_grade,
                "parent_id": s.parent_id,
            }
            for s in students
        ],
    }


@app.get("/api/parents", response_model=list[ParentOut])
def list_parents(db: Session = Depends(get_db)):
    return db.scalars(select(Parent).order_by(Parent.id.asc())).all()


@app.post("/api/students", response_model=StudentOut, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if not db.get(Parent, payload.parent_id):
        raise HTTPException(status_code=404, detail="Parent not found")

    student = Student(
        name=payload.name,
        dob=datetime.combine(payload.dob, time.min),
        gender=payload.gender,
        current_grade=payload.current_grade,
        parent_id=payload.parent_id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/api/students/{student_id}", response_model=StudentDetailOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    stmt = select(Student).options(joinedload(Student.parent)).where(Student.id == student_id)
    student = db.scalars(stmt).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.get("/api/students", response_model=list[StudentDetailOut])
def list_students(db: Session = Depends(get_db)):
    stmt = select(Student).options(joinedload(Student.parent)).order_by(Student.id.asc())
    return db.scalars(stmt).all()


@app.post("/api/classes", response_model=ClassOut, status_code=201)
def create_class(payload: ClassCreate, db: Session = Depends(get_db)):
    day_value = parse_day_value(payload.day_of_week)
    if day_value is None:
        raise HTTPException(status_code=400, detail="day_of_week must be 0-6 or weekday name")

    parsed = parse_time_slot(payload.time_slot)
    if not parsed:
        raise HTTPException(status_code=400, detail="time_slot must be in HH:MM-HH:MM format")

    class_item = Class(
        name=payload.name,
        subject=payload.subject,
        day_of_week=day_value,
        time_slot=f"{parsed[0].strftime('%H:%M')}-{parsed[1].strftime('%H:%M')}",
        teacher_name=payload.teacher_name,
        max_students=payload.max_students,
    )
    db.add(class_item)
    db.commit()
    db.refresh(class_item)
    return class_item


@app.get("/api/classes", response_model=list[ClassOut])
def list_classes(day: str | None = Query(default=None), db: Session = Depends(get_db)):
    stmt = select(Class)
    if day is not None:
        day_value = parse_day_value(day)
        if day_value is None:
            raise HTTPException(status_code=400, detail="day must be 0-6 or weekday name")
        stmt = stmt.where(Class.day_of_week == day_value)

    stmt = stmt.order_by(Class.day_of_week.asc(), Class.time_slot.asc())
    return db.scalars(stmt).all()


@app.post("/api/classes/{class_id}/register", response_model=RegistrationOut, status_code=201)
def register_student(class_id: int, payload: RegistrationCreate, db: Session = Depends(get_db)):
    class_item = db.get(Class, class_id)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")

    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    current_size = db.scalar(
        select(func.count(ClassRegistration.id)).where(ClassRegistration.class_id == class_id)
    )
    if current_size >= class_item.max_students:
        raise HTTPException(status_code=400, detail="Class is full")

    target_slot = parse_time_slot(class_item.time_slot)
    if not target_slot:
        raise HTTPException(status_code=400, detail="Class has invalid time_slot")

    reg_stmt = (
        select(ClassRegistration)
        .options(joinedload(ClassRegistration.class_ref))
        .where(ClassRegistration.student_id == payload.student_id)
    )
    registrations = db.scalars(reg_stmt).all()

    for reg in registrations:
        if reg.class_ref.day_of_week != class_item.day_of_week:
            continue
        slot = parse_time_slot(reg.class_ref.time_slot)
        if slot and is_overlap(slot, target_slot):
            raise HTTPException(status_code=400, detail="Student has another class at the same time")

    subscription = get_active_subscription(db, payload.student_id)
    if not subscription:
        raise HTTPException(status_code=400, detail="No active subscription with remaining sessions")

    registration = ClassRegistration(class_id=class_id, student_id=payload.student_id)
    db.add(registration)
    subscription.used_sessions += 1

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Student already registered in this class")

    db.refresh(registration)
    return registration


@app.delete("/api/registrations/{registration_id}")
def cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(ClassRegistration)
        .options(joinedload(ClassRegistration.class_ref), joinedload(ClassRegistration.student).joinedload(Student.subscriptions))
        .where(ClassRegistration.id == registration_id)
    )
    registration = db.scalars(stmt).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    slot = parse_time_slot(registration.class_ref.time_slot)
    if not slot:
        raise HTTPException(status_code=400, detail="Class has invalid time_slot")

    class_start = next_class_datetime(registration.class_ref.day_of_week, slot[0])
    should_refund = (class_start - datetime.utcnow()) > timedelta(hours=24)

    db.delete(registration)

    if should_refund:
        refundable = sorted(
            [s for s in registration.student.subscriptions if s.used_sessions > 0],
            key=lambda s: s.end_date,
            reverse=True,
        )
        if refundable:
            refundable[0].used_sessions -= 1

    db.commit()
    if should_refund:
        return {"message": "Registration cancelled and one session refunded"}
    return {"message": "Registration cancelled with no refund"}


@app.post("/api/subscriptions", response_model=SubscriptionOut, status_code=201)
def create_subscription(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    if not db.get(Student, payload.student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    subscription = Subscription(
        student_id=payload.student_id,
        package_name=payload.package_name,
        start_date=datetime.combine(payload.start_date, time.min),
        end_date=datetime.combine(payload.end_date, time.max),
        total_sessions=payload.total_sessions,
        used_sessions=payload.used_sessions,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@app.patch("/api/subscriptions/{subscription_id}/use", response_model=SubscriptionOut)
def use_subscription_session(subscription_id: int, db: Session = Depends(get_db)):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    now = datetime.utcnow()
    if now < subscription.start_date or now > subscription.end_date:
        raise HTTPException(status_code=400, detail="Subscription is not active")

    if subscription.used_sessions >= subscription.total_sessions:
        raise HTTPException(status_code=400, detail="No remaining sessions")

    subscription.used_sessions += 1
    db.commit()
    db.refresh(subscription)
    return subscription


@app.get("/api/subscriptions/{subscription_id}", response_model=SubscriptionStatusOut)
def get_subscription(subscription_id: int, db: Session = Depends(get_db)):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {
        "id": subscription.id,
        "student_id": subscription.student_id,
        "package_name": subscription.package_name,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "total_sessions": subscription.total_sessions,
        "used_sessions": subscription.used_sessions,
        "remaining_sessions": subscription.total_sessions - subscription.used_sessions,
    }


@app.get("/api/registrations")
def list_registrations(db: Session = Depends(get_db)):
    stmt = (
        select(ClassRegistration)
        .options(joinedload(ClassRegistration.student), joinedload(ClassRegistration.class_ref))
        .order_by(ClassRegistration.id.asc())
    )
    rows = db.scalars(stmt).all()
    return [
        {
            "id": row.id,
            "class_id": row.class_id,
            "student_id": row.student_id,
            "student": {
                "id": row.student.id,
                "name": row.student.name,
            },
            "class": {
                "id": row.class_ref.id,
                "name": row.class_ref.name,
                "day_of_week": row.class_ref.day_of_week,
                "time_slot": row.class_ref.time_slot,
            },
        }
        for row in rows
    ]
