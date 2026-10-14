# models.py
# ==============================================================================
# Yeh file database ke saare tables aur unke aapsi relationships ko define karti hai.
# Yahan Flask-SQLAlchemy ORM ka use karke relational schema banaya gaya hai.
# ==============================================================================

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Yahan par SQLAlchemy ka main database instance initialize ho raha hai
db = SQLAlchemy()


# ------------------------------------------------------------------------------
# 1. USER MODEL (Admin, Examiner, aur Student sabhi is ek table mein store honge)
# ------------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'

    # Primary Key: Har user ki unique numeric identity
    id = db.Column(db.Integer, primary_key=True)

    # Username: Login ke liye unique identifier (e.g. roll number ya admin id)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)

    # Security: Plain text password kabhi store nahi karte, yahan hashed password store hoga
    password_hash = db.Column(db.String(255), nullable=False)

    # User ka pura naam
    full_name = db.Column(db.String(120), nullable=False)

    # Unique email address notifications aur communication ke liye
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # RBAC Role: 'admin', 'examiner', ya 'student'
    role = db.Column(db.String(20), nullable=False)

    # Account Status: 'active', 'pending_approval' (examiner ke liye), ya 'deactivated'
    status = db.Column(db.String(20), default='active', nullable=False)

    # Examiner specific field: Examiner kis department se belong karta hai
    department = db.Column(db.String(120), nullable=True)

    # Audit timestamp: User kab create hua tha
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # RELATIONSHIPS:
    # Ek examiner multiple examination slots create kar sakta hai
    slots_created = db.relationship('ExaminationSlot', backref='examiner', lazy=True)

    # Ek student multiple bookings kar sakta hai
    bookings = db.relationship('Booking', backref='student', lazy=True)

    def __repr__(self):
        return f"<User {self.username} - Role: {self.role}>"


