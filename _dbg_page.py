import re, uuid, json, subprocess, os
from app import create_app
from models.db import init_database
app=create_app(); app.config['TESTING']=True; app.config['SECRET_KEY']='t'
c=app.test_client(); app.app_context().push(); init_database()
n='pg_'+uuid.uuid4().hex[:6]
c.post('/register', data={'username':n,'email':f'{n}@t.co','password':'password123','confirm_password':'password123','date_of_birth':'1995-04-12','device_fp':'fp-'+n})
c.post('/login', data={'username':n,'password':'password123'})
r=c.get('/cards/classic')
print('page', r.status_code, len(r.data), flush=True)
html=r.data.decode('utf-8','replace')
for token in ['name-south','classic-lobby-modal','MY_USER_ID','restoreState','active_game_id']:
    print(token, token in html, flush=True)
if r.status_code!=200: print(html[:1500], flush=True)
# extract the last script block and syntax check with node
m=re.search(r'<script>(.*?)</script>\s*{% endblock %}', html, re.S)
print('script found', bool(m), flush=True)
if m:
    js=m.group(1)
    js=js.replace('const MY_USER_ID = 0;','const MY_USER_ID = 0;').replace('const DEFAULT_GROUP = 0;','const DEFAULT_GROUP = 0;').replace('const RESTORE_GAME_ID = null;','const RESTORE_GAME_ID = null;')
    open(os.path.join(os.environ.get('TEMP','.'),'classic_check.js'),'w',encoding='utf-8').write(js)
    try:
        out=subprocess.run(['node','--check',os.path.join(os.environ.get('TEMP','.'),'classic_check.js')],capture_output=True,text=True)
        print('node rc', out.returncode, out.stderr[:800], flush=True)
    except FileNotFoundError:
        print('node missing', flush=True)
