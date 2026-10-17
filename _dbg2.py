import uuid, json
from app import create_app
from models.db import init_database, query_one
app=create_app(); app.config['TESTING']=True; app.config['SECRET_KEY']='t'
c=app.test_client(); app.app_context().push(); init_database()
run=uuid.uuid4().hex[:6]
def reg(n):
    r=c.post('/register', data={'username':n,'email':f'{n}@t.co','password':'password123','confirm_password':'password123','date_of_birth':'1995-04-12','device_fp':'d-'+n})
    print('reg',n,r.status_code,r.headers.get('Location'), flush=True)
def login(n):
    r=c.post('/login', data={'username':n,'password':'password123'})
    print('login',n,r.status_code,r.headers.get('Location'), flush=True)
a=f'a_{run}'; b=f'b_{run}'
reg(a); login(a)
r=c.post('/cards/classic/new-game', json={'slug':'hearts','mode':'ai'})
print('new', r.status_code, json.loads(r.data).get('game_id'), flush=True)
gid=json.loads(r.data)['game_id']
reg(b); login(b)
r=c.post('/cards/classic/action', json={'game_id':gid,'action':'bid','value':20})
print('stranger action', r.status_code, r.data[:200], flush=True)
r=c.get(f'/cards/classic/state?game_id={gid}')
print('stranger state', r.status_code, r.data[:200], flush=True)
