import os
import tempfile
import pytest

os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['SEED_DEMO_DATA'] = 'false'
os.environ['SECRET_KEY'] = 'test-secret'
from app import app, db, Facility, User, Donor, Recipient, bcrypt

@pytest.fixture()
def client():
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', SECRET_KEY='test-secret')
    with app.app_context():
        db.drop_all(); db.create_all()
        f=Facility(name='Test Facility', code='TEST-01'); db.session.add(f); db.session.flush()
        u=User(full_name='Test Admin',email='admin@test.local',password_hash=bcrypt.generate_password_hash('Demo@12345').decode(),role='System Administrator',facility_id=f.id)
        db.session.add(u); db.session.commit()
    with app.test_client() as c:
        yield c
    with app.app_context(): db.session.remove(); db.drop_all()

def login(client):
    return client.post('/api/auth/login', json={'email':'admin@test.local','password':'Demo@12345'})

def test_login_and_invalid_password(client):
    assert login(client).status_code == 200
    c=app.test_client()
    assert c.post('/api/auth/login',json={'email':'admin@test.local','password':'wrong'}).status_code == 401

def test_donor_recipient_and_matching(client):
    assert login(client).status_code == 200
    donor=client.post('/api/donors',json={'donor_code':'D-1','display_name':'Synthetic donor','age':32,'blood_group':'O-','organ_type':'Kidney','facility_id':1,'availability_status':'Available'})
    assert donor.status_code == 201, donor.get_json()
    recipient=client.post('/api/recipients',json={'recipient_code':'R-1','display_name':'Synthetic recipient','age':40,'blood_group':'A+','required_organ':'Kidney','facility_id':1,'urgency':'Urgent','waiting_list_date':'2025-01-01','waitlist_status':'Active'})
    assert recipient.status_code == 201, recipient.get_json()
    result=client.post('/api/matches/run',json={'donor_id':donor.get_json()['donor']['id']})
    assert result.status_code == 201, result.get_json()
    assert len(result.get_json()['results']) == 1
    assert client.get('/api/matches/runs').status_code == 200

def test_duplicate_donor_rejected(client):
    login(client)
    payload={'donor_code':'D-1','display_name':'Synthetic donor','age':32,'blood_group':'O-','organ_type':'Kidney','facility_id':1}
    assert client.post('/api/donors',json=payload).status_code == 201
    assert client.post('/api/donors',json=payload).status_code == 409

def test_unauthorized_donor_api(client):
    assert client.get('/api/donors').status_code == 401
