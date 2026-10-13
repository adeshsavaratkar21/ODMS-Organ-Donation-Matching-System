import os
from datetime import datetime, date, timedelta
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-only-change-this-secret')
db_url = os.getenv('DATABASE_URL', 'sqlite:///odms.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True, origins=[os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173'), 'http://127.0.0.1:5173'])

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    code = db.Column(db.String(40), unique=True, nullable=False)
    facility_type = db.Column(db.String(40), default='Hospital')
    region = db.Column(db.String(120), default='Mumbai')
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False, default='Medical Coordinator')
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'))
    active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    blood_group = db.Column(db.String(3), nullable=False)
    rh_factor = db.Column(db.String(8), default='Positive')
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    organ_type = db.Column(db.String(40), nullable=False)
    medical_notes = db.Column(db.Text, default='')
    screening_status = db.Column(db.String(30), default='Pending')
    availability_status = db.Column(db.String(30), default='Available', nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    blood_group = db.Column(db.String(3), nullable=False)
    rh_factor = db.Column(db.String(8), default='Positive')
    required_organ = db.Column(db.String(40), nullable=False)
    urgency = db.Column(db.String(20), default='Routine', nullable=False)
    waiting_list_date = db.Column(db.Date, default=date.today, nullable=False)
    medical_notes = db.Column(db.Text, default='')
    waitlist_status = db.Column(db.String(30), default='Active', nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class MatchRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_code = db.Column(db.String(40), unique=True, nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id'), nullable=False)
    initiated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    algorithm_version = db.Column(db.String(30), default='ODMS-demo-1.0')
    execution_status = db.Column(db.String(30), default='Completed')
    total_candidates_checked = db.Column(db.Integer, default=0)
    eligible_candidates_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class MatchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_run_id = db.Column(db.Integer, db.ForeignKey('match_run.id'), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.id'), nullable=False)
    compatibility_status = db.Column(db.String(40), nullable=False)
    ranking_score = db.Column(db.Integer, default=0)
    ranking_position = db.Column(db.Integer, default=0)
    ranking_explanation = db.Column(db.String(300), default='')
    review_status = db.Column(db.String(30), default='Pending', nullable=False)
    review_notes = db.Column(db.Text, default='')
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    notification_type = db.Column(db.String(40), default='Info')
    related_match_result_id = db.Column(db.Integer, db.ForeignKey('match_result.id'))
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'))
    action = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(60))
    outcome = db.Column(db.String(30), default='Success')
    details = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

BLOOD_GROUPS = {'O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'}
ORGANS = {'Kidney', 'Liver', 'Heart', 'Lung', 'Pancreas'}

# Educational ABO/Rh screening approximation only; not clinical allocation guidance.
ABO_COMPAT = {
    'O-': {'O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'},
    'O+': {'O+', 'A+', 'B+', 'AB+'},
    'A-': {'A-', 'A+', 'AB-', 'AB+'},
    'A+': {'A+', 'AB+'},
    'B-': {'B-', 'B+', 'AB-', 'AB+'},
    'B+': {'B+', 'AB+'},
    'AB-': {'AB-', 'AB+'},
    'AB+': {'AB+'},
}


def current_user():
    uid = session.get('user_id')
    return db.session.get(User, uid) if uid else None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user.active:
            return jsonify({'error': 'Please log in to continue.'}), 401
        return fn(*args, **kwargs)
    return wrapper

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user or not user.active:
                return jsonify({'error': 'Please log in to continue.'}), 401
            if user.role not in roles:
                return jsonify({'error': 'You do not have permission to perform this action.'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def audit(action, entity_type, entity_id=None, details=''):
    user = current_user()
    db.session.add(AuditLog(user_id=user.id if user else None, facility_id=user.facility_id if user else None,
                            action=action, entity_type=entity_type, entity_id=str(entity_id) if entity_id is not None else None,
                            details=details[:300]))

def notify_user(user_id, title, message, kind='Info', match_id=None):
    db.session.add(Notification(user_id=user_id, title=title, message=message,
                                notification_type=kind, related_match_result_id=match_id))

def serialize_facility(f):
    return {'id': f.id, 'name': f.name, 'code': f.code, 'facility_type': f.facility_type, 'region': f.region}
def serialize_user(u):
    f = db.session.get(Facility, u.facility_id) if u.facility_id else None
    return {'id': u.id, 'full_name': u.full_name, 'email': u.email, 'role': u.role,
            'facility_id': u.facility_id, 'facility_name': f.name if f else 'System'}
def serialize_donor(d):
    f = db.session.get(Facility, d.facility_id)
    return {'id': d.id, 'donor_code': d.donor_code, 'display_name': d.display_name, 'age': d.age,
            'blood_group': d.blood_group, 'rh_factor': d.rh_factor, 'height_cm': d.height_cm, 'weight_kg': d.weight_kg,
            'organ_type': d.organ_type, 'medical_notes': d.medical_notes, 'screening_status': d.screening_status,
            'availability_status': d.availability_status, 'facility_id': d.facility_id,
            'facility_name': f.name if f else 'Unknown', 'active': d.active,
            'created_at': d.created_at.isoformat() + 'Z', 'updated_at': d.updated_at.isoformat() + 'Z'}
def serialize_recipient(r):
    f = db.session.get(Facility, r.facility_id)
    return {'id': r.id, 'recipient_code': r.recipient_code, 'display_name': r.display_name, 'age': r.age,
            'blood_group': r.blood_group, 'rh_factor': r.rh_factor, 'required_organ': r.required_organ,
            'urgency': r.urgency, 'waiting_list_date': r.waiting_list_date.isoformat(), 'medical_notes': r.medical_notes,
            'waitlist_status': r.waitlist_status, 'facility_id': r.facility_id, 'facility_name': f.name if f else 'Unknown',
            'created_at': r.created_at.isoformat() + 'Z', 'updated_at': r.updated_at.isoformat() + 'Z'}
def serialize_match_result(m):
    donor, recipient = db.session.get(Donor, m.donor_id), db.session.get(Recipient, m.recipient_id)
    return {'id': m.id, 'match_run_id': m.match_run_id, 'donor_id': m.donor_id,
            'donor_code': donor.donor_code if donor else '—', 'organ_type': donor.organ_type if donor else '—',
            'recipient_id': m.recipient_id, 'recipient_code': recipient.recipient_code if recipient else '—',
            'recipient_name': recipient.display_name if recipient else '—', 'recipient_blood_group': recipient.blood_group if recipient else '—',
            'facility_name': db.session.get(Facility, recipient.facility_id).name if recipient and db.session.get(Facility, recipient.facility_id) else '—',
            'compatibility_status': m.compatibility_status, 'ranking_score': m.ranking_score,
            'ranking_position': m.ranking_position, 'ranking_explanation': m.ranking_explanation,
            'review_status': m.review_status, 'review_notes': m.review_notes,
            'reviewed_at': m.reviewed_at.isoformat() + 'Z' if m.reviewed_at else None,
            'created_at': m.created_at.isoformat() + 'Z'}

def parse_record_payload(data, recipient=False):
    errors = {}
    code_key = 'recipient_code' if recipient else 'donor_code'
    code = str(data.get(code_key, '')).strip().upper()
    name = str(data.get('display_name', '')).strip()
    try: age = int(data.get('age', 0))
    except (TypeError, ValueError): age = 0
    blood = str(data.get('blood_group', '')).upper().strip()
    organ_key = 'required_organ' if recipient else 'organ_type'
    organ = str(data.get(organ_key, '')).strip().title()
    try: facility_id = int(data.get('facility_id') or 0)
    except (TypeError, ValueError): facility_id = 0
    if not code: errors[code_key] = 'A unique identifier is required.'
    if not name: errors['display_name'] = 'Name or demonstration identifier is required.'
    if age < 1 or age > 120: errors['age'] = 'Age must be between 1 and 120.'
    if blood not in BLOOD_GROUPS: errors['blood_group'] = 'Choose a valid blood group.'
    if organ not in ORGANS: errors[organ_key] = 'Choose a valid organ type.'
    if not db.session.get(Facility, facility_id): errors['facility_id'] = 'Choose a valid facility.'
    if errors: return None, errors
    common = {'code': code, 'name': name, 'age': age, 'blood': blood, 'organ': organ, 'facility_id': facility_id}
    if recipient:
        urgency = str(data.get('urgency', 'Routine')).title()
        status = str(data.get('waitlist_status', 'Active')).title()
        if urgency not in {'Routine', 'Urgent', 'Critical'}: errors['urgency'] = 'Choose a valid urgency level.'
        if status not in {'Active', 'Inactive', 'Matched'}: errors['waitlist_status'] = 'Choose a valid status.'
        try: wait_date = date.fromisoformat(str(data.get('waiting_list_date') or date.today().isoformat()))
        except ValueError: wait_date = date.today(); errors['waiting_list_date'] = 'Use YYYY-MM-DD.'
        if errors: return None, errors
        common.update(urgency=urgency, status=status, wait_date=wait_date, notes=str(data.get('medical_notes', '')).strip()[:2000], rh_factor=str(data.get('rh_factor', 'Positive')).title())
    else:
        status = str(data.get('availability_status', 'Available')).title()
        screening = str(data.get('screening_status', 'Pending')).title()
        if status not in {'Available', 'Unavailable', 'Procurement Locked', 'Inactive'}: errors['availability_status'] = 'Choose a valid availability status.'
        if screening not in {'Pending', 'In Review', 'Cleared', 'Flagged'}: errors['screening_status'] = 'Choose a valid screening status.'
        try: height = float(data['height_cm']) if data.get('height_cm') not in (None, '') else None
        except (TypeError, ValueError): height = None; errors['height_cm'] = 'Height must be numeric.'
        try: weight = float(data['weight_kg']) if data.get('weight_kg') not in (None, '') else None
        except (TypeError, ValueError): weight = None; errors['weight_kg'] = 'Weight must be numeric.'
        if height is not None and not 30 <= height <= 260: errors['height_cm'] = 'Height must be between 30 and 260 cm.'
        if weight is not None and not 1 <= weight <= 500: errors['weight_kg'] = 'Weight must be between 1 and 500 kg.'
        if errors: return None, errors
        common.update(status=status, screening=screening, height=height, weight=weight, notes=str(data.get('medical_notes', '')).strip()[:2000], rh_factor=str(data.get('rh_factor', 'Positive')).title())
    return common, None

@app.get('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'ODMS API', 'database': 'configured'})

@app.post('/api/auth/login')
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    user = User.query.filter(func.lower(User.email) == email).first()
    if not user or not user.active:
        db.session.add(AuditLog(user_id=user.id if user else None, action='LOGIN_FAILED', entity_type='User', entity_id=str(user.id) if user else email, outcome='Denied', details='Invalid credentials or inactive account'))
        db.session.commit()
        return jsonify({'error': 'Invalid email or password.'}), 401
    if user.locked_until and user.locked_until > datetime.utcnow():
        return jsonify({'error': 'Account temporarily locked after repeated failed attempts.'}), 423
    if not bcrypt.check_password_hash(user.password_hash, password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=10)
            user.failed_login_attempts = 0
        db.session.add(AuditLog(user_id=user.id, action='LOGIN_FAILED', entity_type='User', entity_id=str(user.id), outcome='Denied', details='Invalid credentials'))
        db.session.commit()
        return jsonify({'error': 'Invalid email or password.'}), 401
    session.clear(); session['user_id'] = user.id
    user.failed_login_attempts = 0; user.locked_until = None; user.last_login_at = datetime.utcnow()
    db.session.add(AuditLog(user_id=user.id, facility_id=user.facility_id, action='LOGIN', entity_type='User', entity_id=str(user.id)))
    db.session.commit()
    return jsonify({'user': serialize_user(user)})

@app.post('/api/auth/logout')
def logout():
    user = current_user()
    if user: audit('LOGOUT', 'User', user.id)
    session.clear(); db.session.commit()
    return jsonify({'message': 'Logged out successfully.'})

@app.get('/api/auth/me')
def me():
    user = current_user()
    if not user or not user.active: return jsonify({'user': None}), 200
    return jsonify({'user': serialize_user(user)})

@app.get('/api/facilities')
@login_required
def facilities():
    return jsonify([serialize_facility(f) for f in Facility.query.filter_by(active=True).order_by(Facility.name).all()])

@app.get('/api/donors')
@login_required
def get_donors():
    q = Donor.query.filter_by(active=True)
    search = request.args.get('search', '').strip()
    if search: q = q.filter(or_(Donor.donor_code.ilike(f'%{search}%'), Donor.display_name.ilike(f'%{search}%')))
    if request.args.get('organ'): q = q.filter_by(organ_type=request.args['organ'])
    if request.args.get('blood_group'): q = q.filter_by(blood_group=request.args['blood_group'])
    if request.args.get('status'): q = q.filter_by(availability_status=request.args['status'])
    return jsonify([serialize_donor(d) for d in q.order_by(Donor.created_at.desc()).all()])

@app.post('/api/donors')
@login_required
def create_donor():
    data = request.get_json(silent=True) or {}; parsed, errors = parse_record_payload(data)
    if errors: return jsonify({'error': 'Please correct the highlighted fields.', 'fields': errors}), 400
    if Donor.query.filter_by(donor_code=parsed['code']).first(): return jsonify({'error': 'That donor ID already exists.'}), 409
    user = current_user()
    donor = Donor(donor_code=parsed['code'], display_name=parsed['name'], age=parsed['age'], blood_group=parsed['blood'],
                  rh_factor=parsed['rh_factor'], height_cm=parsed['height'], weight_kg=parsed['weight'], organ_type=parsed['organ'],
                  medical_notes=parsed['notes'], screening_status=parsed['screening'], availability_status=parsed['status'],
                  facility_id=parsed['facility_id'], created_by_user_id=user.id)
    db.session.add(donor); db.session.flush(); audit('DONOR_CREATED', 'Donor', donor.id, f'Created {donor.donor_code}')
    db.session.commit(); return jsonify({'donor': serialize_donor(donor)}), 201

@app.get('/api/donors/<int:record_id>')
@login_required
def get_donor(record_id):
    d = db.session.get(Donor, record_id)
    if not d or not d.active: return jsonify({'error': 'Donor not found.'}), 404
    return jsonify({'donor': serialize_donor(d)})

@app.patch('/api/donors/<int:record_id>')
@login_required
def update_donor(record_id):
    d = db.session.get(Donor, record_id)
    if not d or not d.active: return jsonify({'error': 'Donor not found.'}), 404
    data = request.get_json(silent=True) or {}; merged = serialize_donor(d); merged.update(data)
    parsed, errors = parse_record_payload(merged)
    if errors: return jsonify({'error': 'Please correct the highlighted fields.', 'fields': errors}), 400
    duplicate = Donor.query.filter(Donor.donor_code == parsed['code'], Donor.id != d.id).first()
    if duplicate: return jsonify({'error': 'That donor ID already exists.'}), 409
    d.donor_code=parsed['code']; d.display_name=parsed['name']; d.age=parsed['age']; d.blood_group=parsed['blood']; d.rh_factor=parsed['rh_factor']; d.height_cm=parsed['height']; d.weight_kg=parsed['weight']; d.organ_type=parsed['organ']; d.medical_notes=parsed['notes']; d.screening_status=parsed['screening']; d.availability_status=parsed['status']; d.facility_id=parsed['facility_id']
    audit('DONOR_UPDATED', 'Donor', d.id, f'Updated {d.donor_code}'); db.session.commit()
    return jsonify({'donor': serialize_donor(d)})

@app.patch('/api/donors/<int:record_id>/status')
@login_required
def donor_status(record_id):
    d = db.session.get(Donor, record_id)
    if not d: return jsonify({'error': 'Donor not found.'}), 404
    status = str((request.get_json(silent=True) or {}).get('availability_status', '')).title()
    if status not in {'Available', 'Unavailable', 'Procurement Locked', 'Inactive'}: return jsonify({'error': 'Invalid availability status.'}), 400
    d.availability_status=status
    if status == 'Inactive': d.active=False
    audit('DONOR_STATUS_CHANGED', 'Donor', d.id, f'Status: {status}'); db.session.commit()
    return jsonify({'donor': serialize_donor(d)})

@app.get('/api/recipients')
@login_required
def get_recipients():
    q = Recipient.query
    search = request.args.get('search', '').strip()
    if search: q = q.filter(or_(Recipient.recipient_code.ilike(f'%{search}%'), Recipient.display_name.ilike(f'%{search}%')))
    if request.args.get('organ'): q = q.filter_by(required_organ=request.args['organ'])
    if request.args.get('blood_group'): q = q.filter_by(blood_group=request.args['blood_group'])
    if request.args.get('status'): q = q.filter_by(waitlist_status=request.args['status'])
    if request.args.get('urgency'): q = q.filter_by(urgency=request.args['urgency'])
    return jsonify([serialize_recipient(r) for r in q.order_by(Recipient.created_at.desc()).all()])

@app.post('/api/recipients')
@login_required
def create_recipient():
    data = request.get_json(silent=True) or {}; parsed, errors = parse_record_payload(data, recipient=True)
    if errors: return jsonify({'error': 'Please correct the highlighted fields.', 'fields': errors}), 400
    if Recipient.query.filter_by(recipient_code=parsed['code']).first(): return jsonify({'error': 'That recipient ID already exists.'}), 409
    user=current_user()
    r=Recipient(recipient_code=parsed['code'], display_name=parsed['name'], age=parsed['age'], blood_group=parsed['blood'], rh_factor=parsed['rh_factor'], required_organ=parsed['organ'], urgency=parsed['urgency'], waiting_list_date=parsed['wait_date'], medical_notes=parsed['notes'], waitlist_status=parsed['status'], facility_id=parsed['facility_id'], created_by_user_id=user.id)
    db.session.add(r); db.session.flush(); audit('RECIPIENT_CREATED', 'Recipient', r.id, f'Created {r.recipient_code}'); db.session.commit()
    return jsonify({'recipient': serialize_recipient(r)}), 201

@app.get('/api/recipients/<int:record_id>')
@login_required
def get_recipient(record_id):
    r=db.session.get(Recipient, record_id)
    if not r: return jsonify({'error': 'Recipient not found.'}), 404
    return jsonify({'recipient': serialize_recipient(r)})

@app.patch('/api/recipients/<int:record_id>')
@login_required
def update_recipient(record_id):
    r=db.session.get(Recipient, record_id)
    if not r: return jsonify({'error': 'Recipient not found.'}), 404
    data=request.get_json(silent=True) or {}; merged=serialize_recipient(r); merged.update(data)
    parsed, errors=parse_record_payload(merged, recipient=True)
    if errors: return jsonify({'error': 'Please correct the highlighted fields.', 'fields': errors}), 400
    duplicate=Recipient.query.filter(Recipient.recipient_code == parsed['code'], Recipient.id != r.id).first()
    if duplicate: return jsonify({'error': 'That recipient ID already exists.'}), 409
    r.recipient_code=parsed['code']; r.display_name=parsed['name']; r.age=parsed['age']; r.blood_group=parsed['blood']; r.rh_factor=parsed['rh_factor']; r.required_organ=parsed['organ']; r.urgency=parsed['urgency']; r.waiting_list_date=parsed['wait_date']; r.medical_notes=parsed['notes']; r.waitlist_status=parsed['status']; r.facility_id=parsed['facility_id']
    audit('RECIPIENT_UPDATED', 'Recipient', r.id, f'Updated {r.recipient_code}'); db.session.commit()
    return jsonify({'recipient': serialize_recipient(r)})

@app.patch('/api/recipients/<int:record_id>/status')
@login_required
def recipient_status(record_id):
    r=db.session.get(Recipient, record_id)
    if not r: return jsonify({'error': 'Recipient not found.'}), 404
    status=str((request.get_json(silent=True) or {}).get('waitlist_status', '')).title()
    if status not in {'Active', 'Inactive', 'Matched'}: return jsonify({'error': 'Invalid waitlist status.'}), 400
    r.waitlist_status=status; audit('RECIPIENT_STATUS_CHANGED', 'Recipient', r.id, f'Status: {status}'); db.session.commit()
    return jsonify({'recipient': serialize_recipient(r)})

@app.post('/api/matches/run')
@login_required
def run_matching():
    data=request.get_json(silent=True) or {}
    try: donor_id=int(data.get('donor_id'))
    except (TypeError, ValueError): return jsonify({'error': 'Select a donor to run matching.'}), 400
    donor=db.session.get(Donor, donor_id)
    if not donor or not donor.active or donor.availability_status != 'Available': return jsonify({'error': 'This donor is not available for a new match run.'}), 400
    candidates=Recipient.query.filter_by(required_organ=donor.organ_type, waitlist_status='Active').all()
    run=MatchRun(run_code=f'MR-{datetime.utcnow().strftime("%y%m%d%H%M%S")}-{donor.id}', donor_id=donor.id, initiated_by_user_id=current_user().id, total_candidates_checked=len(candidates))
    db.session.add(run); db.session.flush()
    compatible=[]
    for r in candidates:
        ok = r.blood_group in ABO_COMPAT.get(donor.blood_group, set())
        if not ok: continue
        days_waiting=max(0, (date.today()-r.waiting_list_date).days)
        urgency_score={'Routine': 10, 'Urgent': 25, 'Critical': 40}.get(r.urgency, 10)
        waiting_score=min(days_waiting // 30, 30)
        score=urgency_score+waiting_score
        compatible.append((r, score, days_waiting, urgency_score))
    compatible.sort(key=lambda x: (-x[1], x[2]*-1, x[0].recipient_code))
    results=[]
    for position,(r,score,days_waiting,urgency_score) in enumerate(compatible, start=1):
        result=MatchResult(match_run_id=run.id, donor_id=donor.id, recipient_id=r.id, compatibility_status='Potential candidate — clinical review required', ranking_score=score, ranking_position=position, ranking_explanation=f'Urgency score {urgency_score}; waiting-time contribution {min(days_waiting // 30,30)} (months capped at 30 points).')
        db.session.add(result); db.session.flush(); results.append(result)
        notify_user(current_user().id, 'Matching run completed', f'{run.run_code}: {len(compatible)} potential candidate(s) generated.', 'Match', result.id)
    run.eligible_candidates_count=len(compatible)
    audit('MATCH_RUN_CREATED', 'MatchRun', run.id, f'{run.run_code}; checked {len(candidates)} active organ-compatible recipient(s); {len(compatible)} ABO-screened candidate(s)')
    db.session.commit()
    return jsonify({'run': {'id': run.id, 'run_code': run.run_code, 'donor_id': donor.id, 'total_candidates_checked': run.total_candidates_checked, 'eligible_candidates_count': run.eligible_candidates_count, 'created_at': run.created_at.isoformat()+'Z'}, 'results': [serialize_match_result(x) for x in results], 'notice': 'Educational screening only. These are not clinical compatibility determinations or transplant allocation decisions.'}), 201

@app.get('/api/matches/runs')
@login_required
def get_match_runs():
    runs=MatchRun.query.order_by(MatchRun.created_at.desc()).limit(100).all()
    return jsonify([{'id':r.id,'run_code':r.run_code,'donor_id':r.donor_id,'donor_code':db.session.get(Donor,r.donor_id).donor_code if db.session.get(Donor,r.donor_id) else '—','total_candidates_checked':r.total_candidates_checked,'eligible_candidates_count':r.eligible_candidates_count,'created_at':r.created_at.isoformat()+'Z'} for r in runs])

@app.get('/api/matches/runs/<int:run_id>')
@login_required
def get_match_run(run_id):
    run=db.session.get(MatchRun,run_id)
    if not run: return jsonify({'error':'Match run not found.'}),404
    results=MatchResult.query.filter_by(match_run_id=run.id).order_by(MatchResult.ranking_position).all()
    return jsonify({'run':{'id':run.id,'run_code':run.run_code,'donor_id':run.donor_id,'total_candidates_checked':run.total_candidates_checked,'eligible_candidates_count':run.eligible_candidates_count,'created_at':run.created_at.isoformat()+'Z'},'results':[serialize_match_result(m) for m in results]})

@app.get('/api/matches/results')
@login_required
def all_match_results():
    return jsonify([serialize_match_result(m) for m in MatchResult.query.order_by(MatchResult.created_at.desc()).limit(200).all()])

@app.patch('/api/matches/results/<int:result_id>/review')
@roles_required('Medical Coordinator','OPO Administrator','System Administrator')
def review_match(result_id):
    m=db.session.get(MatchResult,result_id)
    if not m: return jsonify({'error':'Match result not found.'}),404
    data=request.get_json(silent=True) or {}; status=str(data.get('review_status','')).title(); notes=str(data.get('review_notes','')).strip()[:1000]
    if status not in {'Pending','Accepted','Declined','Needs Review'}: return jsonify({'error':'Invalid review status.'}),400
    if status == 'Accepted':
        donor=db.session.get(Donor,m.donor_id)
        if not donor or donor.availability_status != 'Available': return jsonify({'error':'Donor is no longer available.'}),409
        # Demo lock is transactional. This does not authorize procurement or transplantation.
        donor.availability_status='Procurement Locked'
        for other in MatchResult.query.filter(MatchResult.donor_id==donor.id, MatchResult.id!=m.id, MatchResult.review_status=='Pending').all():
            other.review_status='Needs Review'
    m.review_status=status; m.review_notes=notes; m.reviewed_by_user_id=current_user().id; m.reviewed_at=datetime.utcnow()
    audit('MATCH_REVIEWED','MatchResult',m.id,f'Status: {status}')
    notify_user(current_user().id,'Match review updated',f'{m.id}: status changed to {status}.','Match',m.id)
    db.session.commit(); return jsonify({'result':serialize_match_result(m)})

@app.get('/api/notifications')
@login_required
def notifications():
    items=Notification.query.filter_by(user_id=current_user().id).order_by(Notification.created_at.desc()).limit(100).all()
    return jsonify([{'id':n.id,'title':n.title,'message':n.message,'notification_type':n.notification_type,'is_read':n.is_read,'created_at':n.created_at.isoformat()+'Z'} for n in items])

@app.patch('/api/notifications/<int:notification_id>/read')
@login_required
def read_notification(notification_id):
    n=Notification.query.filter_by(id=notification_id,user_id=current_user().id).first()
    if not n: return jsonify({'error':'Notification not found.'}),404
    n.is_read=True; db.session.commit(); return jsonify({'message':'Notification marked as read.'})

@app.get('/api/audit-logs')
@roles_required('OPO Administrator','System Administrator','Regulatory Auditor')
def audit_logs():
    q=AuditLog.query
    action=request.args.get('action','').strip()
    if action: q=q.filter(AuditLog.action.ilike(f'%{action}%'))
    items=q.order_by(AuditLog.created_at.desc()).limit(250).all()
    return jsonify([{'id':x.id,'user_id':x.user_id,'facility_id':x.facility_id,'action':x.action,'entity_type':x.entity_type,'entity_id':x.entity_id,'outcome':x.outcome,'details':x.details,'created_at':x.created_at.isoformat()+'Z'} for x in items])

@app.get('/api/dashboard/summary')
@login_required
def dashboard_summary():
    active_donors=Donor.query.filter_by(active=True).count()
    available=Donor.query.filter_by(active=True,availability_status='Available').count()
    active_recipients=Recipient.query.filter_by(waitlist_status='Active').count()
    pending=MatchResult.query.filter_by(review_status='Pending').count()
    runs=MatchRun.query.order_by(MatchRun.created_at.desc()).limit(5).all()
    recent=[{'id':r.id,'run_code':r.run_code,'donor_code':db.session.get(Donor,r.donor_id).donor_code if db.session.get(Donor,r.donor_id) else '—','eligible_candidates_count':r.eligible_candidates_count,'created_at':r.created_at.isoformat()+'Z'} for r in runs]
    return jsonify({'active_donors':active_donors,'available_organs':available,'active_recipients':active_recipients,'pending_reviews':pending,'recent_runs':recent,'unread_notifications':Notification.query.filter_by(user_id=current_user().id,is_read=False).count()})

@app.errorhandler(IntegrityError)
def integrity_error(error):
    db.session.rollback()
    return jsonify({'error':'The operation could not be saved because it conflicts with existing data. Check unique IDs and required relationships.'}),409

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'): return jsonify({'error':'API endpoint or record not found.'}),404
    return error

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error':'An unexpected server error occurred. Check the backend terminal for details.'}),500


def seed_demo_data():
    if Facility.query.first(): return
    facility=Facility(name='Harbourview Transplant Centre',code='HVT-MUM-01',facility_type='Transplant Centre',region='Mumbai')
    facility2=Facility(name='Western Medical Institute',code='WMI-MUM-02',facility_type='Hospital',region='Mumbai')
    db.session.add_all([facility,facility2]); db.session.flush()
    admin=User(full_name='Alex Morgan',email='admin@odms.local',password_hash=bcrypt.generate_password_hash('Demo@12345').decode(),role='System Administrator',facility_id=facility.id)
    coordinator=User(full_name='Sam Taylor',email='coordinator@odms.local',password_hash=bcrypt.generate_password_hash('Demo@12345').decode(),role='Medical Coordinator',facility_id=facility.id)
    db.session.add_all([admin,coordinator]); db.session.flush()
    samples=[
      Donor(donor_code='DNR-1001',display_name='Demo Donor A',age=34,blood_group='O-',rh_factor='Negative',height_cm=172,weight_kg=68,organ_type='Kidney',medical_notes='Synthetic demonstration record',screening_status='In Review',availability_status='Available',facility_id=facility.id,created_by_user_id=coordinator.id),
      Donor(donor_code='DNR-1002',display_name='Demo Donor B',age=42,blood_group='A+',rh_factor='Positive',height_cm=165,weight_kg=61,organ_type='Liver',medical_notes='Synthetic demonstration record',screening_status='Pending',availability_status='Available',facility_id=facility.id,created_by_user_id=coordinator.id),
      Donor(donor_code='DNR-1003',display_name='Demo Donor C',age=29,blood_group='B+',rh_factor='Positive',organ_type='Kidney',medical_notes='Synthetic demonstration record',screening_status='Pending',availability_status='Unavailable',facility_id=facility2.id,created_by_user_id=coordinator.id),
    ]
    db.session.add_all(samples); db.session.flush()
    recipients=[
      Recipient(recipient_code='REC-2001',display_name='Demo Recipient A',age=41,blood_group='A+',rh_factor='Positive',required_organ='Kidney',urgency='Urgent',waiting_list_date=date.today()-timedelta(days=190),medical_notes='Synthetic demonstration record',waitlist_status='Active',facility_id=facility.id,created_by_user_id=coordinator.id),
      Recipient(recipient_code='REC-2002',display_name='Demo Recipient B',age=53,blood_group='AB+',rh_factor='Positive',required_organ='Kidney',urgency='Critical',waiting_list_date=date.today()-timedelta(days=80),medical_notes='Synthetic demonstration record',waitlist_status='Active',facility_id=facility2.id,created_by_user_id=coordinator.id),
      Recipient(recipient_code='REC-2003',display_name='Demo Recipient C',age=37,blood_group='B+',rh_factor='Positive',required_organ='Kidney',urgency='Routine',waiting_list_date=date.today()-timedelta(days=20),medical_notes='Synthetic demonstration record',waitlist_status='Active',facility_id=facility.id,created_by_user_id=coordinator.id),
      Recipient(recipient_code='REC-2004',display_name='Demo Recipient D',age=47,blood_group='O-',rh_factor='Negative',required_organ='Kidney',urgency='Critical',waiting_list_date=date.today()-timedelta(days=120),medical_notes='Synthetic demonstration record',waitlist_status='Inactive',facility_id=facility2.id,created_by_user_id=coordinator.id),
      Recipient(recipient_code='REC-2005',display_name='Demo Recipient E',age=32,blood_group='O+',rh_factor='Positive',required_organ='Liver',urgency='Routine',waiting_list_date=date.today()-timedelta(days=60),medical_notes='Synthetic demonstration record',waitlist_status='Active',facility_id=facility2.id,created_by_user_id=coordinator.id),
    ]
    db.session.add_all(recipients); db.session.flush()
    db.session.add(AuditLog(user_id=admin.id,facility_id=facility.id,action='DEMO_DATA_SEEDED',entity_type='System',details='Synthetic demo data initialized'))
    db.session.commit()

with app.app_context():
    db.create_all()
    if os.getenv('SEED_DEMO_DATA','true').lower() == 'true': seed_demo_data()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT','5000')), debug=os.getenv('FLASK_DEBUG','false').lower()=='true')
