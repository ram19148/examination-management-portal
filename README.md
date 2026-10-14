# 🎓 Examination Management Portal (EMP)

An enterprise-grade, role-based web portal designed to streamline academic examination workflows — including examiner slot creation, student seat reservation, rubric-based grading, and administrative scheduling.

Built as part of the **IIT Madras Diploma in Data Science and Applications (MAD-1)** curriculum.

---

## 🚀 Key Highlights & Architecture

- **Zero Client-Side JavaScript Dependency:** All core business logic, validations, and workflow constraints are strictly executed server-side using Flask and SQLAlchemy.
- **Dual-Window Temporal State Machine:** Automated timeline enforcement for Examiner slot creation (`slot_creation_window`) and Student booking (`slot_booking_window`).
- **Strict Role-Based Access Control (RBAC):** Custom Python function decorators (`@login_required`, `@role_required`) protecting endpoints for **Admin**, **Examiner**, and **Student**.
- **Soft Deletion & Audit Integrity:** Slot cancellations restore seat inventory atomically while retaining immutable booking audit logs.
- **RESTful API Layer:** Decoupled JSON endpoints for external integrations and metrics extraction.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Back-end Controller** | Python 3.x, Flask |
| **Object-Relational Mapping (ORM)** | Flask-SQLAlchemy |
| **Relational Database** | SQLite (Programmatically generated schema) |
| **Templating Engine** | Jinja2 |
| **Front-end Framework** | Bootstrap 5, Custom Responsive CSS |
| **Security & Cryptography** | Werkzeug (`scrypt` password hashing) |

---

## 👥 Role Matrix & Workflows

### 1. System Administrator (`admin`)
- **Metrics Dashboard:** Real-time visibility into courses, exams, active examiners, registered students, slots, and bookings.
- **Global Portal Search:** Search users, examinations, course codes, and booking records by query or primary key ID.
- **Course & Exam CRUD:** Add, update, or remove academic courses and configure multi-type examinations (*Viva, Practical, Project Demo, Assessment*).
- **Examiner Governance:** Approve pending faculty registrations or deactivate accounts.
- **Transactional Overrides:** Reschedule student bookings to available slots and reassign examiners under contingency.

### 2. Examiner / Faculty (`examiner`)
- **Self-Registration:** Submits credentials and department info; access gated until administrative approval.
- **Slot Management:** Create examination slots within administrative timeline windows. Modify or delete unbooked slots (`booked_count == 0`).
- **Rubric-Driven Evaluation:** Assess assigned students against structured parameters (*Code Quality, Conceptual Viva, Execution*) and publish scores with qualitative remarks.

### 3. Student (`student`)
- **Direct Self-Registration:** Instant access upon signup.
- **Search & Discovery:** Real-time search by course code or exam title.
- **Slot Reservation:** Book available slots with atomic capacity checks to prevent overbooking and duplicate registrations.
- **Deadline-Enforced Cancellation:** Cancel bookings before the booking deadline (`now <= slot_booking_end`) with immediate seat restoration.
- **Scorecard & Feedback:** View published marks, evaluation criteria, and qualitative feedback.
- **Profile Management:** Update personal details and password credentials.

---

## ⚙️ Local Setup & Installation

### Prerequisites
- Python 3.10+
- Git

### 1. Clone Repository
```bash
git clone [https://github.com/](https://github.com/)<your-username>/examination-management-portal.git
cd examination-management-portal