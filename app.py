from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Patient, Doctor, Appointment, MedicalRecord, Prescription, DoctorAvailability
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, time, date
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise RuntimeError('SECRET_KEY must be set in the environment')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables and sample data
with app.app_context():
    db.create_all()
    
    # Do not create default users or credentials at application startup.
# Create the initial administrator explicitly through a trusted setup process.

# Routes
@app.route('/')
@login_required
def index():
    try:
        patients = Patient.query.all()
        doctors = Doctor.query.all()
        appointments = Appointment.query.all()
        medical_records = MedicalRecord.query.all()
        prescriptions = Prescription.query.all()
        
        # Statistics
        stats = {
            'total_patients': len(patients),
            'total_doctors': len(doctors),
            'total_appointments': len(appointments),
            'total_records': len(medical_records),
            'total_prescriptions': len(prescriptions),
            'today_appointments': len([a for a in appointments if a.date == datetime.now().date()])
        }
        
        return render_template('index.html', 
                             patients=patients, 
                             doctors=doctors, 
                             appointments=appointments,
                             prescriptions=prescriptions,
                             medical_records=medical_records,
                             stats=stats,
                             today=datetime.now().date())
    except Exception as e:
        flash(f"Error loading data: {str(e)}", "error")
        return render_template('index.html', patients=[], doctors=[], appointments=[], prescriptions=[], medical_records=[], stats={}, today=datetime.now().date())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')
        
        # Role validation based on who is creating the account
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                # Admin can create any role
                pass
            elif current_user.role in ['doctor', 'staff']:
                # Doctors and staff can only create staff accounts
                if role != 'staff':
                    flash('You can only create staff member accounts.', 'error')
                    return render_template('register.html')
            else:
                flash('Access denied.', 'error')
                return redirect(url_for('index'))
        else:
            # New user registration - restrict to staff only for security
            if role != 'staff':
                flash('New users can only register as staff members. Contact an administrator for other roles.', 'error')
                return render_template('register.html')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        try:
            # Create new user
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# Patient Management
@app.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Staff or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        today_date = datetime.now().strftime('%Y-%m-%d')
        return render_template('add_patient.html', today_date=today_date)
    
    try:
        # Validate date of birth is not in the future and is reasonable
        date_of_birth_str = request.form.get('date_of_birth')
        date_of_birth = None
        if date_of_birth_str:
            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            if date_of_birth > today:
                flash('Date of birth cannot be in the future.', 'error')
                return redirect(url_for('add_patient'))
            
            # Check if date is not too far in the past (more than 150 years ago)
            max_past_date = today.replace(year=today.year - 150)
            if date_of_birth < max_past_date:
                flash('Date of birth seems unrealistic. Please check the date.', 'error')
                return redirect(url_for('add_patient'))
        
        new_patient = Patient(
            name=request.form.get('complete_name', ''),
            date_of_birth=date_of_birth,
            gender=request.form.get('gender', ''),
            contact_number=request.form.get('contact_number', ''),
            address=request.form.get('address', ''),
            emergency_contact=request.form.get('emergency_contact', ''),
            emergency_phone=request.form.get('emergency_phone', ''),
            blood_type=request.form.get('blood_type', ''),
            allergies=request.form.get('allergies', '')
        )
        db.session.add(new_patient)
        db.session.commit()
        flash("Patient added successfully!", "success")
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding patient: {str(e)}", "error")
        return redirect(url_for('add_patient'))

@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Staff or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        try:
            # Validate date of birth is not in the future and is reasonable
            date_of_birth_str = request.form.get('date_of_birth')
            date_of_birth = None
            if date_of_birth_str:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                today = datetime.now().date()
                
                if date_of_birth > today:
                    flash('Date of birth cannot be in the future.', 'error')
                    return redirect(url_for('edit_patient', patient_id=patient_id))
                
                # Check if date is not too far in the past (more than 150 years ago)
                max_past_date = today.replace(year=today.year - 150)
                if date_of_birth < max_past_date:
                    flash('Date of birth seems unrealistic. Please check the date.', 'error')
                    return redirect(url_for('edit_patient', patient_id=patient_id))
            
            patient.name = request.form.get('complete_name', '')
            patient.date_of_birth = date_of_birth
            patient.gender = request.form.get('gender', '')
            patient.contact_number = request.form.get('contact_number', '')
            patient.address = request.form.get('address', '')
            patient.emergency_contact = request.form.get('emergency_contact', '')
            patient.emergency_phone = request.form.get('emergency_phone', '')
            patient.blood_type = request.form.get('blood_type', '')
            patient.allergies = request.form.get('allergies', '')
            
            db.session.commit()
            flash("Patient updated successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating patient: {str(e)}", "error")
    
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('edit_patient.html', patient=patient, today_date=today_date)

