# app.py
# ==============================================================================
# Yeh application ka main controller aur routing engine hai.
# Isme authentication, role-based authorization, CRUD operations,
# business validation rules aur REST APIs configure kiye gaye hain.
# ==============================================================================

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import json

# Yahan par apne models aur database instance ko import kiya gaya hai
from models import db, User, Course, Examination, ExaminationRubric, ExaminationSlot, Booking, Evaluation

# Flask application instance create ho raha hai
app = Flask(__name__)

# Security: Session cookie encryption ke liye secret key
app.config['SECRET_KEY'] = 'mad1-emp-iitm-secret-key-2026'

# Database Configuration: SQLite database ka local path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emp.db'

# Performance: Extra memory overhead avoid karne ke liye modification tracking disable kiya
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database ko Flask app ke sath initialize kiya ja raha hai
db.init_app(app)


# ==============================================================================
# SECTION 1: ROLE-BASED ACCESS CONTROL (RBAC) SECURITY DECORATORS
# ==============================================================================

def login_required(f):
    """
    Decorator: Check karta hai ki user authenticated (logged in) hai ya nahi.
    Agar session mein user_id nahi milti toh user ko login page par redirect karega.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Kripya pehle login karein.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """
    Decorator: Strict Authorization implement karta hai.
    Check karta hai ki logged-in user ka role allowed_roles tuple mein hai ya nahi.
    Agar role match nahi karta toh access deny karta hai.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check 1: User login hona chahiye
            if 'user_id' not in session:
                flash("Kripya pehle login karein.", "warning")
                return redirect(url_for('login'))
            # Check 2: User ka role authorized hona chahiye
            if session.get('role') not in allowed_roles:
                flash("Is resource ko access karne ki permission aapke paas nahi hai.", "danger")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==============================================================================
# SECTION 2: AUTHENTICATION (LOGIN, REGISTER, LOGOUT)
# ==============================================================================

