# Hospital Management System - Enhanced Edition

A comprehensive, professional-grade hospital management application built with Flask, SQLite, and Bootstrap. This enhanced version includes advanced features like user authentication, medical record management, prescription tracking, and doctor availability scheduling.

## New Features Implemented

### User Authentication System
- **Secure Login**: Professional login interface with session management
- **Role-based Access**: Support for admin, doctor, and staff roles
- **Session Security**: Flask-Login integration with secure password hashing
- **Demo Credentials**: Username: `admin`, Password: `admin123`
- **Account Creation**: Self-registration system for new users
- **User Management**: Admin interface for managing user accounts
- **Password Security**: Strong password requirements and validation

### Medical Record Management
- **File Uploads**: Support for PDF, DOC, images, and other medical documents
- **Secure Storage**: Unique filename generation with UUID protection
- **File Types**: Lab results, X-rays, MRI scans, CT scans, blood tests, etc.
- **Download & Delete**: Secure file access and management

### Prescription Management
- **Medication Tracking**: Complete prescription lifecycle management
- **Dosage Information**: Frequency, duration, and special instructions
- **Expiry Dates**: Medication expiration tracking
- **Patient-Doctor Linking**: Prescription attribution and history

### Doctor Availability System
- **Weekly Scheduling**: Monday through Sunday availability management
- **Time Slots**: Customizable start/end times for each day
- **Appointment Limits**: Maximum appointments per day configuration
- **Visual Interface**: Interactive calendar-style availability management

### 5. Account Creation & User Management
- **Self-Registration**: Users can create their own accounts
- **Role Selection**: Choose between staff, doctor, or admin roles
- **Password Validation**: Strong password requirements with strength indicator
- **Admin Controls**: User activation/deactivation and deletion
- **User Statistics**: Overview of user counts and roles
- **Security Features**: Username/email uniqueness validation

### Professional UI/UX
- **Modern Design**: Bootstrap 5.3 with custom styling
- **Responsive Layout**: Mobile-first design approach
- **Icon Integration**: Font Awesome icons throughout the interface
- **Color-coded Elements**: Intuitive visual feedback system

## Enhanced Database Schema

### Core Entities
- **Users**: Authentication and role management
- **Patients**: Extended profile with medical information
- **Doctors**: Comprehensive professional profiles
- **Appointments**: Enhanced scheduling with time and notes
- **Medical Records**: File management and categorization
- **Prescriptions**: Complete medication tracking
- **Doctor Availability**: Weekly schedule management

### Advanced Features
- **Foreign Key Relationships**: Proper database normalization
- **Audit Trails**: Creation timestamps for all records
- **Data Validation**: Comprehensive input validation
- **Error Handling**: Graceful error management with user feedback

## Installation & Setup

### Prerequisites
- Python 3.9+ (Recommended: Python 3.13.6)
- pip package manager
- Modern web browser

### Quick Start
```bash
# 1. Clone or download the project
cd hospital_app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py

# 4. Access the system
# Open browser: http://localhost:5000
# Login: admin / admin123
```

## Extra Features Implemented

### 1. Medical Record Uploads (File Handling)
- **Secure File Storage**: UUID-based filename generation
- **Multiple Formats**: PDF, DOC, images, medical scans
- **File Management**: Upload, download, and delete operations
- **Categorization**: Record type classification system

### 2. User Authentication
- **Flask-Login Integration**: Professional session management
- **Password Security**: Werkzeug password hashing
- **Role Management**: Admin, doctor, staff role support
- **Session Protection**: Login-required decorators

### 3. Prescription Management
- **Medication Tracking**: Complete prescription lifecycle
- **Dosage Management**: Frequency, duration, instructions
- **Expiry Tracking**: Medication expiration dates
- **Patient History**: Comprehensive prescription records

### 4. Doctor Availability System
- **Weekly Scheduling**: 7-day availability management
- **Time Slot Configuration**: Customizable hours per day
- **Appointment Limits**: Daily capacity management
- **Visual Interface**: Interactive availability cards

## UI/UX Enhancements

### Design Features
- **Modern Bootstrap 5.3**: Latest responsive framework
- **Custom Styling**: Professional color schemes and layouts
- **Icon Integration**: Font Awesome icons for better UX
- **Responsive Design**: Mobile-first approach
- **Interactive Elements**: Hover effects and animations

### Navigation
- **Sidebar Navigation**: Organized feature categories
- **Breadcrumb Trails**: Clear navigation paths
- **Quick Actions**: Dashboard shortcuts for common tasks
- **Consistent Layout**: Unified design language

## 🔧 Technical Implementation

### Backend Architecture
- **Flask 3.0.0**: Latest stable Flask version
- **SQLAlchemy 2.0**: Modern ORM with relationship management
- **Flask-Login**: Professional authentication system
- **File Handling**: Secure file upload and management
- **Error Handling**: Comprehensive exception management

