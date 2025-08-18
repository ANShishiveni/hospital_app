from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Patient, Doctor, Appointment, MedicalRecord, Prescription, DoctorAvailability
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-super-secret-key-change-in-production'
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
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@hospital.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Add sample doctors if none exist
    if not Doctor.query.first():
        sample_doctors = [
            Doctor(name="Dr. Smith", specialization="Cardiology", license_number="MD001", 
                   contact_number="+1-555-0101", email="smith@hospital.com", experience_years=15),
            Doctor(name="Dr. Johnson", specialization="Neurology", license_number="MD002",
                   contact_number="+1-555-0102", email="johnson@hospital.com", experience_years=12),
            Doctor(name="Dr. Williams", specialization="Pediatrics", license_number="MD003",
                   contact_number="+1-555-0103", email="williams@hospital.com", experience_years=8)
        ]
        for doctor in sample_doctors:
            db.session.add(doctor)
        
        db.session.commit()

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
            'today_appointments': len([a for a in appointments if a.date == datetime.now().strftime('%Y-%m-%d')])
        }
        
        return render_template('index.html', 
                             patients=patients, 
                             doctors=doctors, 
                             appointments=appointments,
                             stats=stats)
    except Exception as e:
        flash(f"Error loading data: {str(e)}", "error")
        return render_template('index.html', patients=[], doctors=[], appointments=[], stats={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        
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
        return render_template('add_patient.html')
    
    try:
        new_patient = Patient(
            name=request.form['name'],
            age=request.form['age'],
            gender=request.form['gender'],
            contact_number=request.form['contact_number'],
            address=request.form['address'],
            emergency_contact=request.form['emergency_contact'],
            emergency_phone=request.form['emergency_phone'],
            blood_type=request.form['blood_type'],
            allergies=request.form['allergies']
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
            patient.name = request.form['name']
            patient.age = request.form['age']
            patient.gender = request.form['gender']
            patient.contact_number = request.form['contact_number']
            patient.address = request.form['address']
            patient.emergency_contact = request.form['emergency_contact']
            patient.emergency_phone = request.form['emergency_phone']
            patient.blood_type = request.form['blood_type']
            patient.allergies = request.form['allergies']
            
            db.session.commit()
            flash("Patient updated successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating patient: {str(e)}", "error")
    
    return render_template('edit_patient.html', patient=patient)

@app.route('/delete_patient/<int:patient_id>')
@login_required
def delete_patient(patient_id):
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Staff or admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        patient = Patient.query.get_or_404(patient_id)
        db.session.delete(patient)
        db.session.commit()
        flash("Patient deleted successfully!", "success")
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
            name=request.form['name'],
            specialization=request.form['specialization'],
            license_number=request.form['license_number'],
            contact_number=request.form['contact_number'],
            email=request.form['email'],
            experience_years=request.form['experience_years'],
            education=request.form['education']
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
            doctor.name = request.form['name']
            doctor.specialization = request.form['specialization']
            doctor.license_number = request.form['license_number']
            doctor.contact_number = request.form['contact_number']
            doctor.email = request.form['email']
            doctor.experience_years = request.form['experience_years']
            doctor.education = request.form['education']
            
            db.session.commit()
            flash("Doctor updated successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating doctor: {str(e)}", "error")
    
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/delete_doctor/<int:doctor_id>')
@login_required
def delete_doctor(doctor_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        doctor = Doctor.query.get_or_404(doctor_id)
        db.session.delete(doctor)
        db.session.commit()
        flash("Doctor deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting doctor: {str(e)}", "error")
    
    return redirect(url_for('index'))

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
        new_appointment = Appointment(
            date=request.form['date'],
            time=request.form['time'],
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

@app.route('/delete_appointment/<int:appointment_id>')
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

@app.route('/complete_appointment/<int:appointment_id>')
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
            appointment.date = request.form['date']
            appointment.time = request.form['time']
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
                description=request.form['description']
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

@app.route('/delete_medical_record/<int:record_id>')
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

@app.route('/delete_prescription/<int:prescription_id>')
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

@app.route('/delete_user/<int:user_id>')
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

if __name__ == '__main__':
    app.run(debug=True)

