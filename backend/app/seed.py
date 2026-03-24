from datetime import datetime, timedelta
from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import Class, Parent, Student, Subscription


def seed_if_needed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        has_parent = db.scalar(select(Parent.id).limit(1))
        if has_parent:
            return

        parent_a = Parent(name="Nguyen Van A", phone="0901000001", email="parent.a@example.com")
        parent_b = Parent(name="Tran Thi B", phone="0901000002", email="parent.b@example.com")
        db.add_all([parent_a, parent_b])
        db.flush()

        student_1 = Student(
            name="Pham Minh Khang",
            dob=datetime(2014, 2, 10),
            gender="male",
            current_grade="Grade 6",
            parent_id=parent_a.id,
        )
        student_2 = Student(
            name="Le Bao Chau",
            dob=datetime(2015, 9, 15),
            gender="female",
            current_grade="Grade 5",
            parent_id=parent_a.id,
        )
        student_3 = Student(
            name="Do Anh Thu",
            dob=datetime(2013, 12, 1),
            gender="female",
            current_grade="Grade 7",
            parent_id=parent_b.id,
        )
        db.add_all([student_1, student_2, student_3])
        db.flush()

        classes = [
            Class(
                name="Math Foundation",
                subject="Math",
                day_of_week=1,
                time_slot="18:00-19:30",
                teacher_name="Teacher Linh",
                max_students=20,
            ),
            Class(
                name="Science Explorer",
                subject="Science",
                day_of_week=3,
                time_slot="18:00-19:30",
                teacher_name="Teacher Huy",
                max_students=15,
            ),
            Class(
                name="English Speaking",
                subject="English",
                day_of_week=5,
                time_slot="19:00-20:30",
                teacher_name="Teacher Mai",
                max_students=12,
            ),
        ]
        db.add_all(classes)

        now = datetime.utcnow()
        next_month = now + timedelta(days=30)
        subscriptions = [
            Subscription(
                student_id=student_1.id,
                package_name="Starter 12",
                start_date=now,
                end_date=next_month,
                total_sessions=12,
                used_sessions=2,
            ),
            Subscription(
                student_id=student_2.id,
                package_name="Starter 8",
                start_date=now,
                end_date=next_month,
                total_sessions=8,
                used_sessions=0,
            ),
            Subscription(
                student_id=student_3.id,
                package_name="Premium 16",
                start_date=now,
                end_date=next_month,
                total_sessions=16,
                used_sessions=5,
            ),
        ]
        db.add_all(subscriptions)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_if_needed()