### Database Features
- **SQLite**: Lightweight, file-based database
- **Relationships**: Proper foreign key constraints
- **Indexing**: Optimized query performance
- **Data Integrity**: Constraint validation and error handling

### Security Features
- **Password Hashing**: Secure password storage
- **Session Management**: Flask-Login security
- **File Validation**: Secure file upload handling
- **Input Sanitization**: Form validation and sanitization

## User Interface Features

### Dashboard
- **Statistics Cards**: Real-time data overview
- **Quick Actions**: Common task shortcuts
- **Tabbed Interface**: Organized feature access
- **Responsive Grid**: Adaptive layout system

### Forms
- **Professional Styling**: Bootstrap form components
- **Validation**: Client and server-side validation
- **Error Handling**: User-friendly error messages
- **Responsive Layout**: Mobile-optimized forms

### Tables
- **Data Display**: Organized information presentation
- **Action Buttons**: Edit, delete, and manage options
- **Responsive Design**: Mobile-friendly table layouts
- **Status Indicators**: Visual status representation

## Getting Started

### First Time Setup
1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Run Application**: `python app.py`
3. **Access System**: Navigate to `http://localhost:5000`
4. **Login**: Use demo credentials (admin/admin123)

### Initial Configuration
- **Sample Data**: System starts with sample doctors
- **Database Creation**: Tables created automatically
- **Admin User**: Default admin account created
- **File Storage**: Upload directory created automatically

## Feature Walkthrough

### 1. Authentication
- Professional login interface
- Secure session management
- Role-based access control

### 2. Patient Management
- Extended patient profiles
- Medical information tracking
- Emergency contact details
- Allergy and blood type information

### 3. Doctor Management
- Comprehensive doctor profiles
- Specialization and experience tracking
- License and contact information
- Availability scheduling

### 4. Appointment System
- Advanced scheduling with time slots
- Patient-doctor linking
- Diagnosis and notes tracking
- Status management

### 5. Medical Records
- Secure file upload system
- Multiple file format support
- Categorization and description
- Download and management

### 6. Prescriptions
- Complete medication tracking
- Dosage and frequency management
- Expiry date tracking
- Patient instruction management

### 7. Doctor Availability
- Weekly schedule management
- Time slot configuration
- Appointment capacity limits
- Visual availability interface

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Change port in `app.py` if needed
2. **Database Errors**: Delete `hospital.db` and restart
3. **Import Errors**: Ensure all dependencies installed
4. **File Upload Issues**: Check upload directory permissions

### Error Messages
- **Authentication Errors**: Check username/password
- **Database Issues**: Verify database file permissions
- **File Upload Errors**: Check file size and format
- **Validation Errors**: Review form input requirements

## Future Enhancements

### Planned Features
1. **Advanced Reporting**: Analytics and data visualization
2. **Email Notifications**: Appointment reminders and updates
3. **API Integration**: RESTful API for external systems
4. **Mobile App**: React Native mobile application
5. **Advanced Security**: Two-factor authentication
6. **Backup System**: Automated data backup and recovery

### Technical Improvements
1. **Performance Optimization**: Database query optimization
2. **Caching**: Redis integration for performance
3. **Testing**: Comprehensive test suite
4. **CI/CD**: Automated deployment pipeline
5. **Monitoring**: Application performance monitoring

## Technical Documentation

### Code Structure
```
hospital_app/
├── app.py                 # Main Flask application
├── models.py             # Database models and relationships
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── uploads/             # Medical record storage
└── templates/           # HTML templates
    ├── login.html       # Authentication interface
    ├── index.html       # Main dashboard
    ├── add_patient.html # Patient management
    ├── add_doctor.html  # Doctor management
    ├── add_appointment.html # Appointment scheduling
    ├── upload_medical_record.html # File upload
    ├── add_prescription.html # Prescription management
    ├── manage_availability.html # Doctor scheduling
    ├── edit_patient.html # Patient editing
    └── edit_doctor.html # Doctor editing
```

### Database Schema
- **Users**: Authentication and roles
- **Patients**: Extended medical profiles
- **Doctors**: Professional information
- **Appointments**: Scheduling and management
- **Medical Records**: File storage and metadata
- **Prescriptions**: Medication tracking
- **Doctor Availability**: Schedule management

## Support & Contributing

### Getting Help
- **Documentation**: Comprehensive README and code comments
- **Error Logs**: Check console output for detailed errors
- **Dependencies**: Verify all packages installed correctly
- **Python Version**: Ensure Python 3.9+ compatibility

### Contributing
1. **Fork Repository**: Create your own copy
2. **Feature Branch**: Work on new features
3. **Testing**: Ensure all functionality works
4. **Pull Request**: Submit changes for review

## 📄 License

This project is created for educational purposes as part of the CMP3872 Database Programming course. All code is provided as-is for learning and demonstration purposes.

---

---

**Developed with LOVE using Flask, SQLAlchemy, Bootstrap, and modern web technologies**
