import uuid, json
from app import create_app
from models.db import init_database, query_one
app=create_app(); app.config['TESTING']=True; app.config['SECRET_KEY']='t'
c=app.test_client(); app.app_context().push(); init_database()
n='dbg_'+uuid.uuid4().hex[:6]
r=c.post('/register', data={'username':n,'email':f'{n}@t.co','password':'password123','confirm_password':'password123','date_of_birth':'1995-04-12','device_fp':'d1'})
print('status', r.status_code, r.headers.get('Location'), flush=True)
print(r.data[:400], flush=True)
print('row', query_one("SELECT id, username FROM users WHERE username=%s","SELECT id, username FROM users WHERE username=?",(n,)), flush=True)
r=c.post('/login', data={'username':n,'password':'password123'})
print('login', r.status_code, r.headers.get('Location'), flush=True)
