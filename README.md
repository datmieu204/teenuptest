# Mini LMS - Product Builder Test

Ung dung web mini quan ly:
- Parent + Student
- Classes va class registration
- Subscription theo doi so buoi da dung/con lai

## 1) Tech Stack
- Backend: Python + FastAPI + SQLAlchemy
- Frontend: React + Vite
- Database: PostgreSQL
- DevOps: Docker, Docker Compose

## 2) Project Structure
- `backend/`: FastAPI REST API + SQLAlchemy models + seed
- `frontend/`: UI React
- `docker-compose.yml`: chay dong thoi db + backend + frontend
- `run.sh`: script thao tac nhanh

## 3) Database Schema
Tat ca model co trong `backend/app/models.py`:
- Parents: id, name, phone, email
- Students: id, name, dob, gender, current_grade, parent_id
- Classes: id, name, subject, day_of_week, time_slot, teacher_name, max_students
- ClassRegistrations: id, class_id, student_id
- Subscriptions: id, student_id, package_name, start_date, end_date, total_sessions, used_sessions

## 4) API Endpoints Chinh
Base URL: `http://localhost:4000/api`

### Parents
- `POST /parents`
- `GET /parents/{id}`

### Students
- `POST /students`
- `GET /students/{id}` (include parent)

### Classes
- `POST /classes`
- `GET /classes?day={weekday}`

### ClassRegistrations
- `POST /classes/{class_id}/register`
  - Check si so (`max_students`)
  - Check trung lich cung `day_of_week` va overlap `time_slot`
  - Check subscription con han + con buoi (`used_sessions < total_sessions`)
- `DELETE /registrations/{id}`
  - Huy truoc >24h: refund 1 buoi (`used_sessions - 1`)
  - Huy sat gio <24h: khong refund

### Subscriptions
- `POST /subscriptions`
- `PATCH /subscriptions/{id}/use`
- `GET /subscriptions/{id}`

## 5) Seed Data
Seed script trong `backend/app/seed.py` tao:
- 2 parents
- 3 students
- 3 classes
- 3 subscriptions

## 6) Run With Docker
### Cach 1: dung script
```bash
cd test
chmod +x run.sh
./run.sh up
```

### Cach 2: dung docker compose
```bash
cd test
docker compose up --build
```

Dich vu sau khi chay:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:4000/api`
- Health check: `http://localhost:4000/health`
- PostgreSQL: `localhost:5432` (`postgres/postgres`)

Tat:
```bash
./run.sh down
```

Reset DB volume:
```bash
./run.sh reset
```

## 7) Example curl
### Tao parent
```bash
curl -X POST http://localhost:4000/api/parents \
  -H "Content-Type: application/json" \
  -d '{"name":"Nguyen Van C","phone":"0901999999","email":"parent.c@example.com"}'
```

### Tao student
```bash
curl -X POST http://localhost:4000/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Tran Minh","dob":"2014-05-01","gender":"male","current_grade":"Grade 6","parent_id":1}'
```

### Tao class
```bash
curl -X POST http://localhost:4000/api/classes \
  -H "Content-Type: application/json" \
  -d '{"name":"Math Pro","subject":"Math","day_of_week":"monday","time_slot":"18:00-19:30","teacher_name":"Teacher A","max_students":20}'
```

### Dang ky hoc sinh vao lop
```bash
curl -X POST http://localhost:4000/api/classes/1/register \
  -H "Content-Type: application/json" \
  -d '{"student_id":1}'
```

### Huy dang ky
```bash
curl -X DELETE http://localhost:4000/api/registrations/1
```
