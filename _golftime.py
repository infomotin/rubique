import time, uuid, sys
from app import create_app
from models.db import init_database
from models.user_model import UserModel
from models.card_club import bots, groups, gameplay
from models.card_club.engines import CATALOG

def log(*a): print(*a, flush=True)
app = create_app(); app.config['TESTING']=True; app.config['SECRET_KEY']='x'
app.app_context().push(); init_database()
run = uuid.uuid4().hex[:8]
uid = UserModel.create_user(f'h{run}', f'h{run}@t.co', 'password123', '1995-04-12')
gid = groups.create_group(uid, f'G {run}')['id']
t = gameplay.create_table(gid, uid, 'golf', stake=0, max_seats=4, mode='vs_com')
tid = int(t['id'])
gameplay.start_table(gid, uid, tid)
gameplay.acknowledge_strict_rules(tid, uid)
log('started', tid)

def pick(state, seat, legal):
    a = bots.choose_action(state, seat, legal)
    return a if a in legal else bots._ranked(state, seat, legal)[0]
t0=time.time()
for i in range(600):
    tt = gameplay.get_table(tid)
    if tt['status'] != 'active':
        log('ended at', i, tt['status'], 'in', round(time.time()-t0,2)); break
    seat = gameplay.seat_index_of(tid, uid)
    info, eng = gameplay._engine_for(tt)
    actor = bots.current_actor(eng.state)
    if actor != seat:
        m,_ = gameplay.step_pending_bots(tid)
        if not m:
            log('STALL at', i, 'actor', actor, 'hole', eng.state.get('hole'), 'moves', eng.state.get('moves')); break
        continue
    legal = eng.legal_actions(seat)
    if not legal:
        m,_ = gameplay.step_pending_bots(tid)
        if not m:
            log('STALL no legal at', i, 'hole', eng.state.get('hole')); break
        continue
    if i % 50 == 0: log('iter', i, 'hole', eng.state.get('hole'), 'stocks', eng.state.get('stocks'), 'moves', eng.state.get('moves'))
    gameplay.perform_move(gid, uid, tid, pick(eng.state, seat, legal))
else:
    log('CAP hit', round(time.time()-t0,2))
log('total', round(time.time()-t0,2))
