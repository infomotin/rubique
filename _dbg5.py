import uuid
from app import create_app
from models.db import init_database, query_all
from models.user_model import UserModel
from models import classic_arena as A
from models.card_club import economy
app=create_app(); app.config['TESTING']=True; app.config['SECRET_KEY']='t'
app.app_context().push(); init_database()
run=uuid.uuid4().hex[:6]
u=UserModel.create_user(f'w_{run}', f'w_{run}@t.co','password123','1995-04-12')
economy.replenish_wallet(u, 300)
b0=economy.balances_view(u)['personal']
g=A.create_game(u,'hearts',mode='ai',stake=30)
b1=economy.balances_view(u)['personal']
seats=A.game_seats(g['id'])
bots=[int(s['user_id']) for s in seats if s['user_id']!=u]
bb0={b: economy.balances_view(b)['personal'] for b in bots}
rows=query_all("SELECT id, owner_key, amount, balance_after, entry_type, ref_type, ref_id, note FROM club_ledger WHERE ref_type='classic_game' AND ref_id=%s","SELECT id, owner_key, amount, balance_after, entry_type, ref_type, ref_id, note FROM club_ledger WHERE ref_type='classic_game' AND ref_id=?",(g['id'],))
print('ledger for game', g['id'], flush=True)
for r in rows: print(dict(r) if isinstance(r,dict) else r, flush=True)
v=A.view_for(g['id'], u)
while not v.get('over') and v['legal_actions']:
    v,s=A.apply_action(g['id'], u, v['legal_actions'][0])
print('settle', s, flush=True)
rows=query_all("SELECT id, owner_key, amount, balance_after, entry_type, ref_type, ref_id, note FROM club_ledger WHERE ref_type='classic_game' AND ref_id=%s","SELECT id, owner_key, amount, balance_after, entry_type, ref_type, ref_id, note FROM club_ledger WHERE ref_type='classic_game' AND ref_id=?",(g['id'],))
for r in rows: print(dict(r) if isinstance(r,dict) else r, flush=True)
print('owner', b0, b1, economy.balances_view(u)['personal'], flush=True)
print('bots', bb0, {b: economy.balances_view(b)['personal'] for b in bots}, flush=True)
