import uuid, traceback
from app import create_app
from models.db import init_database
from models.user_model import UserModel
from models import classic_arena as A
from models.card_club import economy, groups as G, bots

app = create_app(); app.config['TESTING']=True; app.config['SECRET_KEY']='x'
app.app_context().push(); init_database()
run = uuid.uuid4().hex[:6]
def log(*a): print(*a, flush=True)

u = UserModel.create_user(f'staker_{run}', f'staker_{run}@t.co', 'password123', '1995-04-12')
economy.replenish_wallet(u, 300)
log('start bal', economy.balances_view(u)['personal'])

try:
    g = A.create_game(u, 'hearts', mode='ai', stake=25)
    log('stake bal after create', economy.balances_view(u)['personal'],
        'stakes', economy.classic_stakes(g['id']))
    v = A.view_for(g['id'], u)
    n=0; s=None
    while not v.get('over') and n < 900:
        if not v['legal_actions']: log('stuck', v['phase']); break
        v, s = A.apply_action(g['id'], u, v['legal_actions'][0]); n+=1
    log('over', v['over'], 'moves', n, 'settle', s)
    log('end bal', economy.balances_view(u)['personal'])
except Exception:
    traceback.print_exc()

# group mode with two humans
try:
    g2 = A.create_game(u, 'spades', mode='group', group_id=0, stake=0)
    log('group status', g2['status'])
    u2 = UserModel.create_user(f'staker2_{run}', f'staker2_{run}@t.co', 'password123', '1995-04-12')
    idx = A.join_game(u2, g2['id'])
    log('joined at seat', idx)
    g2 = A.start_game(u, g2['id'])
    log('started', g2['status'])
    v1 = A.view_for(g2['id'], u); v2 = A.view_for(g2['id'], u2)
    log('humans', v1['human_seats'], 'my_seat', v1['my_seat'], v2['my_seat'])
    # both players keep acting until one is on move / done
    for k in range(6):
        if v1.get('over'): break
        if v1['is_my_turn']:
            v1, s = A.apply_action(g2['id'], u, v1['legal_actions'][0])
        elif v2['is_my_turn']:
            v2, s = A.apply_action(g2['id'], u2, v2['legal_actions'][0])
        else:
            log('nobody to move', v1['phase'], v1['turn'], v1['bid_turn'], v1['is_my_turn'], v2['is_my_turn']); break
        v1 = A.view_for(g2['id'], u); v2 = A.view_for(g2['id'], u2)
        log('step', k, 'phase', v1['phase'], 'my1', v1['is_my_turn'], 'my2', v2['is_my_turn'])
except Exception:
    traceback.print_exc()
log('ledger', economy.verify_ledger())