@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Staff or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Delete medical record files before cascade delete
        for record in patient.medical_records:
            if record.file_path:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], record.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Delete patient (cascade will handle related records)
        db.session.delete(patient)
        db.session.commit()
        flash("Patient and all related records deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting patient: {str(e)}", "error")
    
    return redirect(url_for('index'))

# Doctor Management
@app.route('/add_doctor', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('add_doctor.html')
    
    try:
        new_doctor = Doctor(
            name=request.form.get('complete_name', ''),
            specialization=request.form.get('specialization', ''),
            license_number=request.form.get('license_number', ''),
            contact_number=request.form.get('contact_number', ''),
            email=request.form.get('email', ''),
            experience_years=request.form.get('experience_years', ''),
            education=request.form.get('education', '')
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash("Doctor added successfully!", "success")
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding doctor: {str(e)}", "error")
        return redirect(url_for('add_doctor'))

@app.route('/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        try:
            new_license_number = request.form.get('license_number', '').strip()
            
            # Validate required fields
            new_name = request.form.get('complete_name', '').strip()
            if not new_name:
                flash("Error: Doctor name is required", "error")
                return render_template('edit_doctor.html', doctor=doctor)
            
            if not new_license_number:
                flash("Error: License number is required", "error")
                return render_template('edit_doctor.html', doctor=doctor)
            
            # Check if license number is being changed and if it conflicts with another doctor
            if new_license_number != doctor.license_number:
                existing_doctor = Doctor.query.filter_by(license_number=new_license_number).first()
                if existing_doctor and existing_doctor.id != doctor.id:
                    flash("Error: License number already exists for another doctor", "error")
                    return render_template('edit_doctor.html', doctor=doctor)
            
            doctor.name = new_name
            new_specialization = request.form.get('specialization', '').strip()
            if not new_specialization:
                flash("Error: Specialization is required", "error")
                return render_template('edit_doctor.html', doctor=doctor)
            doctor.specialization = new_specialization
            doctor.license_number = new_license_number
            doctor.contact_number = request.form.get('contact_number', '')
            doctor.email = request.form.get('email', '')
            
            # Handle experience_years as integer
            experience_years_str = request.form.get('experience_years', '')
            if experience_years_str:
                try:
                    doctor.experience_years = int(experience_years_str)
                except ValueError:
                    flash("Error: Experience years must be a valid number", "error")
                    return render_template('edit_doctor.html', doctor=doctor)
            else:
                doctor.experience_years = None
                
            doctor.education = request.form.get('education', '')
            
            db.session.commit()
            flash("Doctor updated successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating doctor: {str(e)}", "error")
    
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/delete_doctor/<int:doctor_id>', methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        doctor = Doctor.query.get_or_404(doctor_id)
        
        # Delete medical record files before cascade delete
        for record in doctor.medical_records:
            if record.file_path:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], record.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Delete doctor (cascade will handle related records)
        db.session.delete(doctor)
        db.session.commit()
        flash("Doctor and all related records deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting doctor: {str(e)}", "error")
    
    return redirect(url_for('index'))

def check_appointment_conflicts(doctor_id, date, start_time, end_time, exclude_appointment_id=None):
    """Check if there are any appointment conflicts for a doctor at a given time"""
    # Convert string times to time objects if needed
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()
    
    # Query for conflicting appointments
    query = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date == date,
        Appointment.status != 'cancelled'
    )
    
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    existing_appointments = query.all()
    
    for appointment in existing_appointments:
        # Check if the new appointment overlaps with existing ones
        if (start_time < appointment.end_time and end_time > appointment.start_time):
            return True, appointment
    
    return False, None

def check_patient_appointment_conflicts(patient_id, date, start_time, end_time, exclude_appointment_id=None):
    """Check if there are any appointment conflicts for a patient at a given time"""
    # Convert string times to time objects if needed
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()
    
    # Query for conflicting appointments for the same patient
    query = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.date == date,
        Appointment.status != 'cancelled'
    )
    
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    existing_appointments = query.all()
    
    for appointment in existing_appointments:
        # Check if the new appointment overlaps with existing ones
        if (start_time < appointment.end_time and end_time > appointment.start_time):
            return True, appointment
    
    return False, None

