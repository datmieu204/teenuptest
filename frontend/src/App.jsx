import { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4000/api";
const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json"
    },
    ...options
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Request failed (${response.status})`);
  }

  return response.json();
}

function useForm(initial) {
  const [form, setForm] = useState(initial);
  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };
  const reset = () => setForm(initial);
  return { form, onChange, setForm, reset };
}

export default function App() {
  const parentForm = useForm({ name: "", phone: "", email: "" });
  const studentForm = useForm({
    name: "",
    dob: "",
    gender: "male",
    current_grade: "",
    parent_id: ""
  });

  const [parents, setParents] = useState([]);
  const [students, setStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [registerStudentByClass, setRegisterStudentByClass] = useState({});

  const classByDay = useMemo(() => {
    const map = new Map(DAYS.map((_, idx) => [idx, []]));
    const classList = Array.isArray(classes) ? classes : [];
    for (const item of classList) {
      const dayIndex = Number(item.day_of_week);
      if (Number.isInteger(dayIndex) && dayIndex >= 0 && dayIndex <= 6) {
        map.get(dayIndex)?.push(item);
      }
    }
    for (const list of map.values()) {
      list.sort((a, b) => (a.time_slot || "").localeCompare(b.time_slot || ""));
    }
    return map;
  }, [classes]);

  function normalizeClassItem(item) {
    return {
      ...item,
      day_of_week: item.day_of_week ?? item.dayOfWeek,
      time_slot: item.time_slot ?? item.timeSlot,
      teacher_name: item.teacher_name ?? item.teacherName
    };
  }

  async function loadData() {
    setLoading(true);
    try {
      const [parentsData, studentsData, classesData] = await Promise.all([
        api("/parents"),
        api("/students"),
        api("/classes")
      ]);
      setParents(Array.isArray(parentsData) ? parentsData : []);
      setStudents(Array.isArray(studentsData) ? studentsData : []);
      setClasses(Array.isArray(classesData) ? classesData.map(normalizeClassItem) : []);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function submitParent(e) {
    e.preventDefault();
    try {
      await api("/parents", {
        method: "POST",
        body: JSON.stringify(parentForm.form)
      });
      parentForm.reset();
      setMessage("Created parent successfully");
      loadData();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function submitStudent(e) {
    e.preventDefault();
    try {
      await api("/students", {
        method: "POST",
        body: JSON.stringify({
          ...studentForm.form,
          parent_id: Number(studentForm.form.parent_id)
        })
      });
      studentForm.reset();
      setMessage("Created student successfully");
      loadData();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function registerClass(classId) {
    const studentId = Number(registerStudentByClass[classId]);
    if (!studentId) {
      setMessage("Please select a student before registering");
      return;
    }

    try {
      await api(`/classes/${classId}/register`, {
        method: "POST",
        body: JSON.stringify({ student_id: studentId })
      });
      setMessage("Registration successful");
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Product Builder Assignment</p>
          <h1>Mini LMS for Student, Parent and Subscription</h1>
          <p className="sub">Create data, browse weekly classes and register students in one place.</p>
        </div>
        <button type="button" onClick={loadData} className="refresh-btn">
          Refresh Data
        </button>
      </header>

      {message && <div className="message">{message}</div>}

      <section className="grid-two">
        <form className="card" onSubmit={submitParent}>
          <h2>Create Parent</h2>
          <input name="name" placeholder="Name" value={parentForm.form.name} onChange={parentForm.onChange} required />
          <input name="phone" placeholder="Phone" value={parentForm.form.phone} onChange={parentForm.onChange} required />
          <input name="email" type="email" placeholder="Email" value={parentForm.form.email} onChange={parentForm.onChange} required />
          <button type="submit">Create Parent</button>
        </form>

        <form className="card" onSubmit={submitStudent}>
          <h2>Create Student</h2>
          <input name="name" placeholder="Student Name" value={studentForm.form.name} onChange={studentForm.onChange} required />
          <input name="dob" type="date" value={studentForm.form.dob} onChange={studentForm.onChange} required />
          <select name="gender" value={studentForm.form.gender} onChange={studentForm.onChange}>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
          <input name="current_grade" placeholder="Current Grade" value={studentForm.form.current_grade} onChange={studentForm.onChange} required />
          <select name="parent_id" value={studentForm.form.parent_id} onChange={studentForm.onChange} required>
            <option value="">Select Parent</option>
            {parents.map((parent) => (
              <option key={parent.id} value={parent.id}>
                {parent.name} (ID: {parent.id})
              </option>
            ))}
          </select>
          <button type="submit">Create Student</button>
        </form>
      </section>

      <section className="card full">
        <h2>Weekly Classes</h2>
        {loading ? <p>Loading...</p> : null}
        <div className="week-grid">
          {DAYS.map((day, dayIndex) => (
            <div key={day} className="day-col">
              <h3>{day}</h3>
              {(classByDay.get(dayIndex) || []).length === 0 ? (
                <p className="empty">No classes</p>
              ) : (
                (classByDay.get(dayIndex) || []).map((classItem) => (
                  <div key={classItem.id} className="class-item">
                    <strong>{classItem.name}</strong>
                    <p>{classItem.subject}</p>
                    <p>{classItem.time_slot}</p>
                    <p>{classItem.teacher_name}</p>
                    <div className="register-bar">
                      <select
                        value={registerStudentByClass[classItem.id] || ""}
                        onChange={(e) =>
                          setRegisterStudentByClass((prev) => ({
                            ...prev,
                            [classItem.id]: e.target.value
                          }))
                        }
                      >
                        <option value="">Select student</option>
                        {students.map((student) => (
                          <option key={student.id} value={student.id}>
                            {student.name}
                          </option>
                        ))}
                      </select>
                      <button type="button" onClick={() => registerClass(classItem.id)}>
                        Register
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
