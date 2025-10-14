from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='staff')  # admin, doctor, staff
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    contact_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    blood_type = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True, cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True, cascade='all, delete-orphan')

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(50))
    license_number = db.Column(db.String(50), unique=True)
    contact_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    experience_years = db.Column(db.Integer)
    education = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    appointments = db.relationship('Appointment', backref='doctor', lazy=True, cascade='all, delete-orphan')
    availabilities = db.relationship('DoctorAvailability', backref='doctor', lazy=True, cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True, cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='doctor', lazy=True, cascade='all, delete-orphan')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    diagnosis = db.Column(db.Text)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    notes = db.Column(db.Text)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    @property
    def time_slot(self):
        """Return formatted time slot"""
        if self.start_time and self.end_time:
            return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
        return "No time set"
    
    @property
    def duration_minutes(self):
        """Calculate appointment duration in minutes"""
        if self.start_time and self.end_time:
            start = datetime.combine(datetime.min, self.start_time)
            end = datetime.combine(datetime.min, self.end_time)
            return int((end - start).total_seconds() / 60)
        return 0

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    record_type = db.Column(db.String(50))  # lab_result, xray, mri, etc.
    file_path = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    date = db.Column(db.Date, default=datetime.now().date)  # Date field for the record
    upload_date = db.Column(db.DateTime, default=datetime.now)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    medication_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    instructions = db.Column(db.Text)
    prescribed_date = db.Column(db.DateTime, default=datetime.now)
    expiry_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    day_of_week = db.Column(db.Integer)  # 0=Monday, 1=Tuesday, etc.
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))  # Fixed: Changed from Integer to String
    is_available = db.Column(db.Boolean, default=True)
    max_appointments = db.Column(db.Integer, default=10)
    