def check_business_hours_conflicts(date, start_time, end_time):
    """Check if appointment is within business hours (8 AM - 6 PM)"""
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()
    
    business_start = time(8, 0)  # 8:00 AM
    business_end = time(18, 0)   # 6:00 PM
    
    if start_time < business_start or end_time > business_end:
        return True, f"Appointments must be between {business_start.strftime('%H:%M')} and {business_end.strftime('%H:%M')}"
    
    return False, None

def check_weekend_conflicts(date):
    """Check if appointment is on a weekend"""
    # date.weekday() returns 0=Monday, 6=Sunday
    if date.weekday() >= 5:  # Saturday (5) or Sunday (6)
        return True, "Appointments are not available on weekends"
    
    return False, None

def check_lunch_break_conflicts(start_time, end_time):
    """Check if appointment conflicts with lunch break (12:00 PM - 1:00 PM)"""
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()
    
    lunch_start = time(12, 0)  # 12:00 PM
    lunch_end = time(13, 0)    # 1:00 PM
    
    # Check if appointment overlaps with lunch break
    if (start_time < lunch_end and end_time > lunch_start):
        return True, "Appointments cannot be scheduled during lunch break (12:00 PM - 1:00 PM)"
    
    return False, None

def check_buffer_time_conflicts(doctor_id, date, start_time, end_time, exclude_appointment_id=None):
    """Check if there's enough buffer time between appointments (15 minutes)"""
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()
    
    buffer_minutes = 15
    
    # Query for appointments on the same day
    query = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date == date,
        Appointment.status != 'cancelled'
    )
    
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    existing_appointments = query.all()
    
    for appointment in existing_appointments:
        # Check if there's enough buffer time
        if (start_time < appointment.end_time + timedelta(minutes=buffer_minutes) and 
            end_time > appointment.start_time - timedelta(minutes=buffer_minutes)):
            return True, f"Need at least {buffer_minutes} minutes buffer between appointments. Doctor has appointment at {appointment.time_slot}"
    
    return False, None

def check_max_daily_appointments(doctor_id, date, exclude_appointment_id=None):
    """Check if doctor has reached maximum appointments per day (16 appointments)"""
    max_appointments = 16
    
    query = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date == date,
        Appointment.status != 'cancelled'
    )
    
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    current_count = query.count()
    
    if current_count >= max_appointments:
        return True, f"Doctor has reached maximum appointments per day ({max_appointments})"
    
    return False, None

def check_patient_travel_time_conflicts(patient_id, date, start_time, end_time, exclude_appointment_id=None):
    """Check if patient has enough travel time between appointments (minimum 30 minutes)"""
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()
    
    min_travel_time = 30  # minutes
    
    # Query for other appointments on the same day
    query = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.date == date,
        Appointment.status != 'cancelled'
    )
    
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    existing_appointments = query.all()
    
    for appointment in existing_appointments:
        # Check if there's enough travel time
        if (start_time < appointment.end_time + timedelta(minutes=min_travel_time) and 
            end_time > appointment.start_time - timedelta(minutes=min_travel_time)):
            return True, f"Need at least {min_travel_time} minutes between patient appointments for travel time. Patient has appointment at {appointment.time_slot}"
    
    return False, None

def check_holiday_conflicts(appointment_date):
    """Check if appointment is on a holiday"""
    # Define holidays (you can expand this list)
    holidays = [
        date(2025, 1, 1),   # New Year's Day
        date(2025, 7, 4),   # Independence Day
        date(2025, 12, 25), # Christmas Day
        # Add more holidays as needed
    ]
    
    if appointment_date in holidays:
        return True, "Appointments are not available on holidays"
    
    return False, None

