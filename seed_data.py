# seed_data.py
# ==============================================================================
# Yeh script application mein demonstration aur evaluation ke liye
# clean pre-populated dummy data insert karti hai.
# ==============================================================================

from werkzeug.security import generate_password_hash
from datetime import datetime, date, time, timedelta
from app import app
from models import db, User, Course, Examination, ExaminationRubric, ExaminationSlot, Booking, Evaluation
import json

def seed_database():
    with app.app_context():
        print("[INFO] Purana database clean ho raha hai...")
        db.drop_all()
        db.create_all()

        # ----------------------------------------------------------------------
        # 1. SEED USERS (Admin, Examiners, Students)
        # ----------------------------------------------------------------------
        admin = User(
            username='admin',
            password_hash=generate_password_hash('Admin@IITM2026'),
            full_name='System Administrator',
            email='admin@emp.iitm.ac.in',
            role='admin',
            status='active'
        )

        ex1 = User(
            username='prof_sharma',
            password_hash=generate_password_hash('Pass@123'),
            full_name='Prof. Ramesh Sharma',
            email='sharma@faculty.iitm.ac.in',
            role='examiner',
            status='active',
            department='Computer Science & Engineering'
        )

        ex2 = User(
            username='prof_verma',
            password_hash=generate_password_hash('Pass@123'),
            full_name='Dr. Neha Verma',
            email='verma@faculty.iitm.ac.in',
            role='examiner',
            status='pending_approval',  # Demo approval flow
            department='Data Science & AI'
        )

        st1 = User(
            username='23f2003167',
            password_hash=generate_password_hash('Pass@123'),
            full_name='Ram Krishna Singh',
            email='23f2003167@study.iitm.ac.in',
            role='student',
            status='active'
        )

        st2 = User(
            username='23f2003999',
            password_hash=generate_password_hash('Pass@123'),
            full_name='Anjali Kumari',
            email='anjali@study.iitm.ac.in',
            role='student',
            status='active'
        )

        db.session.add_all([admin, ex1, ex2, st1, st2])
        db.session.commit()
        print("[SUCCESS] Users successfully seeded!")

        # ----------------------------------------------------------------------
        # 2. SEED COURSES
        # ----------------------------------------------------------------------
        c1 = Course(course_code='CS101', course_name='Modern Application Development - 1', description='Web architectures, Flask back-end, Jinja2, Bootstrap, and SQLite integration.')
        c2 = Course(course_code='DS201', course_name='Machine Learning Practice', description='Applied machine learning algorithms, model training, and end-term project demos.')
        c3 = Course(course_code='MA101', course_name='Mathematics for Data Science', description='Linear algebra, multivariate calculus, and foundational probability.')

        db.session.add_all([c1, c2, c3])
        db.session.commit()
        print("[SUCCESS] Courses successfully seeded!")

        # ----------------------------------------------------------------------
        # 3. SEED EXAMINATIONS & RUBRICS
        # ----------------------------------------------------------------------
        now = datetime.now()
        exam1 = Examination(
            course_id=c1.id,
            name='Term-End Project Demo & Viva',
            exam_type='Project Demo',
            duration_minutes=25,
            max_marks=100.0,
            slot_creation_start=now - timedelta(days=5),
            slot_creation_end=now + timedelta(days=10),
            slot_booking_start=now - timedelta(days=2),
            slot_booking_end=now + timedelta(days=8),
            status='Active'
        )

        exam2 = Examination(
            course_id=c2.id,
            name='Mid-Term Practical Evaluation',
            exam_type='Practical',
            duration_minutes=20,
            max_marks=50.0,
            slot_creation_start=now - timedelta(days=5),
            slot_creation_end=now + timedelta(days=10),
            slot_booking_start=now - timedelta(days=1),
            slot_booking_end=now + timedelta(days=7),
            status='Active'
        )

        db.session.add_all([exam1, exam2])
        db.session.flush()

        # Rubrics attachment
        r1 = ExaminationRubric(examination_id=exam1.id, criterion_name="Code Quality & Architecture", max_marks=40.0)
        r2 = ExaminationRubric(examination_id=exam1.id, criterion_name="Viva & Concept Clarity", max_marks=40.0)
        r3 = ExaminationRubric(examination_id=exam1.id, criterion_name="UI/UX Implementation", max_marks=20.0)

        r4 = ExaminationRubric(examination_id=exam2.id, criterion_name="Model Execution & Accuracy", max_marks=30.0)
        r5 = ExaminationRubric(examination_id=exam2.id, criterion_name="Viva Questions", max_marks=20.0)

        db.session.add_all([r1, r2, r3, r4, r5])
        db.session.commit()
        print("[SUCCESS] Exams & Rubrics successfully seeded!")

        # ----------------------------------------------------------------------
        # 4. SEED EXAMINATION SLOTS
        # ----------------------------------------------------------------------
        # Slot 1: Booked Slot (Capacity 2)
        slot1 = ExaminationSlot(
            examination_id=exam1.id, examiner_id=ex1.id,
            date=date.today(), start_time=time(10, 0), end_time=time(10, 30),
            capacity=2, booked_count=2, status='Full'
        )

        # Slot 2: Empty Slot for Edit/Delete demo
        slot2 = ExaminationSlot(
            examination_id=exam1.id, examiner_id=ex1.id,
            date=date.today(), start_time=time(11, 0), end_time=time(11, 30),
            capacity=1, booked_count=0, status='Available'
        )

        # Slot 3: Evaluated Slot for Result demo
        slot3 = ExaminationSlot(
            examination_id=exam2.id, examiner_id=ex1.id,
            date=date.today() + timedelta(days=1), start_time=time(14, 0), end_time=time(14, 30),
            capacity=1, booked_count=1, status='Full'
        )

        db.session.add_all([slot1, slot2, slot3])
        db.session.commit()
        print("[SUCCESS] Slots successfully seeded!")

        # ----------------------------------------------------------------------
        # 5. SEED BOOKINGS & EVALUATIONS
        # ----------------------------------------------------------------------
        # Booking 1: Pending evaluation
        b1 = Booking(student_id=st1.id, slot_id=slot1.id, status='Booked')
        # Booking 2: Pending evaluation
        b2 = Booking(student_id=st2.id, slot_id=slot1.id, status='Booked')
        # Booking 3: Completed evaluation
        b3 = Booking(student_id=st2.id, slot_id=slot3.id, status='Completed')

        db.session.add_all([b1, b2, b3])
        db.session.flush()

        # Evaluation for Booking 3
        eval1 = Evaluation(
            booking_id=b3.id,
            examiner_id=ex1.id,
            total_marks=44.5,
            rubric_scores=json.dumps({"Model Execution & Accuracy": 27.0, "Viva Questions": 17.5}),
            remarks="Utkrisht code implementation aur viva me spasht uttar. Very good performance!",
            status='Published'
        )
        db.session.add(eval1)
        db.session.commit()
        print("[SUCCESS] Bookings & Evaluations seeded successfully!")
        print("\n[READY] Database is fully populated with test data!")

if __name__ == '__main__':
    seed_database()