/* Card Club client: HTTP API helpers, group forms, live table play.
 * Transport strategy: Socket.IO websocket push when available, automatic
 * fallback to 2.5s state polling - the game stays fully playable either way
 * because every move also has an HTTP endpoint. */

const ClubSection = (() => {

    function toast(msg, ok = true) {
        const el = document.getElementById('club-toast');
        if (!el) { alert(msg); return; }
        el.textContent = msg;
        el.className = 'fixed bottom-5 right-5 z-50 px-4 py-3 rounded-xl font-mono text-xs font-bold shadow-2xl border ' +
            (ok ? 'bg-emerald-950 border-emerald-500/50 text-emerald-200'
                : 'bg-rose-950 border-rose-500/50 text-rose-200');
        el.classList.remove('hidden');
        clearTimeout(el._t);
        el._t = setTimeout(() => el.classList.add('hidden'), 3500);
    }

    async function post(url, body = {}) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Card-Club': '1' },
            credentials: 'same-origin',
            body: JSON.stringify(body)
        });
        let data = null;
        try { data = await res.json(); } catch (e) { /* no body */ }
        if (!res.ok || (data && data.ok === false)) {
            const msg = (data && data.error) || ('Request failed (' + res.status + ')');
            if (data && data.age_gate) { window.location.href = '/club/age-gate'; return null; }
            throw new Error(msg);
        }
        return data;
    }

    function collect(form) {
        const out = {};
        new FormData(form).forEach((v, k) => { out[k] = v; });
        return out;
    }

    function wire(globalLedger = false) {
        document.querySelectorAll('form[data-club-action]').forEach(form => {
            form.addEventListener('submit', async (ev) => {
                ev.preventDefault();
                const btn = form.querySelector('button[type="submit"], button:not([type])');
                try {
                    if (btn) btn.disabled = true;
                    const data = await post(form.dataset.clubAction, collect(form));
                    if (data) {
                        toast(data.error || 'Done', !data.error);
                        setTimeout(() => window.location.reload(), 600);
                    }
                } catch (e) {
                    toast(e.message, false);
                    if (btn) btn.disabled = false;
                }
            });
        });

        document.querySelectorAll('[data-club-post]').forEach(btn => {
            btn.addEventListener('click', async () => {
                const confirmMsg = btn.dataset.confirm;
                if (confirmMsg && !window.confirm(confirmMsg)) return;
                let body = {};
                try { body = JSON.parse(btn.dataset.clubBody || '{}'); } catch (e) {}
                try {
                    btn.disabled = true;
                    const data = await post(btn.dataset.clubPost, body);
                    if (data) {
                        toast('Done', true);
                        setTimeout(() => window.location.reload(), 600);
                    }
                } catch (e) {
                    toast(e.message, false);
                    btn.disabled = false;
                }
            });
        });

        const verifyBtn = document.getElementById('club-verify-btn');
        if (verifyBtn) {
            verifyBtn.addEventListener('click', async () => {
                try {
                    verifyBtn.disabled = true;
                    const res = await fetch('/club/api/ledger/verify',
                        { headers: { 'X-Card-Club': '1' }, credentials: 'same-origin' });
                    const data = await res.json();
                    if (data.ok === false) throw new Error(data.error || 'Verify failed');
                    toast('Ledger ' + (data.report.ok ? 'VERIFIED' : 'VIOLATIONS FOUND'),
                          data.report.ok);
                    setTimeout(() => window.location.reload(), 900);
                } catch (e) {
                    toast(e.message, false);
                    verifyBtn.disabled = false;
                }
            });
        }
    }

    return {
        init(globalLedger = false) { wire(globalLedger); },
        toast, post
    };
})();