@app.route('/')
def home():
    """Root route: Logged-in user ko unke dashboard par bhejta hai, varna login page par."""
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'examiner':
            return redirect(url_for('examiner_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User authentication route (Admin, Examiner, Student)."""
    # Agar user pehle se logged in hai toh dubara login form dikhane ki jagah redirect karein
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'examiner':
            return redirect(url_for('examiner_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Database query: Username ke basis par user fetch karna
        user = User.query.filter_by(username=username).first()

        # Password check: Werkzeug security utility se secure hash comparison
        if not user or not check_password_hash(user.password_hash, password):
            flash("Galat username ya password दर्ज kiya gaya hai.", "danger")
            return redirect(url_for('login'))

        # Business Rule: Examiner bina admin approval ke login nahi kar sakta
        if user.role == 'examiner' and user.status != 'active':
            flash("Aapka examiner account abhi Admin approval ke liye pending hai.", "warning")
            return redirect(url_for('login'))

        # Deactivated user check
        if user.status == 'deactivated':
            flash("Yeh account deactivate kar diya gaya hai. Administrator se sampark karein.", "danger")
            return redirect(url_for('login'))

        # Session persistence: Client cookie mein encrypted user data store karna
        session['user_id'] = user.id
        session['username'] = user.username
        session['full_name'] = user.full_name
        session['role'] = user.role

        flash(f"Swagat hai, {user.full_name}!", "success")
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'examiner':
            return redirect(url_for('examiner_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Self-registration flow for Students and Examiners (Admin registration blocked)."""
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        role = request.form.get('role')
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        department = request.form.get('department', '').strip()
        password = request.form.get('password', '')

        # Duplicate check: Username ya Email pehle se exist toh nahi karta
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Yeh username ya email pehle se registered hai.", "danger")
            return redirect(url_for('register'))

        # Business Rule: Student turant active hota hai, Examiner approval ke liye pending rehta hai
        status = 'active' if role == 'student' else 'pending_approval'

        # Naya User object create ho raha hai
        new_user = User(
            username=username,
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            status=status,
            department=department if role == 'examiner' else None
        )
        db.session.add(new_user)
        db.session.commit()

        if role == 'student':
            flash("Student registration safal! Ab aap login kar sakte hain.", "success")
        else:
            flash("Examiner application submit ho gayi hai. Admin approval ki pratiksha karein.", "info")

        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
def logout():
    """Session clear karke user ko secure tareeqe se logout karta hai."""
    session.clear()
    flash("Aap successfully logout ho chuke hain.", "info")
    return redirect(url_for('login'))


# ==============================================================================
# SECTION 3: ADMIN MODULE (CRUD, METRICS, SEARCH, RESCHEDULING)
# ==============================================================================

@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    """Admin Overview Dashboard: Summary metrics aur unified global search."""
    search_query = request.args.get('search', '').strip()
    search_results = None

    if search_query:
        # Global Search Engine: Multiple tables mein query execute karna
        users_found = User.query.filter(
            (User.full_name.ilike(f'%{search_query}%')) |
            (User.username.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%'))
        ).all()

        exams_found = Examination.query.filter(
            (Examination.name.ilike(f'%{search_query}%')) |
            (Examination.exam_type.ilike(f'%{search_query}%'))
        ).all()

        courses_found = Course.query.filter(
            (Course.course_code.ilike(f'%{search_query}%')) |
            (Course.course_name.ilike(f'%{search_query}%'))
        ).all()

        bookings_found = []
        if search_query.isdigit():
            b = Booking.query.get(int(search_query))
            if b:
                bookings_found.append(b)

        search_results = {
            'users': users_found,
            'exams': exams_found,
            'courses': courses_found,
            'bookings': bookings_found
        }

    # Summary metrics cards ka data aggregate karna
    stats = {
        'courses': Course.query.count(),
        'exams': Examination.query.count(),
        'examiners': User.query.filter_by(role='examiner').count(),
        'students': User.query.filter_by(role='student').count(),
        'slots': ExaminationSlot.query.count(),
        'bookings': Booking.query.count()
    }
    return render_template('admin/dashboard.html', stats=stats, search_query=search_query, search_results=search_results)


# --- COURSE CRUD ---
@app.route('/admin/courses', methods=['GET', 'POST'])
@role_required('admin')
def admin_courses():
    """Course creation aur list view."""
    if request.method == 'POST':
        code = request.form.get('course_code', '').strip().upper()
        name = request.form.get('course_name', '').strip()
        desc = request.form.get('description', '').strip()

        if Course.query.filter_by(course_code=code).first():
            flash("Yeh course code pehle se maujood hai.", "danger")
        else:
            course = Course(course_code=code, course_name=name, description=desc)
            db.session.add(course)
            db.session.commit()
            flash("Naya course safalta-purvak add ho gaya.", "success")
        return redirect(url_for('admin_courses'))

    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses)


@app.route('/admin/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_course(course_id):
    """Course details edit karna."""
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.course_code = request.form.get('course_code', '').strip().upper()
        course.course_name = request.form.get('course_name', '').strip()
        course.description = request.form.get('description', '').strip()
        course.status = request.form.get('status', 'Active')
        db.session.commit()
        flash(f"Course {course.course_code} update ho gaya.", "success")
        return redirect(url_for('admin_courses'))
    return render_template('admin/edit_course.html', course=course)


@app.route('/admin/courses/delete/<int:course_id>', methods=['POST', 'GET'])
@role_required('admin')
def delete_course(course_id):
    """Course aur uske associated records delete karna (Cascade Delete)."""
    course = Course.query.get_or_404(course_id)
    code = course.course_code
    db.session.delete(course)
    db.session.commit()
    flash(f"Course {code} aur uske related exams delete kar diye gaye.", "info")
    return redirect(url_for('admin_courses'))


# --- EXAMINATION CRUD ---
@app.route('/admin/exams', methods=['GET', 'POST'])
@role_required('admin')
def admin_exams():
    """Exam schedule create karna with timeline validation & auto rubrics."""
    if request.method == 'POST':
        course_id = int(request.form.get('course_id'))
        name = request.form.get('name')
        exam_type = request.form.get('exam_type')
        duration = int(request.form.get('duration_minutes'))
        max_marks = float(request.form.get('max_marks'))

        slot_create_start = datetime.strptime(request.form.get('slot_creation_start'), '%Y-%m-%dT%H:%M')
        slot_create_end = datetime.strptime(request.form.get('slot_creation_end'), '%Y-%m-%dT%H:%M')
        book_start = datetime.strptime(request.form.get('slot_booking_start'), '%Y-%m-%dT%H:%M')
        book_end = datetime.strptime(request.form.get('slot_booking_end'), '%Y-%m-%dT%H:%M')

        # Naya exam schedule object
        exam = Examination(
            course_id=course_id, name=name, exam_type=exam_type,
            duration_minutes=duration, max_marks=max_marks,
            slot_creation_start=slot_create_start, slot_creation_end=slot_create_end,
            slot_booking_start=book_start, slot_booking_end=book_end, status='Active'
        )
        db.session.add(exam)
        db.session.flush()  # Primary Key id generate karne ke liye bina transaction close kiye

        # Auto-Rubrics Generation: Standard rubric criteria automatically add karna
        half_marks = round(max_marks / 2.0, 1)
        r1 = ExaminationRubric(examination_id=exam.id, criterion_name="Technical Execution & Demo", max_marks=half_marks)
        r2 = ExaminationRubric(examination_id=exam.id, criterion_name="Viva & Conceptual Clarity", max_marks=max_marks - half_marks)
        db.session.add_all([r1, r2])

        db.session.commit()
        flash("Pariksha schedule aur standard rubrics create ho gaye.", "success")
        return redirect(url_for('admin_exams'))

    courses = Course.query.all()
    exams = Examination.query.all()
    return render_template('admin/exams.html', courses=courses, exams=exams)


@app.route('/admin/exams/edit/<int:exam_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_exam(exam_id):
    """Exam settings aur timeline windows edit karna."""
    exam = Examination.query.get_or_404(exam_id)
    if request.method == 'POST':
        exam.name = request.form.get('name')
        exam.exam_type = request.form.get('exam_type')
        exam.duration_minutes = int(request.form.get('duration_minutes'))
        exam.max_marks = float(request.form.get('max_marks'))
        exam.slot_creation_start = datetime.strptime(request.form.get('slot_creation_start'), '%Y-%m-%dT%H:%M')
        exam.slot_creation_end = datetime.strptime(request.form.get('slot_creation_end'), '%Y-%m-%dT%H:%M')
        exam.slot_booking_start = datetime.strptime(request.form.get('slot_booking_start'), '%Y-%m-%dT%H:%M')
        exam.slot_booking_end = datetime.strptime(request.form.get('slot_booking_end'), '%Y-%m-%dT%H:%M')
        exam.status = request.form.get('status', 'Active')
        db.session.commit()
        flash(f"Exam '{exam.name}' update ho gaya.", "success")
        return redirect(url_for('admin_exams'))

    courses = Course.query.all()
    return render_template('admin/edit_exam.html', exam=exam, courses=courses)


@app.route('/admin/exams/delete/<int:exam_id>', methods=['POST', 'GET'])
@role_required('admin')
def delete_exam(exam_id):
    """Exam delete karna."""
    exam = Examination.query.get_or_404(exam_id)
    name = exam.name
    db.session.delete(exam)
    db.session.commit()
    flash(f"Exam '{name}' successfully remove kar diya gaya.", "info")
    return redirect(url_for('admin_exams'))


# --- EXAMINER APPROVALS & CONTROLS ---
@app.route('/admin/examiners')
@role_required('admin')
def admin_examiners():
    """Sabhi examiners ki table aur approval list."""
    examiners = User.query.filter_by(role='examiner').all()
    return render_template('admin/examiners.html', examiners=examiners)


@app.route('/admin/examiners/approve/<int:user_id>')
@role_required('admin')
def approve_examiner(user_id):
    """Pending examiner ko active approve karna."""
    examiner = User.query.get_or_404(user_id)
    examiner.status = 'active'
    db.session.commit()
    flash(f"Examiner {examiner.full_name} ko approve kar diya gaya hai.", "success")
    return redirect(url_for('admin_examiners'))


@app.route('/admin/examiners/deactivate/<int:user_id>')
@role_required('admin')
def deactivate_examiner(user_id):
    """Examiner account ko deactivate karna taaki wo login na kar sake."""
    examiner = User.query.get_or_404(user_id)
    examiner.status = 'deactivated'
    db.session.commit()
    flash(f"Examiner {examiner.full_name} ko deactivate kar diya gaya.", "warning")
    return redirect(url_for('admin_examiners'))


# --- BOOKING MANAGEMENT & RESCHEDULING ---
@app.route('/admin/bookings')
@role_required('admin')
def admin_bookings():
    """Sabhi student bookings ki master list aur management controls."""
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    active_examiners = User.query.filter_by(role='examiner', status='active').all()
    return render_template('admin/bookings.html', bookings=bookings, examiners=active_examiners)


@app.route('/admin/booking/reschedule/<int:booking_id>', methods=['POST'])
@role_required('admin')
def reschedule_booking(booking_id):
    """Admin Power: Student ki booking ko kisi doosre available slot mein shift karna."""
    booking = Booking.query.get_or_404(booking_id)
    new_slot_id = int(request.form.get('new_slot_id'))
    new_slot = ExaminationSlot.query.get_or_404(new_slot_id)

    # Capacity check on new slot
    if new_slot.available_seats <= 0:
        flash("Chuna gaya naya slot pehle se full hai!", "danger")
        return redirect(url_for('admin_bookings'))

    # Step 1: Purane slot ki seat free karna
    old_slot = booking.slot
    old_slot.booked_count = max(0, old_slot.booked_count - 1)
    old_slot.status = 'Available'

    # Step 2: Naye slot mein seat occupy karna
    new_slot.booked_count += 1
    if new_slot.booked_count >= new_slot.capacity:
        new_slot.status = 'Full'

    # Step 3: Booking pointer update karna
    booking.slot_id = new_slot.id
    db.session.commit()
    flash(f"Booking #BK-{booking.id} successfully reschedule ho gayi.", "success")
    return redirect(url_for('admin_bookings'))


@app.route('/admin/slot/change-examiner/<int:slot_id>', methods=['POST'])
@role_required('admin')
def change_slot_examiner(slot_id):
    """Admin Power: Kisi slot ke examiner ko reassign karna."""
    slot = ExaminationSlot.query.get_or_404(slot_id)
    new_examiner_id = int(request.form.get('new_examiner_id'))
    examiner = User.query.get_or_404(new_examiner_id)

    if examiner.role != 'examiner' or examiner.status != 'active':
        flash("Invalid ya inactive examiner!", "danger")
        return redirect(url_for('admin_bookings'))

    slot.examiner_id = examiner.id
    db.session.commit()
    flash(f"Slot #SL-{slot.id} ke liye examiner badal kar {examiner.full_name} kiya gaya.", "success")
    return redirect(url_for('admin_bookings'))


# ==============================================================================
# SECTION 4: EXAMINER MODULE (SLOT CREATION, EDITING, EVALUATION)
# ==============================================================================

@app.route('/examiner/dashboard')
@role_required('examiner')
def examiner_dashboard():
    """Examiner Dashboard: Assigned slots aur unme booked students ki list."""
    my_slots = ExaminationSlot.query.filter_by(examiner_id=session['user_id']).all()
    return render_template('examiner/dashboard.html', slots=my_slots)


@app.route('/examiner/slots/create', methods=['GET', 'POST'])
@role_required('examiner')
def create_slot():
    """Timeline window ke andar naya examination slot banana."""
    if request.method == 'POST':
        exam_id = int(request.form.get('examination_id'))
        exam = Examination.query.get_or_404(exam_id)
        now = datetime.now()

        # Business Rule Validation: Slot creation timeline check
        if not (exam.slot_creation_start <= now <= exam.slot_creation_end):
            flash("Truti: Is exam ke liye slot creation window band ho chuki hai!", "danger")
            return redirect(url_for('create_slot'))

        date_val = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        start_time_val = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        end_time_val = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        capacity = int(request.form.get('capacity', 1))

        slot = ExaminationSlot(
            examination_id=exam.id, examiner_id=session['user_id'],
            date=date_val, start_time=start_time_val, end_time=end_time_val,
            capacity=capacity, booked_count=0, status='Available'
        )
        db.session.add(slot)
        db.session.commit()
        flash("Naya slot safalta-purvak create ho gaya.", "success")
        return redirect(url_for('examiner_dashboard'))

    active_exams = Examination.query.filter_by(status='Active').all()
    return render_template('examiner/create_slot.html', exams=active_exams)


@app.route('/examiner/slots/edit/<int:slot_id>', methods=['GET', 'POST'])
@role_required('examiner')
def edit_slot(slot_id):
    """Slot edit karna: keval tabhi jab tak koi student book na kare (booked_count == 0)."""
    slot = ExaminationSlot.query.get_or_404(slot_id)

    # Ownership check
    if slot.examiner_id != session['user_id']:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('examiner_dashboard'))

    # Booking check
    if slot.booked_count > 0:
        flash("Student booking ke baad slot edit nahi kiya ja sakta!", "danger")
        return redirect(url_for('examiner_dashboard'))

    if request.method == 'POST':
        slot.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        slot.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        slot.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        slot.capacity = int(request.form.get('capacity', 1))
        db.session.commit()
        flash("Slot details update ho gayi hain.", "success")
        return redirect(url_for('examiner_dashboard'))

    return render_template('examiner/edit_slot.html', slot=slot)


@app.route('/examiner/slots/delete/<int:slot_id>', methods=['POST', 'GET'])
@role_required('examiner')
def delete_slot(slot_id):
    """Empty slot ko delete karna."""
    slot = ExaminationSlot.query.get_or_404(slot_id)

    if slot.examiner_id != session['user_id']:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('examiner_dashboard'))

    if slot.booked_count > 0:
        flash("Booked slot delete nahi kiya ja sakta!", "danger")
        return redirect(url_for('examiner_dashboard'))

    db.session.delete(slot)
    db.session.commit()
    flash("Slot delete ho gaya.", "info")
    return redirect(url_for('examiner_dashboard'))


@app.route('/examiner/evaluate/<int:booking_id>', methods=['GET', 'POST'])
@role_required('examiner')
def evaluate_student(booking_id):
    """Rubrics ke hisaab se student ka evaluation submit karna."""
    booking = Booking.query.get_or_404(booking_id)

    # Ownership Security Check: Examiner keval apne assigned student ko evaluate kare
    if booking.slot.examiner_id != session['user_id']:
        flash("Aap keval apne slots ke students ko evaluate kar sakte hain!", "danger")
        return redirect(url_for('examiner_dashboard'))

    rubrics = booking.slot.examination.rubrics

    if request.method == 'POST':
        total_score = 0.0
        scores_dict = {}

        if rubrics:
            for r in rubrics:
                val = float(request.form.get(f'rubric_{r.id}', 0))
                scores_dict[r.criterion_name] = val
                total_score += val
        else:
            val = float(request.form.get('rubric_0', 0))
            total_score = val
            scores_dict['Overall Score'] = val

        remarks = request.form.get('remarks', '')

        # Evaluation record insertion
        eval_record = Evaluation(
            booking_id=booking.id, examiner_id=session['user_id'],
            total_marks=total_score, rubric_scores=json.dumps(scores_dict),
            remarks=remarks, status='Published'
        )
        # Booking status update
        booking.status = 'Completed'
        db.session.add(eval_record)
        db.session.commit()

        flash(f"Evaluation complete! Total marks awarded: {total_score}", "success")
        return redirect(url_for('examiner_dashboard'))

    return render_template('examiner/evaluate.html', booking=booking, rubrics=rubrics)


# ==============================================================================
# SECTION 5: STUDENT MODULE (SEARCH, BOOKING, CANCELLATION, PROFILE)
# ==============================================================================

@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    """Student Dashboard: Available exams, booked slots, aur exam history."""
    search_query = request.args.get('search', '').strip()
    if search_query:
        exams = Examination.query.join(Course).filter(
            (Examination.name.ilike(f'%{search_query}%')) |
            (Course.course_code.ilike(f'%{search_query}%'))
        ).all()
    else:
        exams = Examination.query.filter_by(status='Active').all()

    my_bookings = Booking.query.filter_by(student_id=session['user_id']).all()
    return render_template('student/dashboard.html', exams=exams, bookings=my_bookings, search_query=search_query)


@app.route('/student/book/<int:exam_id>', methods=['GET', 'POST'])
@role_required('student')
def book_slot(exam_id):
    """Slot booking workflow with timeline, duplicate, and concurrency checks."""
    exam = Examination.query.get_or_404(exam_id)
    now = datetime.now()

    # Rule 1: Booking timeline window validation
    if not (exam.slot_booking_start <= now <= exam.slot_booking_end):
        flash("Is exam ki booking window abhi band hai!", "danger")
        return redirect(url_for('student_dashboard'))

    # Rule 2: Prevent duplicate active booking for the same examination
    existing = Booking.query.join(ExaminationSlot).filter(
        Booking.student_id == session['user_id'],
        Booking.status == 'Booked',
        ExaminationSlot.examination_id == exam.id
    ).first()

    if existing:
        flash("Aap is exam ke liye pehle hi slot book kar chuke hain!", "warning")
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        slot_id = int(request.form.get('slot_id'))
        slot = ExaminationSlot.query.get_or_404(slot_id)

        # Rule 3: Overbooking prevention (Concurrency protection)
        if slot.booked_count >= slot.capacity:
            flash("Yeh slot full ho chuka hai. Kripya doosra slot chunein.", "danger")
            return redirect(url_for('book_slot', exam_id=exam.id))

        slot.booked_count += 1
        if slot.booked_count >= slot.capacity:
            slot.status = 'Full'

        new_booking = Booking(student_id=session['user_id'], slot_id=slot.id, status='Booked')
        db.session.add(new_booking)
        db.session.commit()

        flash("Exam slot successfully book ho gaya!", "success")
        return redirect(url_for('student_dashboard'))

    available_slots = ExaminationSlot.query.filter(
        ExaminationSlot.examination_id == exam.id,
        ExaminationSlot.status == 'Available'
    ).all()

    return render_template('student/book_slot.html', exam=exam, slots=available_slots)


@app.route('/student/cancel/<int:booking_id>')
@role_required('student')
def cancel_booking(booking_id):
    """Soft-cancel booking with deadline check and seat restoration."""
    booking = Booking.query.get_or_404(booking_id)

    # Ownership check
    if booking.student_id != session['user_id']:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('student_dashboard'))

    # Business Rule: Can cancel only BEFORE slot booking deadline
    now = datetime.now()
    if now > booking.slot.examination.slot_booking_end:
        flash("Booking deadline samapt ho chuki hai. Ab cancel karna sambhav nahi hai!", "danger")
        return redirect(url_for('student_dashboard'))

    # Soft cancel: Record database mein rahega audit purpose ke liye, seat restore ho jayegi
    booking.status = 'Cancelled'
    booking.slot.booked_count = max(0, booking.slot.booked_count - 1)
    booking.slot.status = 'Available'
    db.session.commit()

    flash("Booking safely cancel kar di gayi hai aur seat restore ho gayi.", "info")
    return redirect(url_for('student_dashboard'))


@app.route('/student/profile', methods=['GET', 'POST'])
@role_required('student')
def student_profile():
    """Student profile updates (Name, Email, Password)."""
    user = User.query.get_or_404(session['user_id'])
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '')

        if new_password:
            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        session['full_name'] = user.full_name
        flash("Profile safalta-purvak update ho gayi.", "success")
        return redirect(url_for('student_profile'))

    return render_template('student/profile.html', user=user)


@app.route('/student/results')
@role_required('student')
def student_results():
    """Published scorecards aur examiner feedback dekhna."""
    my_evaluations = Evaluation.query.join(Booking).filter(Booking.student_id == session['user_id']).all()
    return render_template('student/results.html', evaluations=my_evaluations)


# ==============================================================================
# SECTION 6: BONUS REST API ENDPOINTS (FOR RESUME / RECRUITER DEMO)
# ==============================================================================

@app.route('/api/v1/courses', methods=['GET'])
def api_courses():
    """Public JSON API: Sabhi courses ki list return karta hai."""
    courses = Course.query.all()
    return jsonify([{
        'id': c.id,
        'code': c.course_code,
        'name': c.course_name,
        'status': c.status
    } for c in courses])


@app.route('/api/v1/exams', methods=['GET'])
def api_exams():
    """Public JSON API: Active examinations ka data return karta hai."""
    exams = Examination.query.all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'course': e.course.course_code,
        'type': e.exam_type,
        'max_marks': e.max_marks,
        'status': e.status
    } for e in exams])


@app.route('/api/v1/stats', methods=['GET'])
def api_stats():
    """Dashboard Stats JSON API."""
    return jsonify({
        'total_courses': Course.query.count(),
        'total_exams': Examination.query.count(),
        'total_bookings': Booking.query.count(),
        'total_slots': ExaminationSlot.query.count()
    })


# ==============================================================================
# SECTION 7: PROGRAMMATIC DATABASE INITIALIZATION & DEFAULT SUPERUSER
# ==============================================================================

def setup_database():
    """Programmatically schema create karna aur Admin ko default seed karna."""
    with app.app_context():
        # SQLite schema programmatically create ho raha hai
        db.create_all()

        # Check agar admin pehle se maujood hai
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            default_admin = User(
                username='admin',
                password_hash=generate_password_hash('Admin@IITM2026'),
                full_name='System Administrator',
                email='admin@emp.iitm.ac.in',
                role='admin',
                status='active'
            )
            db.session.add(default_admin)
            db.session.commit()
            print("[SUCCESS] Programmatic Database created & Default Admin seeded!")
        else:
            print("[INFO] Database & Default Admin already present.")


# ==============================================================================
# SECTION 8: SERVER BOOTSTRAP
# ==============================================================================

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)