# Appointment Management
@app.route('/add_appointment', methods=['GET', 'POST'])
@login_required
def add_appointment():
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Staff or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        patients = Patient.query.all()
        doctors = Doctor.query.all()
        return render_template('add_appointment.html', patients=patients, doctors=doctors)
    
    try:
        # Parse date and times
        appointment_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        
        # Validate appointment duration (should be 30 minutes)
        start_dt = datetime.combine(datetime.min, start_time)
        end_dt = datetime.combine(datetime.min, end_time)
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        
        if duration_minutes != 30:
            flash("Appointments must be exactly 30 minutes long", "error")
            return redirect(url_for('add_appointment'))
        
        # Check for doctor conflicts
        has_doctor_conflict, conflicting_doctor_appointment = check_appointment_conflicts(
            request.form['doctor_id'], 
            appointment_date, 
            start_time, 
            end_time
        )
        
        if has_doctor_conflict:
            flash(f"Doctor conflict! Doctor already has an appointment at {conflicting_doctor_appointment.time_slot}", "error")
            return redirect(url_for('add_appointment'))
        
        # Check for past date conflicts
        if appointment_date < datetime.now().date():
            flash("Cannot schedule appointments in the past", "error")
            return redirect(url_for('add_appointment'))
        
        # Check for weekend conflicts
        has_weekend_conflict, weekend_message = check_weekend_conflicts(appointment_date)
        if has_weekend_conflict:
            flash(weekend_message, "error")
            return redirect(url_for('add_appointment'))
        
        # Check for holiday conflicts
        has_holiday_conflict, holiday_message = check_holiday_conflicts(appointment_date)
        if has_holiday_conflict:
            flash(holiday_message, "error")
            return redirect(url_for('add_appointment'))
        
        # Check for business hours conflicts
        has_business_hours_conflict, business_hours_message = check_business_hours_conflicts(
            appointment_date, start_time, end_time
        )
        if has_business_hours_conflict:
            flash(business_hours_message, "error")
            return redirect(url_for('add_appointment'))
        
        # Check for lunch break conflicts
        has_lunch_conflict, lunch_message = check_lunch_break_conflicts(start_time, end_time)
        if has_lunch_conflict:
            flash(lunch_message, "error")
            return redirect(url_for('add_appointment'))
        
        # Check for buffer time conflicts
        has_buffer_conflict, buffer_message = check_buffer_time_conflicts(
            request.form['doctor_id'], 
            appointment_date, 
            start_time, 
            end_time
        )
        if has_buffer_conflict:
            flash(buffer_message, "error")
            return redirect(url_for('add_appointment'))
        
        # Check for maximum daily appointments
        has_max_daily_conflict, max_daily_message = check_max_daily_appointments(
            request.form['doctor_id'], 
            appointment_date
        )
        if has_max_daily_conflict:
            flash(max_daily_message, "error")
            return redirect(url_for('add_appointment'))
        
        # Check for patient conflicts
        has_patient_conflict, conflicting_patient_appointment = check_patient_appointment_conflicts(
            request.form['patient_id'], 
            appointment_date, 
            start_time, 
            end_time
        )
        
        if has_patient_conflict:
            flash(f"Patient conflict! Patient already has an appointment at {conflicting_patient_appointment.time_slot} with Dr. {conflicting_patient_appointment.doctor.name}", "error")
            return redirect(url_for('add_appointment'))
        
        # Check for patient travel time conflicts
        has_travel_time_conflict, travel_time_message = check_patient_travel_time_conflicts(
            request.form['patient_id'], 
            appointment_date, 
            start_time, 
            end_time
        )
        if has_travel_time_conflict:
            flash(travel_time_message, "error")
            return redirect(url_for('add_appointment'))
        
        new_appointment = Appointment(
            date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            diagnosis=request.form['diagnosis'],
            notes=request.form['notes'],
            patient_id=request.form['patient_id'],
            doctor_id=request.form['doctor_id']
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash("Appointment scheduled successfully!", "success")
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error scheduling appointment: {str(e)}", "error")
        return redirect(url_for('add_appointment'))

@app.route('/delete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        db.session.delete(appointment)
        db.session.commit()
        flash("Appointment cancelled successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling appointment: {str(e)}", "error")
    
    return redirect(url_for('index'))

@app.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def complete_appointment(appointment_id):
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied. Doctor or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        appointment.status = 'completed'
        db.session.commit()
        flash("Appointment marked as completed!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error completing appointment: {str(e)}", "error")
    
    return redirect(url_for('index'))

@app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Staff or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if request.method == 'POST':
        try:
            # Parse date and times
            appointment_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
            
            # Validate appointment duration (should be 30 minutes)
            start_dt = datetime.combine(datetime.min, start_time)
            end_dt = datetime.combine(datetime.min, end_time)
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            
            if duration_minutes != 30:
                flash("Appointments must be exactly 30 minutes long", "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for past date conflicts
            if appointment_date < datetime.now().date():
                flash("Cannot schedule appointments in the past", "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for weekend conflicts
            has_weekend_conflict, weekend_message = check_weekend_conflicts(appointment_date)
            if has_weekend_conflict:
                flash(weekend_message, "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for holiday conflicts
            has_holiday_conflict, holiday_message = check_holiday_conflicts(appointment_date)
            if has_holiday_conflict:
                flash(holiday_message, "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for business hours conflicts
            has_business_hours_conflict, business_hours_message = check_business_hours_conflicts(
                appointment_date, start_time, end_time
            )
            if has_business_hours_conflict:
                flash(business_hours_message, "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for lunch break conflicts
            has_lunch_conflict, lunch_message = check_lunch_break_conflicts(start_time, end_time)
            if has_lunch_conflict:
                flash(lunch_message, "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for doctor conflicts (excluding current appointment)
            has_doctor_conflict, conflicting_doctor_appointment = check_appointment_conflicts(
                request.form['doctor_id'], 
                appointment_date, 
                start_time, 
                end_time,
                exclude_appointment_id=appointment_id
            )
            
            if has_doctor_conflict:
                flash(f"Doctor conflict! Doctor already has an appointment at {conflicting_doctor_appointment.time_slot}", "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for buffer time conflicts
            has_buffer_conflict, buffer_message = check_buffer_time_conflicts(
                request.form['doctor_id'], 
                appointment_date, 
                start_time, 
                end_time,
                exclude_appointment_id=appointment_id
            )
            if has_buffer_conflict:
                flash(buffer_message, "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for maximum daily appointments
            has_max_daily_conflict, max_daily_message = check_max_daily_appointments(
                request.form['doctor_id'], 
                appointment_date,
                exclude_appointment_id=appointment_id
            )
            if has_max_daily_conflict:
                flash(max_daily_message, "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for patient conflicts (excluding current appointment)
            has_patient_conflict, conflicting_patient_appointment = check_patient_appointment_conflicts(
                request.form['patient_id'], 
                appointment_date, 
                start_time, 
                end_time,
                exclude_appointment_id=appointment_id
            )
            
            if has_patient_conflict:
                flash(f"Patient conflict! Patient already has an appointment at {conflicting_patient_appointment.time_slot} with Dr. {conflicting_patient_appointment.doctor.name}", "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            # Check for patient travel time conflicts
            has_travel_time_conflict, travel_time_message = check_patient_travel_time_conflicts(
                request.form['patient_id'], 
                appointment_date, 
                start_time, 
                end_time,
                exclude_appointment_id=appointment_id
            )
            if has_travel_time_conflict:
                flash(travel_time_message, "error")
                return redirect(url_for('edit_appointment', appointment_id=appointment_id))
            
            appointment.date = appointment_date
            appointment.start_time = start_time
            appointment.end_time = end_time
            appointment.diagnosis = request.form['diagnosis']
            appointment.notes = request.form['notes']
            appointment.patient_id = request.form['patient_id']
            appointment.doctor_id = request.form['doctor_id']
            
            db.session.commit()
            flash("Appointment updated successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating appointment: {str(e)}", "error")
    
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    return render_template('edit_appointment.html', appointment=appointment, patients=patients, doctors=doctors)

# Medical Records Management
@app.route('/upload_medical_record', methods=['GET', 'POST'])
@login_required
def upload_medical_record():
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied. Doctor or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        patients = Patient.query.all()
        doctors = Doctor.query.all()
        return render_template('upload_medical_record.html', patients=patients, doctors=doctors)
    
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            record = MedicalRecord(
                patient_id=request.form['patient_id'],
                doctor_id=request.form['doctor_id'],
                record_type=request.form['record_type'],
                file_path=unique_filename,
                file_name=filename,
                file_size=os.path.getsize(file_path),
                description=request.form['description'],
                date=datetime.now().date()  # Set the record date to today
            )
            db.session.add(record)
            db.session.commit()
            flash("Medical record uploaded successfully!", "success")
            return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error uploading medical record: {str(e)}", "error")
    
    return redirect(url_for('upload_medical_record'))

@app.route('/download_medical_record/<int:record_id>')
@login_required
def download_medical_record(record_id):
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied. Doctor or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        record = MedicalRecord.query.get_or_404(record_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], record.file_path)
        
        if os.path.exists(file_path):
            return send_from_directory(app.config['UPLOAD_FOLDER'], record.file_path, as_attachment=True)
        else:
            flash('File not found', 'error')
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_medical_record/<int:record_id>', methods=['POST'])
@login_required
def delete_medical_record(record_id):
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied. Doctor or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        record = MedicalRecord.query.get_or_404(record_id)
        
        # Delete the file
        if record.file_path:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], record.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(record)
        db.session.commit()
        flash("Medical record deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting medical record: {str(e)}", "error")
    
    return redirect(url_for('index'))

# Prescription Management
@app.route('/add_prescription', methods=['GET', 'POST'])
@login_required
def add_prescription():
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied. Doctor or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        patients = Patient.query.all()
        doctors = Doctor.query.all()
        return render_template('add_prescription.html', patients=patients, doctors=doctors)
    
    try:
        new_prescription = Prescription(
            patient_id=request.form['patient_id'],
            doctor_id=request.form['doctor_id'],
            medication_name=request.form['medication_name'],
            dosage=request.form['dosage'],
            frequency=request.form['frequency'],
            duration=request.form['duration'],
            instructions=request.form['instructions'],
            expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d') if request.form['expiry_date'] else None
        )
        db.session.add(new_prescription)
        db.session.commit()
        flash("Prescription added successfully!", "success")
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding prescription: {str(e)}", "error")
        return redirect(url_for('add_prescription'))

@app.route('/delete_prescription/<int:prescription_id>', methods=['POST'])
@login_required
def delete_prescription(prescription_id):
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied. Doctor or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        prescription = Prescription.query.get_or_404(prescription_id)
        db.session.delete(prescription)
        db.session.commit()
        flash("Prescription deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting prescription: {str(e)}", "error")
    
    return redirect(url_for('index'))

# Doctor Availability Management
@app.route('/manage_availability/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def manage_availability(doctor_id):
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied. Doctor or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # If user is a doctor, they can only manage their own availability
    if current_user.role == 'doctor':
        # Check if the doctor is trying to manage their own availability
        # For now, we'll allow doctors to manage any availability, but you can restrict this further
        pass
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        try:
            # Clear existing availability
            DoctorAvailability.query.filter_by(doctor_id=doctor_id).delete()
            
            # Add new availability
            for day in range(7):  # Monday to Sunday
                if request.form.get(f'available_{day}'):
                    availability = DoctorAvailability(
                        doctor_id=doctor_id,
                        day_of_week=day,
                        start_time=request.form.get(f'start_time_{day}', '09:00'),
                        end_time=request.form.get(f'end_time_{day}', '17:00'),
                        max_appointments=int(request.form.get(f'max_appointments_{day}', 10))
                    )
                    db.session.add(availability)
            
            db.session.commit()
            flash("Doctor availability updated successfully!", "success")
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating availability: {str(e)}", "error")
    
    # Get current availability
    availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()
    availability_dict = {a.day_of_week: a for a in availability}
    
    return render_template('manage_availability.html', doctor=doctor, availability=availability_dict)

# User Management (Admin only)
@app.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        users = User.query.all()
        return render_template('users.html', users=users)
    except Exception as e:
        flash(f"Error loading users: {str(e)}", "error")
        return render_template('users.html', users=[])

@app.route('/toggle_user_status/<int:user_id>')
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You cannot deactivate your own account!', 'error')
        else:
            user.is_active = not user.is_active
            status = 'activated' if user.is_active else 'deactivated'
            db.session.commit()
            flash(f'User {user.username} has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user status: {str(e)}', 'error')
    
    return redirect(url_for('users'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('You cannot delete your own account!', 'error')
        elif user.role == 'admin':
            flash('Cannot delete administrator accounts!', 'error')
        else:
            db.session.delete(user)
            db.session.commit()
            flash(f'User {user.username} has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('users'))

# Doctor Account Linking Route
@app.route('/link_doctor_account', methods=['GET', 'POST'])
def link_doctor_account():
    if request.method == 'GET':
        return render_template('link_doctor_account.html')
    
    try:
        license_number = request.form['license_number']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('link_doctor_account.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('link_doctor_account.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('link_doctor_account.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('link_doctor_account.html')
        
        # Find doctor by license number and email
        doctor = Doctor.query.filter_by(license_number=license_number, email=email).first()
        if not doctor:
            flash('No doctor found with this license number and email combination.', 'error')
            return render_template('link_doctor_account.html')
        
        # Create user account
        new_user = User(username=username, email=email, role='doctor')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Doctor account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating doctor account: {str(e)}', 'error')
        return render_template('link_doctor_account.html')

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate current password
            if not current_password or not current_user.check_password(current_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('settings'))
            
            # Validate new password
            if not new_password or len(new_password) < 6:
                flash('New password must be at least 6 characters long', 'error')
                return redirect(url_for('settings'))
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return redirect(url_for('settings'))
            
            # Update password
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('settings'))
    
    return render_template('settings.html')

if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", debug=debug)

