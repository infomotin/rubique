import json, uuid, traceback
from app import create_app
from models.db import init_database
from models.user_model import UserModel
from models import classic_arena as A
from models.card_club import economy

def log(*a): print(*a, flush=True)

app = create_app(); app.config['TESTING']=True; app.config['SECRET_KEY']='x'
app.app_context().push(); init_database()
run = uuid.uuid4().hex[:6]
u = UserModel.create_user(f'classic_{run}', f'classic_{run}@t.co', 'password123', '1995-04-12')
log('user', u, 'bal', economy.balances_view(u)['personal'])

try:
    g = A.create_game(u, '29', mode='ai', stake=0)
    log('created', g['id'], g['status'], g['slug'])
    seats = A.game_seats(g['id'])
    log('seats', [(s['seat_index'], s['is_bot'], s['display_name']) for s in seats])
    v = A.view_for(g['id'], u)
    log('view keys', sorted(v.keys())[:8], 'legal', len(v['legal_actions']), 'labels', v['seat_labels'])

    # illegal move
    st = json.loads(A.get_game(g['id'])['state'])
    hand = st['hands']['0']
    phase = st['phase']; log('phase', phase, 'turn', st.get('turn'), 'bid_turn', st.get('bid_turn'))
    if phase == 'bidding':
        try:
            A.apply_action(g['id'], u, {"action":"bid","value":5})
            log('BAD: illegal bid accepted')
        except Exception as e:
            log('illegal bid rejected:', type(e).__name__, e)

    # legal play
    v, s = A.apply_action(g['id'], u, v['legal_actions'][0])
    log('move ok; over=', v['over'], 'phase', v['phase'], 'my_turn', v['is_my_turn'])
except Exception:
    traceback.print_exc()

# full game to completion
try:
    g2 = A.create_game(u, 'spades', mode='ai', stake=0)
    v = A.view_for(g2['id'], u)
    n = 0
    while n < 800:
        if v.get('over'): break
        if not v['legal_actions']:
            log('stuck', v['phase'], v['turn'], v['bid_turn']); break
        v, s = A.apply_action(g2['id'], u, v['legal_actions'][0])
        n += 1
    log('spades finished?', v['over'], 'moves', n, 'settle', s)
    log('status', A.get_game(g2['id'])['status'])
except Exception:
    traceback.print_exc()
log('ledger', economy.verify_ledger())