const ClubTable = (() => {
    let view = null;
    let socket = null;
    let pollTimer = null;
    let live = false;

    const C = () => window.CLUB;

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function cardChip(c) {
        const red = /^([HD])/.test(String(c));
        return `<span class="inline-block px-2 py-1 mr-1 mb-1 rounded-lg border font-mono text-[11px] font-bold ${red
            ? 'bg-rose-950/80 border-rose-500/40 text-rose-200'
            : 'bg-slate-900 border-slate-600 text-slate-100'}">${esc(c)}</span>`;
    }

    function actionLabel(a) {
        if (!a || typeof a !== 'object') return JSON.stringify(a);
        const bits = [String(a.action || '?').replace(/_/g, ' ')];
        ['card', 'cards', 'suit', 'value', 'pile', 'rank', 'target'].forEach(k => {
            if (a[k] !== undefined && a[k] !== null) {
                bits.push(Array.isArray(a[k]) ? a[k].join(',') : String(a[k]));
            }
        });
        return bits.join(' · ');
    }

    function render(v) {
        view = v;
        const t = v.table || {};
        const g = v.game || {};
        const mySeat = v.seat;

        // seats strip
        const seatsEl = document.getElementById('club-seats');
        if (seatsEl) {
            const turn = (t.status === 'active') ? g.turn : null;
            const finish = v.finish || [];
            seatsEl.innerHTML = (v.seats || []).map(s => {
                const isMe = s.seat_index === mySeat;
                const isTurn = s.seat_index === turn;
                const pos = finish.indexOf(s.seat_index);
                return `<span class="px-3 py-1.5 rounded-xl border font-bold
                    ${isMe ? 'bg-indigo-950 border-indigo-400/50 text-indigo-200'
                           : 'bg-slate-900 border-slate-700 text-slate-300'}
                    ${isTurn ? 'ring-2 ring-amber-400/70 animate-pulse' : ''}">
                    ${esc(s.username)} <span class="text-[9px] opacity-60">#${s.seat_index}</span>
                    ${pos >= 0 ? `<span class="ml-1 text-[9px] text-emerald-300">#${pos + 1}</span>` : ''}
                </span>`;
            }).join('') || '<span class="text-slate-600">No seats yet</span>';
            if (turn !== null && turn !== undefined) {
                const me = (v.seats || []).find(s => s.seat_index === mySeat);
                const whose = (v.seats || []).find(s => s.seat_index === turn);
                const hint = document.getElementById('club-turn-hint');
                if (hint) {
                    hint.textContent = (mySeat === turn) ? 'YOUR TURN' :
                        'waiting for ' + (whose ? whose.username : '#' + turn);
                    hint.className = 'text-[10px] font-mono ' +
                        (mySeat === turn ? 'text-amber-300 font-bold' : 'text-slate-500');
                }
            }
        }

        const potEl = document.getElementById('club-pot');
        if (potEl) potEl.textContent = v.pot != null ? v.pot : 0;
        const chip = document.getElementById('club-status-chip');
        if (chip) chip.textContent = t.status || '';

        renderControls(v);
        renderGame(v);
        renderLegal(v);
    }

    function renderControls(v) {
        const el = document.getElementById('club-controls');
        if (!el) return;
        const t = v.table || {};
        const seated = v.seat !== null && v.seat !== undefined;
        const btns = [];
        if (t.status === 'waiting') {
            if (!seated) btns.push(`<button class="club-ctrl px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold" data-url="${C().joinUrl}"><i class="fa-solid fa-chair mr-1.5"></i>Join Table</button>`);
            else {
                btns.push(`<button class="club-ctrl px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-xs font-bold" data-url="${C().leaveUrl}"><i class="fa-solid fa-door-open mr-1.5"></i>Leave</button>`);
                btns.push(`<button class="club-ctrl px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold" data-url="${C().startUrl}"><i class="fa-solid fa-play mr-1.5"></i>Start (${(v.seats || []).length}/${v.max_players || '?'} needed: ${v.min_players || '?'})</button>`);
            }
            btns.push(`<button class="club-ctrl px-3 py-2 rounded-xl bg-rose-900/60 hover:bg-rose-800 text-rose-200 text-xs font-bold" data-url="${C().abandonUrl}">Cancel Table</button>`);
        } else if (t.status === 'active') {
            if (!seated) btns.push(`<span class="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 text-xs font-mono">spectating</span>`);
            btns.push(`<button class="club-ctrl px-3 py-2 rounded-xl bg-rose-900/60 hover:bg-rose-800 text-rose-200 text-xs font-bold" data-url="${C().abandonUrl}" data-confirm="Abandon the table in play? All escrowed stakes are refunded.">Abandon</button>`);
        } else {
            btns.push(`<span class="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 text-xs font-mono">table ${esc(t.status)}</span>`);
        }
        el.innerHTML = btns.join('');
        el.querySelectorAll('.club-ctrl').forEach(b => {
            b.addEventListener('click', async () => {
                if (b.dataset.confirm && !window.confirm(b.dataset.confirm)) return;
                b.disabled = true;
                try {
                    await ClubSection.post(b.dataset.url, {});
                } catch (e) { ClubSection.toast(e.message, false); }
                b.disabled = false;
                refresh();
            });
        });
    }

    function renderGame(v) {
        const el = document.getElementById('club-game');
        if (!el) return;
        const t = v.table || {};
        const g = v.game || {};

        if (t.status === 'waiting') {
            el.innerHTML = `
                <div class="text-center py-8">
                    <i class="fa-solid fa-hourglass-half text-3xl text-amber-400 mb-3 block"></i>
                    <div class="text-sm font-bold text-white">Waiting for players</div>
                    <div class="text-xs text-slate-400 font-mono mt-1">
                        ${esc(v.game_name || '')} needs ${v.min_players || '?'}-${v.max_players || '?'} players
                        &bull; ${(v.seats || []).length} seated
                    </div>
                    <div class="text-[11px] text-slate-500 font-mono mt-3 max-w-lg mx-auto leading-relaxed">${esc(v.rules || '')}</div>
                </div>`;
            return;
        }
        if (t.status !== 'active') {
            el.innerHTML = `<div class="text-center py-8 text-slate-500 font-mono text-xs">Table closed (${esc(t.status)}).</div>`;
            return;
        }

        const panels = [];

        if (g.hand && Array.isArray(g.hand)) {
            panels.push(`<div>
                <div class="text-[10px] font-mono text-slate-500 uppercase mb-1.5">Your hand (${g.hand.length})</div>
                <div>${g.hand.map(cardChip).join('')}</div>
            </div>`);
        }

        const centerKeys = ['top', 'center', 'pile', 'discard', 'stock', 'stock_count',
            'draw_count', 'pending_draw', 'revealed', 'market', 'table_cards', 'face_up',
            'show', 'spoons', 'spoon_count', 'trick', 'trump', 'current', 'captures'];
        const center = centerKeys.filter(k => g[k] !== undefined && g[k] !== null);
        if (center.length) {
            panels.push(`<div>
                <div class="text-[10px] font-mono text-slate-500 uppercase mb-1.5">Table</div>
                <div class="p-3 rounded-xl bg-black/50 border border-slate-800 font-mono text-xs text-slate-200 flex flex-wrap gap-1">
                ${center.map(k => {
                    const val = g[k];
                    if (Array.isArray(val)) {
                        return `<span class="text-slate-500 mr-1">${esc(k)}:</span>` +
                            (val.every(x => typeof x === 'string' && x.length <= 4)
                                ? val.map(cardChip).join('')
                                : esc(JSON.stringify(val)));
                    }
                    if (typeof val === 'object') {
                        return `<span class="text-slate-500 mr-1">${esc(k)}:</span>${esc(JSON.stringify(val))}`;
                    }
                    return `<span class="text-slate-500 mr-1">${esc(k)}:</span><strong class="text-amber-300">${esc(val)}</strong>`;
                }).join('')}
                </div>
            </div>`);
        }

        if (g.counts) {
            panels.push(`<div>
                <div class="text-[10px] font-mono text-slate-500 uppercase mb-1.5">Card counts</div>
                <div class="flex flex-wrap gap-2">
                ${Object.entries(g.counts).map(([seat, n]) => {
                    const who = (v.seats || []).find(s => s.seat_index == seat);
                    const mine = seat == v.seat;
                    return `<span class="px-2.5 py-1 rounded-lg border text-[11px] font-mono ${mine
                        ? 'bg-indigo-950 border-indigo-400/40 text-indigo-200'
                        : 'bg-slate-900 border-slate-700 text-slate-300'}">
                        ${esc(who ? who.username : '#' + seat)}: <strong>${esc(n)}</strong></span>`;
                }).join('')}
                </div>
            </div>`);
        }

        if (g.scores && Object.keys(g.scores).length) {
            panels.push(`<div>
                <div class="text-[10px] font-mono text-slate-500 uppercase mb-1.5">Scores</div>
                <div class="flex flex-wrap gap-2 font-mono text-[11px]">
                ${Object.entries(g.scores).map(([seat, sc]) => {
                    const who = (v.seats || []).find(s => s.seat_index == seat);
                    return `<span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-slate-200">
                        ${esc(who ? who.username : '#' + seat)}: <strong class="text-cyan-300">${esc(sc)}</strong></span>`;
                }).join('')}
                </div>
            </div>`);
        }

        if (g.log && g.log.length) {
            panels.push(`<div>
                <div class="text-[10px] font-mono text-slate-500 uppercase mb-1.5">Log</div>
                <div class="max-h-36 overflow-y-auto space-y-0.5 text-[11px] font-mono text-slate-400">
                ${g.log.slice().reverse().map(l => {
                    const who = (v.seats || []).find(s => s.seat_index == l.seat);
                    return `<div><span class="text-slate-600">${esc(who ? who.username : '#' + l.seat)}</span> ${esc(l.text)}</div>`;
                }).join('')}
                </div>
            </div>`);
        }

        const known = new Set(['slug', 'players', 'turn', 'dir', 'finish', 'over', 'log',
            'counts', 'hand', 'scores', 'status', 'min_players', 'max_players', 'rules', ...centerKeys]);
        const rest = Object.keys(g).filter(k => !known.has(k));
        if (rest.length) {
            panels.push(`<details class="text-[11px] font-mono">
                <summary class="text-slate-500 cursor-pointer hover:text-slate-300">Raw game state (${rest.length} more keys)</summary>
                <pre class="mt-2 p-3 rounded-xl bg-black/60 border border-slate-800 text-slate-400 overflow-x-auto text-[10px]">${esc(JSON.stringify(
                    rest.reduce((o, k) => (o[k] = g[k], o), {}), null, 1))}</pre>
            </details>`);
        }

        if (g.over) {
            panels.unshift(`<div class="px-4 py-3 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-200 font-mono text-xs font-bold text-center">
                <i class="fa-solid fa-trophy mr-1.5"></i> Game over - settlement processed
            </div>`);
        }

        el.innerHTML = panels.join('') || '<div class="text-slate-600 font-mono text-xs">Waiting for state&hellip;</div>';
    }

    function renderLegal(v) {
        const el = document.getElementById('club-legal');
        if (!el) return;
        const legal = Array.isArray(v.legal) ? v.legal : [];
        if (v.seat === null || v.seat === undefined || v.table.status !== 'active') {
            el.innerHTML = '<span class="text-slate-600 text-xs font-mono">Not seated at this table.</span>';
            return;
        }
        if (!legal.length) {
            el.innerHTML = '<span class="text-slate-500 text-xs font-mono">No legal moves right now (waiting for other players or the game is over).</span>';
            return;
        }
        el.innerHTML = legal.map((a, i) =>
            `<button class="club-move px-3 py-2 rounded-xl bg-slate-800 hover:bg-indigo-600 border border-slate-700 hover:border-indigo-400 text-white text-[11px] font-mono font-bold transition-all" data-i="${i}">${esc(actionLabel(a))}</button>`
        ).join('');
        el.querySelectorAll('.club-move').forEach(b => {
            b.addEventListener('click', () => sendMove(legal[parseInt(b.dataset.i, 10)]));
        });
    }

    function showErr(msg) {
        const el = document.getElementById('club-error');
        if (!el) return;
        if (!msg) { el.classList.add('hidden'); return; }
        el.textContent = msg;
        el.classList.remove('hidden');
    }

    async function sendMove(action) {
        showErr(null);
        try {
            if (socket && socket.connected) {
                const ack = await new Promise((resolve) => {
                    socket.timeout(5000).emit('table_move',
                        { table_id: C().tableId, action },
                        (err, res) => resolve(err ? { ok: false, error: 'no reply' } : res));
                });
                if (ack && ack.ok) {
                    if (ack.state) render(ack.state);
                    if (ack.settlement) showSettlement(ack.settlement);
                } else {
                    showErr((ack && ack.error) || 'Move rejected');
                }
                return;
            }
            const data = await ClubSection.post(C().moveUrl, { action });
            if (data) {
                if (data.view) render(data.view);
                if (data.settlement) showSettlement(data.settlement);
            }
        } catch (e) {
            showErr(e.message);
        }
    }

    function showSettlement(s) {
        const el = document.getElementById('club-settlement');
        if (!el || !s) return;
        el.innerHTML = `<i class="fa-solid fa-coins mr-2"></i>Settled: pot ${s.pot}` +
            (s.pool_bonus ? ` + pool bonus ${s.pool_bonus}` : '') +
            ` = <strong>${s.total}</strong> coins paid out (zero-sum).`;
        el.classList.remove('hidden');
        ClubSection.toast('Table settled', true);
        setTimeout(() => window.location.reload(), 3000);
    }

    async function refresh() {
        try {
            const res = await fetch(C().stateUrl,
                { headers: { 'X-Card-Club': '1' }, credentials: 'same-origin' });
            const data = await res.json();
            if (data && data.ok && data.state) render(data.state);
        } catch (e) { /* transient */ }
    }

    function startPolling() {
        if (pollTimer) return;
        pollTimer = setInterval(() => {
            if (document.visibilityState === 'visible' && !live) refresh();
        }, 2500);
    }

    function stopPolling() {
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    }

    function initSocket() {
        const conn = document.getElementById('club-conn');
        if (typeof window.io !== 'function') {
            if (conn) { conn.textContent = 'polling mode'; conn.className = 'px-2 py-0.5 rounded bg-amber-950 border border-amber-500/40 text-amber-300 text-[10px] font-mono'; }
            startPolling();
            return;
        }
        try {
            socket = window.io({ transports: ['websocket', 'polling'] });
        } catch (e) {
            startPolling();
            return;
        }
        socket.on('connect', () => {
            live = true;
            stopPolling();
            if (conn) { conn.textContent = 'live'; conn.className = 'px-2 py-0.5 rounded bg-emerald-950 border border-emerald-500/50 text-emerald-300 text-[10px] font-mono animate-pulse'; }
            socket.emit('watch_table', { table_id: C().tableId }, (ack) => {
                if (ack && ack.ok && ack.state) render(ack.state);
            });
        });
        socket.on('disconnect', () => {
            live = false;
            if (conn) { conn.textContent = 'polling mode'; conn.className = 'px-2 py-0.5 rounded bg-amber-950 border border-amber-500/40 text-amber-300 text-[10px] font-mono'; }
            startPolling();
        });
        socket.on('table_state', (v) => {
            if (v && v.table && v.table.id === C().tableId && v.seat !== null && v.seat !== undefined) render(v);
        });
        socket.on('table_spectate', (v) => {
            if (v && v.table && v.table.id === C().tableId &&
                (view === null || view.seat === null || view.seat === undefined)) render(v);
        });
        socket.on('table_settlement', (payload) => {
            if (payload && payload.table_id === C().tableId && payload.settlement) {
                showSettlement(payload.settlement);
            }
        });
    }

    return {
        init() {
            try {
                const raw = document.getElementById('club-view-json').textContent;
                view = JSON.parse(raw);
            } catch (e) { view = null; }
            if (view) render(view);
            const custom = document.getElementById('club-custom-send');
            if (custom) {
                custom.addEventListener('click', () => {
                    const ta = document.getElementById('club-custom-action');
                    try {
                        const action = JSON.parse(ta.value);
                        if (typeof action !== 'object') throw new Error('object required');
                        sendMove(action);
                    } catch (e) { showErr('Invalid JSON action: ' + e.message); }
                });
            }
            initSocket();
            if (!live) startPolling();
            const send = document.getElementById('club-custom-send');
            if (send) send.disabled = false;
        },
        render
    };
})();
