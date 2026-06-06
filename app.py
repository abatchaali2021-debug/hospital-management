from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'hospital_secret_2024'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='staff')

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    blood_group = db.Column(db.String(5))
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pending')
    notes = db.Column(db.String(200))
    patient = db.relationship('Patient', backref='appointments')
    doctor = db.relationship('Doctor', backref='appointments')

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    medicine = db.Column(db.String(200))
    dosage = db.Column(db.String(100))
    notes = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('Patient', backref='prescriptions')
    doctor = db.relationship('Doctor', backref='prescriptions')

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    amount = db.Column(db.Float)
    description = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Unpaid')
    date = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('Patient', backref='bills')

# --- ROUTES ---
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        return render_template('login.html',
                             error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()
    total_bills = Bill.query.filter_by(status='Unpaid').count()
    recent_patients = Patient.query.order_by(
        Patient.date_registered.desc()
    ).limit(5).all()
    return render_template('dashboard.html',
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         total_appointments=total_appointments,
                         total_bills=total_bills,
                         recent_patients=recent_patients)

@app.route('/patients')
def patients():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    search = request.args.get('search')
    if search:
        all_patients = Patient.query.filter(
            Patient.name.like('%' + search + '%')
        ).all()
    else:
        all_patients = Patient.query.all()
    return render_template('patients.html',
                         patients=all_patients)

@app.route('/add-patient', methods=['GET', 'POST'])
def add_patient():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_patient = Patient(
            name=request.form['name'],
            age=request.form['age'],
            gender=request.form['gender'],
            phone=request.form['phone'],
            address=request.form['address'],
            blood_group=request.form['blood_group']
        )
        db.session.add(new_patient)
        db.session.commit()
        return redirect(url_for('patients'))
    return render_template('add_patient.html')

@app.route('/delete-patient/<int:id>')
def delete_patient(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    patient = db.session.get(Patient, id)
    db.session.delete(patient)
    db.session.commit()
    return redirect(url_for('patients'))

@app.route('/doctors')
def doctors():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    all_doctors = Doctor.query.all()
    return render_template('doctors.html',
                         doctors=all_doctors)

@app.route('/add-doctor', methods=['GET', 'POST'])
def add_doctor():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_doctor = Doctor(
            name=request.form['name'],
            specialization=request.form['specialization'],
            phone=request.form['phone'],
            email=request.form['email']
        )
        db.session.add(new_doctor)
        db.session.commit()
        return redirect(url_for('doctors'))
    return render_template('add_doctor.html')

@app.route('/delete-doctor/<int:id>')
def delete_doctor(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doctor = db.session.get(Doctor, id)
    db.session.delete(doctor)
    db.session.commit()
    return redirect(url_for('doctors'))

@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    if request.method == 'POST':
        new_appointment = Appointment(
            patient_id=request.form['patient_id'],
            doctor_id=request.form['doctor_id'],
            date=request.form['date'],
            time=request.form['time'],
            notes=request.form['notes']
        )
        db.session.add(new_appointment)
        db.session.commit()
    all_appointments = Appointment.query.all()
    return render_template('appointments.html',
                         appointments=all_appointments,
                         patients=patients,
                         doctors=doctors)

@app.route('/update-appointment/<int:id>/<status>')
def update_appointment(id, status):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    appointment = db.session.get(Appointment, id)
    appointment.status = status
    db.session.commit()
    return redirect(url_for('appointments'))

@app.route('/prescriptions', methods=['GET', 'POST'])
def prescriptions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    if request.method == 'POST':
        new_prescription = Prescription(
            patient_id=request.form['patient_id'],
            doctor_id=request.form['doctor_id'],
            medicine=request.form['medicine'],
            dosage=request.form['dosage'],
            notes=request.form['notes']
        )
        db.session.add(new_prescription)
        db.session.commit()
    all_prescriptions = Prescription.query.all()
    return render_template('prescriptions.html',
                         prescriptions=all_prescriptions,
                         patients=patients,
                         doctors=doctors)

@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    patients = Patient.query.all()
    if request.method == 'POST':
        new_bill = Bill(
            patient_id=request.form['patient_id'],
            amount=float(request.form['amount']),
            description=request.form['description']
        )
        db.session.add(new_bill)
        db.session.commit()
    all_bills = Bill.query.all()
    return render_template('billing.html',
                         bills=all_bills,
                         patients=patients)

@app.route('/pay-bill/<int:id>')
def pay_bill(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    bill = db.session.get(Bill, id)
    bill.status = 'Paid'
    db.session.commit()
    return redirect(url_for('billing'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin = db.session.execute(
            db.select(User).filter_by(username='admin')
        ).scalar_one_or_none()
        if not admin:
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)