# ------------------------------------------------------------------------------
# 2. COURSE MODEL (Courses jinke andar alag-alag exams conduct honge)
# ------------------------------------------------------------------------------
class Course(db.Model):
    __tablename__ = 'courses'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Unique Course Code (e.g. CS101, DS201)
    course_code = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Course ka pura naam
    course_name = db.Column(db.String(150), nullable=False)

    # Course ka brief description
    description = db.Column(db.Text, nullable=True)

    # Course ka status ('Active' ya 'Archived')
    status = db.Column(db.String(20), default='Active', nullable=False)

    # RELATIONSHIP:
    # Ek course ke andar multiple examinations ho sakti hain.
    # cascade='all, delete-orphan' ka matlab: agar course delete ho toh uske exams bhi clean ho jayein
    examinations = db.relationship('Examination', backref='course', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f"<Course {self.course_code}: {self.course_name}>"


# ------------------------------------------------------------------------------
# 3. EXAMINATION MODEL (Admin dwara schedule ki gayi parikshayein)
# ------------------------------------------------------------------------------
class Examination(db.Model):
    __tablename__ = 'examinations'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key: Yeh exam kis course ke under schedule hua hai
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    # Exam ka title (e.g. End Term Viva / Project Demo)
    name = db.Column(db.String(150), nullable=False)

    # Pariksha ka format: 'Viva', 'Practical', 'Project Demo', ya 'Assessment'
    exam_type = db.Column(db.String(50), nullable=False)

    # Total duration minutes mein (e.g. 20 ya 30 minutes)
    duration_minutes = db.Column(db.Integer, default=20, nullable=False)

    # Pariksha ke total maximum marks
    max_marks = db.Column(db.Float, default=100.0, nullable=False)

    # BUSINESS TIMELINES:
    # 1. Window: Examiner kab se kab tak slot create kar sakta hai
    slot_creation_start = db.Column(db.DateTime, nullable=False)
    slot_creation_end = db.Column(db.DateTime, nullable=False)

    # 2. Window: Student kab se kab tak slot book kar sakta hai
    slot_booking_start = db.Column(db.DateTime, nullable=False)
    slot_booking_end = db.Column(db.DateTime, nullable=False)

    # Exam status: 'Active', 'Draft', 'Closed', 'Completed'
    status = db.Column(db.String(20), default='Active', nullable=False)

    # RELATIONSHIPS:
    # Exam ke evaluation rubrics
    rubrics = db.relationship('ExaminationRubric', backref='examination', cascade='all, delete-orphan', lazy=True)
    # Exam ke andar banaye gaye slots
    slots = db.relationship('ExaminationSlot', backref='examination', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f"<Examination {self.name} ({self.exam_type})>"


# ------------------------------------------------------------------------------
# 4. EXAMINATION RUBRIC MODEL (Evaluation criteria aur unke marks distribution)
# ------------------------------------------------------------------------------
class ExaminationRubric(db.Model):
    __tablename__ = 'examination_rubrics'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key: Rubric kis examination se linked hai
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)

    # Criterion ka naam (e.g. Code Quality, Viva Clarity, Demo Performance)
    criterion_name = db.Column(db.String(150), nullable=False)

    # Is specific parameter ke maximum marks
    max_marks = db.Column(db.Float, nullable=False)

    # Weightage factor (default 1.0)
    weightage = db.Column(db.Float, default=1.0, nullable=False)

    # Criterion ka detailed description
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Rubric {self.criterion_name} - Max: {self.max_marks}>"


# ------------------------------------------------------------------------------
# 5. EXAMINATION SLOT MODEL (Examiner dwara create kiye gaye time slots)
# ------------------------------------------------------------------------------
class ExaminationSlot(db.Model):
    __tablename__ = 'examination_slots'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys: Slot kis exam aur kis examiner ka hai
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Slot ka date aur time
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # Capacity management
    capacity = db.Column(db.Integer, default=1, nullable=False)
    booked_count = db.Column(db.Integer, default=0, nullable=False)

    # Slot Status: 'Available', 'Full', 'Cancelled', 'Completed'
    status = db.Column(db.String(20), default='Available', nullable=False)

    # RELATIONSHIP: Is slot ke under hone wali bookings
    bookings = db.relationship('Booking', backref='slot', cascade='all, delete-orphan', lazy=True)

    # COMPUTED PROPERTY: Recruiter ya interviewer ke saamne dikhane ke liye dynamic calculation
    @property
    def available_seats(self):
        # Remaining seats calculate karne ka method
        return max(0, self.capacity - self.booked_count)

    def __repr__(self):
        return f"<Slot #{self.id} on {self.date} [{self.booked_count}/{self.capacity}]>"


# ------------------------------------------------------------------------------
# 6. BOOKING MODEL (Student dwara slot book karne ka transactional record)
# ------------------------------------------------------------------------------
class Booking(db.Model):
    __tablename__ = 'bookings'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys: Kaunsa student aur kaunsa slot
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('examination_slots.id'), nullable=False)

    # Booking kab create hui
    booking_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Status: 'Booked', 'Cancelled' (soft delete), 'Completed'
    status = db.Column(db.String(20), default='Booked', nullable=False)

    # RELATIONSHIP: Booking ka single evaluation record (1-to-1 relationship)
    evaluation = db.relationship('Evaluation', backref='booking', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Booking #{self.id}: Student {self.student_id} -> Slot {self.slot_id} ({self.status})>"


# ------------------------------------------------------------------------------
# 7. EVALUATION MODEL (Examiner dwara diye gaye marks, rubrics breakdown aur feedback)
# ------------------------------------------------------------------------------
class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys: Kis booking ka evaluation hua aur kis examiner ne evaluate kiya
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Total score jo student ko mila
    total_marks = db.Column(db.Float, nullable=False)

    # Flexible JSON storage: Rubric-wise marks ka breakdown (e.g. {"Code Quality": 25, "Viva": 20})
    rubric_scores = db.Column(db.Text, nullable=True)

    # Examiner ka qualitative feedback aur remarks
    remarks = db.Column(db.Text, nullable=True)

    # Status: 'Draft' ya 'Published'
    status = db.Column(db.String(20), default='Published', nullable=False)

    # Evaluation kab submit hua
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Direct relationship: Evaluation record se directly examiner ka data fetch karne ke liye
    examiner = db.relationship('User', backref='evaluations_given')

    def __repr__(self):
        return f"<Evaluation #{self.id} - Marks: {self.total_marks} / Booking #{self.booking_id}>"

        