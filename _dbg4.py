import uuid, json
from app import create_app
from models.db import init_database
from models.user_model import UserModel
from models import classic_arena as A
from models.card_club import economy
app=create_app(); app.config['TESTING']=True; app.config['SECRET_KEY']='t'
app.app_context().push(); init_database()
run=uuid.uuid4().hex[:6]
def log(*a): print(*a, flush=True)
u=UserModel.create_user(f'z_{run}', f'z_{run}@t.co','password123','1995-04-12')
economy.replenish_wallet(u, 300)
g=A.create_game(u,'oh_hell',mode='ai',stake=30)
seats=A.game_seats(g['id'])
before={int(s['user_id']): economy.balances_view(int(s['user_id']))['personal'] for s in seats}
log('before', before, 'sum', sum(before.values()))
v=A.view_for(g['id'], u)
while not v.get('over') and v['legal_actions']:
    v, s = A.apply_action(g['id'], u, v['legal_actions'][0])
log('settle', s)
after={uid: economy.balances_view(uid)['personal'] for uid in before}
log('after', after, 'sum', sum(after.values()))
log('stakes', economy.classic_stakes(g['id']))
log('ledger', economy.verify_ledger())
