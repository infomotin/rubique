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
        if (window.ClubAudio) {
            if (ok) window.ClubAudio.success(); else window.ClubAudio.error();
        }
    }

    // ---------------------------------------------------------- confetti
    let confettiCanvas = null;
    let confettiParts = [];
    let confettiRaf = null;

    function confettiBurst(x, y, count = 70) {
        try {
            if (!confettiCanvas) {
                confettiCanvas = document.createElement('canvas');
                confettiCanvas.id = 'club-confetti';
                confettiCanvas.className = 'club-confetti-canvas';
                document.body.appendChild(confettiCanvas);
                const resize = () => {
                    confettiCanvas.width = window.innerWidth;
                    confettiCanvas.height = window.innerHeight;
                };
                resize();
                window.addEventListener('resize', resize);
            }
            const colors = ['#fbbf24', '#34d399', '#22d3ee', '#f43f5e', '#a78bfa', '#ffffff'];
            for (let i = 0; i < count; i++) {
                const ang = Math.random() * Math.PI * 2;
                const spd = 3 + Math.random() * 9;
                confettiParts.push({
                    x, y,
                    vx: Math.cos(ang) * spd,
                    vy: Math.sin(ang) * spd - 4,
                    w: 5 + Math.random() * 6,
                    h: 7 + Math.random() * 7,
                    rot: Math.random() * Math.PI * 2,
                    vr: (Math.random() - 0.5) * 0.4,
                    color: colors[(Math.random() * colors.length) | 0],
                    life: 1
                });
            }
            if (!confettiRaf) confettiLoop();
        } catch (e) { /* visual only */ }
    }

    function confettiLoop() {
        const ctx = confettiCanvas.getContext('2d');
        const step = () => {
            ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
            for (let i = confettiParts.length - 1; i >= 0; i--) {
                const p = confettiParts[i];
                p.vy += 0.28;              // gravity
                p.vx *= 0.99;              // drag
                p.x += p.vx;
                p.y += p.vy;
                p.rot += p.vr;
                p.life -= 0.008;
                if (p.life <= 0 || p.y > confettiCanvas.height + 40) {
                    confettiParts.splice(i, 1);
                    continue;
                }
                ctx.save();
                ctx.globalAlpha = Math.max(0, Math.min(1, p.life));
                ctx.translate(p.x, p.y);
                ctx.rotate(p.rot);
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
                ctx.restore();
            }
            if (confettiParts.length) {
                confettiRaf = requestAnimationFrame(step);
            } else {
                confettiRaf = null;
                ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
            }
        };
        confettiRaf = requestAnimationFrame(step);
    }

    // ------------------------------------------------------------ audio
    let audioArmed = false;

    function armAudio() {
        if (audioArmed) return;
        audioArmed = true;
        if (!window.ClubAudio) return;
        window.ClubAudio.unlock();
        // One welcome flourish per session, on the first real gesture
        try {
            if (!sessionStorage.getItem('club_welcomed')) {
                sessionStorage.setItem('club_welcomed', '1');
                setTimeout(() => {
                    window.ClubAudio.shuffle();
                    setTimeout(() => window.ClubAudio.dealFan(6), 750);
                }, 150);
            }
        } catch (e) { /* private mode */ }
    }

    function fx(name) {
        const A = window.ClubAudio;
        if (!A) return;
        switch (name) {
            case 'shuffle': A.shuffle(); break;
            case 'slap': {
                A.slap();
                const felt = document.querySelector('.casino-table-felt');
                if (felt) {
                    felt.classList.remove('table-slap-impact');
                    void felt.offsetWidth;
                    felt.classList.add('table-slap-impact');
                }
                break;
            }
            case 'throw': A.throw(); break;
            case 'deal': A.deal(); break;
            case 'flip': A.flip(); break;
            case 'chips': A.chips(); break;
            case 'coins': A.coins(); break;
            case 'win': A.win(); break;
            case 'success': A.success(); break;
            case 'welcome-deal':
                A.shuffle();
                setTimeout(() => A.dealFan(10), 620);
                setTimeout(() => A.coins(), 1700);
                break;
            default: A.hover();
        }
    }

    function wireSoundToggle() {
        const btn = document.getElementById('club-sound-toggle-btn');
        const icon = document.getElementById('club-sound-icon');
        const label = document.getElementById('club-sound-label');
        const slider = document.getElementById('club-volume-slider');
        if (btn && window.ClubAudio) {
            const paint = () => {
                const muted = window.ClubAudio.isMuted();
                if (icon) icon.className = muted
                    ? 'fa-solid fa-volume-xmark text-slate-500'
                    : 'fa-solid fa-volume-high text-amber-400';
                if (label) label.textContent = muted ? 'Audio Muted' : 'Audio ON';
                const viz = document.getElementById('hero-audio-viz');
                if (viz) viz.classList.toggle('is-audio-playing', !muted);
            };
            paint();
            btn.addEventListener('click', () => {
                audioArmed = true;
                window.ClubAudio.unlock();
                window.ClubAudio.toggleMute();
                paint();
                if (!window.ClubAudio.isMuted()) window.ClubAudio.hover();
            });
        }
        if (slider && window.ClubAudio) {
            slider.value = window.ClubAudio.getVolume();
            slider.addEventListener('input', (e) => {
                window.ClubAudio.setVolume(parseFloat(e.target.value));
            });
        }
    }

    function revealInit() {
        const items = document.querySelectorAll('.reveal');
        if (!('IntersectionObserver' in window)) {
            items.forEach(el => el.classList.add('revealed'));
            return;
        }
        const io = new IntersectionObserver((entries) => {
            entries.forEach(en => {
                if (en.isIntersecting) {
                    en.target.classList.add('revealed');
                    io.unobserve(en.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
        items.forEach(el => io.observe(el));
        // reveal immediately anything already on screen (hero etc.)
        requestAnimationFrame(() => {
            items.forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.top < window.innerHeight) el.classList.add('revealed');
            });
        });
    }

    function countUpWallet() {
        const el = document.getElementById('club-wallet-count');
        if (!el) return;
        const target = parseInt(el.dataset.target, 10) || 0;
        const dur = 1100;
        const t0 = performance.now();
        const tick = (t) => {
            const k = Math.min(1, (t - t0) / dur);
            const eased = 1 - Math.pow(1 - k, 3);
            el.textContent = Math.round(target * eased);
            if (k < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
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
        // Debounced hover tick for interactive controls
        let lastHover = 0;
        const hoverTick = () => {
            const now = performance.now();
            if (now - lastHover > 90 && window.ClubAudio) {
                lastHover = now;
                window.ClubAudio.hover();
            }
        };

        document.querySelectorAll('form[data-club-action]').forEach(form => {
            form.addEventListener('submit', async (ev) => {
                ev.preventDefault();
                const btn = form.querySelector('button[type="submit"], button:not([type])');
                try {
                    if (btn) btn.disabled = true;
                    const data = await post(form.dataset.clubAction, collect(form));
                    if (data) {
                        if (window.ClubAudio) window.ClubAudio.chips();
                        const r = form.getBoundingClientRect();
                        confettiBurst(r.left + r.width / 2, r.top + 20, 45);
                        toast(data.error || 'Done', !data.error);
                        setTimeout(() => window.location.reload(), 700);
                    }
                } catch (e) {
                    toast(e.message, false);
                    if (btn) btn.disabled = false;
                }
            });
        });

        document.querySelectorAll('[data-club-post]').forEach(btn => {
            btn.addEventListener('mouseenter', hoverTick);
            btn.addEventListener('click', async () => {
                const confirmMsg = btn.dataset.confirm;
                if (confirmMsg && !window.confirm(confirmMsg)) return;
                let body = {};
                try { body = JSON.parse(btn.dataset.clubBody || '{}'); } catch (e) {}
                try {
                    btn.disabled = true;
                    const data = await post(btn.dataset.clubPost, body);
                    if (data) {
                        const r = btn.getBoundingClientRect();
                        confettiBurst(r.left + r.width / 2, r.top, 35);
                        toast('Done', true);
                        setTimeout(() => window.location.reload(), 700);
                    }
                } catch (e) {
                    toast(e.message, false);
                    btn.disabled = false;
                }
            });
        });

        // Signature FX buttons (Mix / Slap / Throw / Coins / Deal Me In)
        document.querySelectorAll('[data-fx]').forEach(btn => {
            btn.addEventListener('click', () => {
                audioArmed = true;
                if (window.ClubAudio) window.ClubAudio.unlock();
                fx(btn.dataset.fx);
                if (btn.dataset.fx === 'welcome-deal') {
                    const r = btn.getBoundingClientRect();
                    confettiBurst(r.left + r.width / 2, r.top + r.height / 2, 80);
                }
            });
        });

        const verifyBtn = document.getElementById('club-verify-btn');
        if (verifyBtn) {
            verifyBtn.addEventListener('mouseenter', hoverTick);
            verifyBtn.addEventListener('click', async () => {
                try {
                    verifyBtn.disabled = true;
                    const res = await fetch('/club/api/ledger/verify',
                        { headers: { 'X-Card-Club': '1' }, credentials: 'same-origin' });
                    const data = await res.json();
                    if (data.ok === false) throw new Error(data.error || 'Verify failed');
                    if (data.report.ok && window.ClubAudio) window.ClubAudio.coins();
                    toast('Ledger ' + (data.report.ok ? 'VERIFIED' : 'VIOLATIONS FOUND'),
                          data.report.ok);
                    if (data.report.ok) {
                        const r = verifyBtn.getBoundingClientRect();
                        confettiBurst(r.left + r.width / 2, r.top, 60);
                    }
                    setTimeout(() => window.location.reload(), 900);
                } catch (e) {
                    toast(e.message, false);
                    verifyBtn.disabled = false;
                }
            });
        }
    }

    return {
        init(globalLedger = false) {
            wire(globalLedger);
            revealInit();
            countUpWallet();
            wireSoundToggle();
            if (typeof this.initHeroInteractive === 'function') {
                try { this.initHeroInteractive(); } catch (e) { /* hero optional */ }
            }
            if (typeof this.initPlayerDiscovery === 'function') {
                try { this.initPlayerDiscovery(); } catch (e) { /* discovery optional */ }
            }
            if (typeof this.initCoinFaucet === 'function') {
                try { this.initCoinFaucet(); } catch (e) { /* faucet optional */ }
            }
            if (typeof this.initGameCatalogFilters === 'function') {
                try { this.initGameCatalogFilters(); } catch (e) { /* filters optional */ }
            }
            if (typeof this.initMultiplayerWizard === 'function') {
                try { this.initMultiplayerWizard(); } catch (e) { /* wizard optional */ }
            }
            // Arm the AudioContext on the first real user gesture
            // (browser autoplay policy) and fire the welcome flourish.
            const armOnce = () => {
                armAudio();
                document.removeEventListener('pointerdown', armOnce);
                document.removeEventListener('keydown', armOnce);
            };
            document.addEventListener('pointerdown', armOnce);
            document.addEventListener('keydown', armOnce);
        },
        initHeroInteractive() {
            // Audio controls
            const muteBtn = document.getElementById('hero-mute-btn');
            const volSlider = document.getElementById('hero-vol-slider');
            const muteIcon = document.getElementById('hero-mute-icon');

            function syncAudioUI() {
                const muted = window.ClubAudio ? window.ClubAudio.isMuted() : false;
                const vol = window.ClubAudio ? window.ClubAudio.getVolume() : 0.85;
                if (muteIcon) {
                    muteIcon.className = muted ? 'fa-solid fa-volume-xmark text-rose-400' : 'fa-solid fa-volume-high text-emerald-400';
                }
                if (volSlider) {
                    volSlider.value = Math.round(vol * 100);
                }
                const viz = document.getElementById('hero-audio-viz');
                if (viz) viz.classList.toggle('is-audio-playing', !muted && vol > 0);
            }
            syncAudioUI();

            if (muteBtn) {
                muteBtn.addEventListener('click', () => {
                    if (window.ClubAudio) {
                        window.ClubAudio.toggleMute();
                        syncAudioUI();
                    }
                });
            }

            if (volSlider) {
                volSlider.addEventListener('input', (e) => {
                    const v = parseInt(e.target.value, 10) / 100;
                    if (window.ClubAudio) {
                        window.ClubAudio.setVolume(v);
                        if (window.ClubAudio.isMuted()) window.ClubAudio.setMuted(false);
                        syncAudioUI();
                    }
                });
            }

            // Felt theme switcher
            const feltArea = document.getElementById('hero-felt-table');
            document.querySelectorAll('.hero-felt-theme-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const theme = btn.dataset.feltTheme;
                    if (feltArea) {
                        feltArea.classList.remove('felt-emerald', 'felt-midnight', 'felt-crimson');
                        feltArea.classList.add(theme);
                        if (window.ClubAudio) window.ClubAudio.hover();
                    }
                });
            });

            // Action: Mix / Shuffle
            const mixBtn = document.getElementById('hero-act-shuffle');
            const riffleDeck = document.getElementById('hero-riffle-deck');
            if (mixBtn && riffleDeck) {
                mixBtn.addEventListener('click', () => {
                    if (riffleDeck.classList.contains('is-shuffling')) return;
                    riffleDeck.classList.add('is-shuffling');
                    if (window.ClubAudio) window.ClubAudio.shuffle();
                    
                    // Create fluttering cards
                    const flutterContainer = document.getElementById('hero-flutter-cards');
                    if (flutterContainer) {
                        flutterContainer.innerHTML = '';
                        for (let i = 0; i < 8; i++) {
                            const fc = document.createElement('div');
                            fc.className = 'riffle-interleave-card playing-card-3d absolute';
                            fc.style.setProperty('--flutter-rot', `${(Math.random() * 16 - 8).toFixed(1)}deg`);
                            fc.style.animationDelay = `${(i * 0.05).toFixed(2)}s`;
                            fc.innerHTML = `
                                <div class="card-back">
                                    <div class="card-back-pattern">
                                        <i class="fa-solid fa-diamond text-amber-400/40 text-xs"></i>
                                    </div>
                                </div>
                            `;
                            flutterContainer.appendChild(fc);
                        }
                    }

                    setTimeout(() => {
                        riffleDeck.classList.remove('is-shuffling');
                    }, 850);
                });
            }

            // Action: Card Slap
            const slapBtn = document.getElementById('hero-act-slap');
            const slapTarget = document.getElementById('hero-slap-dropzone');
            if (slapBtn && slapTarget) {
                slapBtn.addEventListener('click', () => {
                    if (window.ClubAudio) window.ClubAudio.slap();
                    
                    // Trigger table shake
                    if (feltArea) {
                        feltArea.classList.remove('table-slap-impact');
                        void feltArea.offsetWidth;
                        feltArea.classList.add('table-slap-impact');
                    }

                    // Shockwave ring
                    const wave = document.createElement('div');
                    wave.className = 'slap-shockwave';
                    slapTarget.appendChild(wave);
                    setTimeout(() => wave.remove(), 500);

                    // Slap card
                    const card = document.createElement('div');
                    card.className = 'playing-card-3d anim-card-slap relative';
                    const sampleCards = [
                        { r: 'A', s: '♠', red: false },
                        { r: 'K', s: '♥', red: true },
                        { r: 'J', s: '♠', red: false },
                        { r: 'Q', s: '♦', red: true }
                    ];
                    const pick = sampleCards[Math.floor(Math.random() * sampleCards.length)];
                    card.innerHTML = `
                        <div class="card-face ${pick.red ? 'suit-red' : 'suit-black'}">
                            <div class="card-corner card-corner-top">
                                <span class="card-val">${pick.r}</span>
                                <span class="card-suit-sm">${pick.s}</span>
                            </div>
                            <div class="card-center court-card">${pick.s}</div>
                            <div class="card-corner card-corner-bottom">
                                <span class="card-val">${pick.r}</span>
                                <span class="card-suit-sm">${pick.s}</span>
                            </div>
                        </div>
                    `;
                    slapTarget.innerHTML = '';
                    slapTarget.appendChild(card);
                });
            }

            // Action: Card Throw
            const throwBtn = document.getElementById('hero-act-throw');
            const throwTarget = document.getElementById('hero-throw-dropzone');
            if (throwBtn && throwTarget) {
                throwBtn.addEventListener('click', () => {
                    if (window.ClubAudio) window.ClubAudio.throw();

                    const card = document.createElement('div');
                    card.className = 'playing-card-3d anim-card-flight relative';
                    const rot = (Math.random() * 24 - 12).toFixed(1);
                    card.style.setProperty('--throw-rot', `${rot}deg`);
                    card.style.setProperty('--throw-from-x', `${(Math.random() * 80 - 40).toFixed(0)}px`);
                    card.style.setProperty('--throw-from-y', '150px');
                    card.style.setProperty('--throw-to-x', '0px');
                    card.style.setProperty('--throw-to-y', '0px');

                    const sampleCards = [
                        { r: '10', s: '♦', red: true },
                        { r: 'A', s: '♣', red: false },
                        { r: '9', s: '♥', red: true },
                        { r: 'J', s: '♣', red: false }
                    ];
                    const pick = sampleCards[Math.floor(Math.random() * sampleCards.length)];
                    card.innerHTML = `
                        <div class="card-face ${pick.red ? 'suit-red' : 'suit-black'}">
                            <div class="card-corner card-corner-top">
                                <span class="card-val">${pick.r}</span>
                                <span class="card-suit-sm">${pick.s}</span>
                            </div>
                            <div class="card-center court-card">${pick.s}</div>
                            <div class="card-corner card-corner-bottom">
                                <span class="card-val">${pick.r}</span>
                                <span class="card-suit-sm">${pick.s}</span>
                            </div>
                        </div>
                    `;
                    throwTarget.innerHTML = '';
                    throwTarget.appendChild(card);
                });
            }

            // Action: Deal cards
            const dealBtn = document.getElementById('hero-act-deal');
            const dealTarget = document.getElementById('hero-deal-dropzone');
            if (dealBtn && dealTarget) {
                dealBtn.addEventListener('click', () => {
                    dealTarget.innerHTML = '';
                    const sampleCards = [
                        { r: 'A', s: '♠', red: false },
                        { r: 'K', s: '♥', red: true },
                        { r: 'Q', s: '♦', red: true },
                        { r: 'J', s: '♣', red: false },
                        { r: '10', s: '♠', red: false }
                    ];
                    sampleCards.forEach((c, idx) => {
                        setTimeout(() => {
                            if (window.ClubAudio) window.ClubAudio.deal();
                            const card = document.createElement('div');
                            card.className = 'playing-card-3d anim-card-deal';
                            card.style.marginLeft = idx === 0 ? '0px' : '-24px';
                            card.innerHTML = `
                                <div class="card-face ${c.red ? 'suit-red' : 'suit-black'}">
                                    <div class="card-corner card-corner-top">
                                        <span class="card-val">${c.r}</span>
                                        <span class="card-suit-sm">${c.s}</span>
                                    </div>
                                    <div class="card-center court-card">${c.s}</div>
                                    <div class="card-corner card-corner-bottom">
                                        <span class="card-val">${c.r}</span>
                                        <span class="card-suit-sm">${c.s}</span>
                                    </div>
                                </div>
                            `;
                            card.addEventListener('mouseenter', () => window.ClubAudio && window.ClubAudio.hover());
                            dealTarget.appendChild(card);
                        }, idx * 110);
                    });
                });
            }

            // Action: Chip Bet
            const chipsBtn = document.getElementById('hero-act-chips');
            const chipsTarget = document.getElementById('hero-chips-dropzone');
            if (chipsBtn && chipsTarget) {
                chipsBtn.addEventListener('click', () => {
                    if (window.ClubAudio) window.ClubAudio.chips();
                    const chip = document.createElement('div');
                    chip.className = 'anim-chip-pop inline-flex items-center justify-center w-11 h-11 rounded-full bg-gradient-to-br from-amber-300 via-amber-500 to-amber-700 border-2 border-white/80 shadow-lg font-mono font-black text-slate-950 text-xs select-none';
                    chip.textContent = '100';
                    chipsTarget.appendChild(chip);
                    setTimeout(() => chip.remove(), 2400);
                });
            }

            // Action: Victory Win
            const winBtn = document.getElementById('hero-act-win');
            if (winBtn) {
                winBtn.addEventListener('click', () => {
                    if (window.ClubAudio) {
                        window.ClubAudio.win();
                        setTimeout(() => window.ClubAudio.coins(), 750);
                    }
                    const r = winBtn.getBoundingClientRect();
                    if (typeof this.confettiBurst === 'function') {
                        this.confettiBurst(r.left + r.width / 2, r.top, 130);
                    }
                    toast('🏆 Victory Fanfare: Triad Harmony Sound Triggered!', true);
                });
            }

            // Interactive sound hover on game catalog cards
            document.querySelectorAll('.catalog-game-card').forEach(card => {
                card.addEventListener('mouseenter', () => {
                    if (window.ClubAudio) window.ClubAudio.hover();
                });
                card.addEventListener('click', () => {
                    if (window.ClubAudio) window.ClubAudio.deal();
                });
            });

            // Ambient floating suit particles
            const suitsCanvas = document.getElementById('hero-suits-canvas');
            if (suitsCanvas) {
                const suits = ['♠', '♥', '♦', '♣'];
                for (let i = 0; i < 16; i++) {
                    const span = document.createElement('span');
                    span.className = 'floating-suit';
                    span.textContent = suits[i % suits.length];
                    span.style.left = `${(Math.random() * 96).toFixed(1)}%`;
                    span.style.animationDelay = `${(Math.random() * 10).toFixed(1)}s`;
                    span.style.animationDuration = `${(8 + Math.random() * 8).toFixed(1)}s`;
                    span.style.fontSize = `${(1 + Math.random() * 1.5).toFixed(1)}rem`;
                    if (span.textContent === '♥' || span.textContent === '♦') {
                        span.style.color = 'rgba(239, 68, 68, 0.08)';
                    }
                    suitsCanvas.appendChild(span);
                }
            }
        },
        initPlayerDiscovery() {
            // Tab switching
            const tabs = document.querySelectorAll('.lobby-tab-btn');
            const panes = document.querySelectorAll('.lobby-tab-pane');
            tabs.forEach(btn => {
                btn.addEventListener('click', () => {
                    tabs.forEach(t => {
                        t.classList.remove('active');
                        t.classList.add('text-slate-400');
                    });
                    btn.classList.add('active');
                    btn.classList.remove('text-slate-400');
                    const targetId = btn.getAttribute('data-target');
                    panes.forEach(p => {
                        if (p.id === targetId) {
                            p.classList.remove('hidden');
                        } else {
                            p.classList.add('hidden');
                        }
                    });
                    if (window.ClubAudio) window.ClubAudio.deal();
                });
            });

            // Group selector changing join URL & WhatsApp text
            const grpSelect = document.getElementById('hub-group-select');
            const urlInput = document.getElementById('hub-share-url-input');
            const waBtn = document.getElementById('hub-whatsapp-btn');
            const tgBtn = document.getElementById('hub-telegram-btn');

            function updateShareUrls() {
                if (!grpSelect || !urlInput) return;
                const opt = grpSelect.selectedOptions[0];
                if (!opt) return;
                const code = opt.getAttribute('data-code');
                const name = opt.getAttribute('data-name') || 'Private Room';
                const base = window.location.origin;
                const joinUrl = `${base}/club/join/${code}`;
                urlInput.value = joinUrl;

                const waText = `🃏 Hey! Join my private Card Club room '${name}' on Rubique to play games with real-time video & chips: ${joinUrl}`;
                if (waBtn) {
                    waBtn.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(waText)}`;
                }
                if (tgBtn) {
                    tgBtn.href = `https://t.me/share/url?url=${encodeURIComponent(joinUrl)}&text=${encodeURIComponent(`🃏 Join my private Card Club room on Rubique: ${name}`)}`;
                }
            }

            if (grpSelect) {
                grpSelect.addEventListener('change', () => {
                    updateShareUrls();
                    if (window.ClubAudio) window.ClubAudio.hover();
                });
            }

            // Copy Link button
            const copyBtn = document.getElementById('hub-copy-link-btn');
            if (copyBtn && urlInput) {
                copyBtn.addEventListener('click', async () => {
                    try {
                        await navigator.clipboard.writeText(urlInput.value);
                        toast('📋 Invitation link copied to clipboard! Share on WhatsApp with your friends.', true);
                        if (window.ClubAudio) window.ClubAudio.success();
                    } catch (e) {
                        urlInput.select();
                        document.execCommand('copy');
                        toast('📋 Invitation link copied!', true);
                    }
                });
            }

            // Native Web Share
            const nativeShareBtn = document.getElementById('hub-native-share-btn');
            if (nativeShareBtn && urlInput) {
                nativeShareBtn.addEventListener('click', async () => {
                    const opt = grpSelect ? grpSelect.selectedOptions[0] : null;
                    const name = opt ? (opt.getAttribute('data-name') || 'Card Club') : 'Card Club';
                    const shareData = {
                        title: `Card Club - ${name}`,
                        text: `🃏 Join my private Card Club room '${name}' on Rubique!`,
                        url: urlInput.value
                    };
                    if (navigator.share) {
                        try {
                            await navigator.share(shareData);
                            toast('Invitation shared!', true);
                        } catch (e) { /* cancelled */ }
                    } else if (waBtn) {
                        waBtn.click();
                    }
                });
            }

            // Live member search
            const searchInput = document.getElementById('hub-player-search-input');
            const playersGrid = document.getElementById('hub-players-grid');
            let searchTimeout = null;

            if (searchInput && playersGrid) {
                searchInput.addEventListener('input', () => {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(async () => {
                        const q = searchInput.value.trim();
                        try {
                            const res = await fetch(`/club/api/members/search?q=${encodeURIComponent(q)}`, {
                                headers: { 'Accept': 'application/json' }
                            });
                            const data = await res.json();
                            if (!data.ok || !data.members) return;
                            playersGrid.innerHTML = '';
                            if (data.members.length === 0) {
                                playersGrid.innerHTML = '<p class="text-xs text-slate-500 font-mono col-span-3 text-center py-4">No matching players found.</p>';
                                return;
                            }
                            data.members.forEach(pl => {
                                const card = document.createElement('div');
                                card.className = 'p-3 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/40 transition-all flex items-center justify-between gap-3 player-card-item';
                                card.innerHTML = `
                                    <div class="flex items-center gap-2.5 overflow-hidden">
                                        <div class="player-avatar-chip shrink-0 bg-emerald-600" style="background-color: ${pl.avatar_color || '#059669'}">
                                            ${(pl.username[0] || 'U').toUpperCase()}
                                            <span class="player-online-dot"></span>
                                        </div>
                                        <div class="overflow-hidden">
                                            <div class="text-xs font-bold text-white truncate">${pl.username}</div>
                                            <div class="text-[10px] text-slate-400 font-mono uppercase">${pl.role || 'Member'} &bull; Ready</div>
                                        </div>
                                    </div>
                                    <button type="button" class="hub-invite-player-btn px-2.5 py-1.5 rounded-lg bg-emerald-600/80 hover:bg-emerald-500 text-white font-bold text-[11px] font-mono shrink-0 transition-all"
                                            data-username="${pl.username}" title="Invite to current group">
                                        <i class="fa-solid fa-paper-plane mr-1"></i>Invite
                                    </button>
                                `;
                                playersGrid.appendChild(card);
                            });
                            wireInviteButtons();
                        } catch (e) { /* ignore */ }
                    }, 250);
                });
            }

            function wireInviteButtons() {
                document.querySelectorAll('.hub-invite-player-btn').forEach(btn => {
                    btn.onclick = async () => {
                        const uname = btn.getAttribute('data-username');
                        const gid = grpSelect ? grpSelect.value : null;
                        if (!gid) {
                            toast('Please create or select a group first', false);
                            return;
                        }
                        try {
                            btn.disabled = true;
                            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                            await post(`/club/api/groups/${gid}/invites`, { username: uname });
                            toast(`VIP Invitation sent to @${uname}!`, true);
                            if (window.ClubAudio) window.ClubAudio.success();
                            btn.className = 'px-2.5 py-1.5 rounded-lg bg-slate-800 text-emerald-400 font-mono text-[10px] shrink-0';
                            btn.innerHTML = '<i class="fa-solid fa-check mr-1"></i>Invited';
                        } catch (e) {
                            toast(e.message, false);
                            btn.disabled = false;
                            btn.innerHTML = '<i class="fa-solid fa-paper-plane mr-1"></i>Invite';
                        }
                    };
                });
            }
            wireInviteButtons();
        },
        initCoinFaucet() {
            const claimButtons = [
                document.getElementById('hero-btn-claim-coins'),
                document.getElementById('wizard-claim-coins-btn'),
                document.getElementById('wizard-refill-alert-btn')
            ].filter(Boolean);

            claimButtons.forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    const originalHtml = btn.innerHTML;
                    try {
                        btn.disabled = true;
                        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Claiming...';
                        const res = await post('/club/api/wallet/claim', {});
                        btn.disabled = false;
                        btn.innerHTML = originalHtml;
                        if (res && res.ok) {
                            if (window.ClubAudio) {
                                window.ClubAudio.coins();
                                setTimeout(() => window.ClubAudio && window.ClubAudio.win(), 250);
                            }
                            const r = btn.getBoundingClientRect();
                            confettiBurst(r.left + r.width / 2, r.top, 80);
                            toast(res.message || '🎉 +100 Coins claimed successfully!', true);

                            // Update balances across the UI
                            const walletEl = document.getElementById('club-wallet-count');
                            if (walletEl) {
                                walletEl.textContent = res.balance;
                                walletEl.dataset.target = res.balance;
                            }
                            const wizardBalEl = document.getElementById('wizard-my-balance-display');
                            if (wizardBalEl) {
                                wizardBalEl.textContent = res.balance;
                            }

                            // Dismiss insufficient coins alerts
                            const alertBox = document.getElementById('wizard-insufficient-coins-alert');
                            if (alertBox) alertBox.classList.add('hidden');
                            const nextBtn = document.getElementById('wizard-next-btn');
                            if (nextBtn) nextBtn.disabled = false;
                        }
                    } catch (err) {
                        toast(err.message || 'Failed to claim coins', false);
                        btn.disabled = false;
                        btn.innerHTML = originalHtml;
                    }
                });
            });
        },
        initGameCatalogFilters() {
            const pills = document.querySelectorAll('.mode-filter-pill');
            const searchInput = document.getElementById('game-catalog-search');
            const cards = document.querySelectorAll('.catalog-game-card');

            let currentMode = 'all';
            let currentSearch = '';

            const applyFilter = () => {
                const q = currentSearch.toLowerCase().trim();
                cards.forEach(card => {
                    const solo = card.dataset.solo === '1';
                    const com = card.dataset.com === '1';
                    const multi = card.dataset.multi === '1';
                    const name = (card.dataset.name || '').toLowerCase();
                    const slug = (card.dataset.slug || '').toLowerCase();
                    const text = card.textContent.toLowerCase();

                    let modeMatch = true;
                    if (currentMode === 'solo') modeMatch = solo;
                    else if (currentMode === 'com') modeMatch = com;
                    else if (currentMode === 'multiplayer') modeMatch = multi;

                    let textMatch = true;
                    if (q) {
                        textMatch = name.includes(q) || slug.includes(q) || text.includes(q);
                    }

                    if (modeMatch && textMatch) {
                        card.classList.remove('hidden');
                    } else {
                        card.classList.add('hidden');
                    }
                });
            };

            pills.forEach(pill => {
                pill.addEventListener('click', () => {
                    pills.forEach(p => {
                        p.classList.remove('active', 'border-emerald-500/40');
                        p.classList.add('bg-slate-900', 'border-slate-800', 'text-slate-300');
                    });
                    pill.classList.add('active', 'border-emerald-500/40');
                    pill.classList.remove('bg-slate-900', 'border-slate-800', 'text-slate-300');
                    currentMode = pill.dataset.mode || 'all';
                    if (window.ClubAudio) window.ClubAudio.hover();
                    applyFilter();
                });
            });

            if (searchInput) {
                searchInput.addEventListener('input', () => {
                    currentSearch = searchInput.value;
                    applyFilter();
                });
            }
        },
        initMultiplayerWizard() {
            const modal = document.getElementById('multiplayer-wizard-modal');
            if (!modal) return;

            const openBtns = [
                document.getElementById('btn-open-multiplayer-wizard'),
                document.getElementById('btn-banner-open-wizard')
            ].filter(Boolean);

            const closeBtn = document.getElementById('wizard-close-btn');
            const prevBtn = document.getElementById('wizard-prev-btn');
            const nextBtn = document.getElementById('wizard-next-btn');
            const counter = document.getElementById('wizard-step-counter');

            // Game options in step 1
            const gameOptions = document.querySelectorAll('.wizard-game-option');
            const quotaContainer = document.getElementById('wizard-quota-buttons-container');
            const privPrivateCard = document.getElementById('wizard-privacy-private');
            const privPublicCard = document.getElementById('wizard-privacy-public');
            const stakeBtns = document.querySelectorAll('.wizard-chip-btn[data-stake]');
            const insufficientAlert = document.getElementById('wizard-insufficient-coins-alert');
            const aliasToggle = document.getElementById('wizard-use-alias-toggle');
            const fakeNameInput = document.getElementById('wizard-fake-name-input');
            const aliasWrapper = document.getElementById('wizard-alias-input-wrapper');
            const launchBtn = document.getElementById('wizard-btn-launch-table');

            // Summary elements in step 6
            const sumGame = document.getElementById('w-sum-game');
            const sumQuota = document.getElementById('w-sum-quota');
            const sumPrivacy = document.getElementById('w-sum-privacy');
            const sumStake = document.getElementById('w-sum-stake');
            const sumAlias = document.getElementById('w-sum-alias');

            // State
            let step = 1;
            let selectedSlug = 'callbreak';
            let selectedName = 'Call Break';
            let selectedMin = 4;
            let selectedMax = 4;
            let selectedQuota = 4;
            let selectedPrivacy = 'private'; // 'private' or 'public'
            let selectedStake = 10;
            let currentFlowMode = 'multiplayer';
            let useAlias = true;
            let fakeName = fakeNameInput ? fakeNameInput.value.trim() : 'GhostAce_777';
            let createdTableId = null;

            function getMyBalance() {
                const balEl = document.getElementById('wizard-my-balance-display');
                if (!balEl) return 100;
                return parseInt(balEl.textContent.replace(/[^0-9]/g, ''), 10) || 0;
            }

            function openWizard(preselectedSlug = null, initialMode = 'multiplayer') {
                step = 1;
                createdTableId = null;
                currentFlowMode = initialMode || 'multiplayer';
                document.getElementById('wizard-launch-action-box')?.classList.remove('hidden');
                document.getElementById('wizard-created-hub-box')?.classList.add('hidden');
                if (nextBtn) {
                    nextBtn.innerHTML = '<span>Next</span> &rarr;';
                    nextBtn.classList.remove('hidden');
                }

                if (preselectedSlug) {
                    const opt = document.querySelector(`.wizard-game-option[data-slug="${preselectedSlug}"]`);
                    if (opt) selectGameOption(opt);
                } else {
                    const first = document.querySelector('.wizard-game-option.selected') || gameOptions[0];
                    if (first) selectGameOption(first);
                }

                renderStep();
                modal.classList.remove('hidden');
                document.body.style.overflow = 'hidden';
                if (window.ClubAudio) window.ClubAudio.deal();
            }

            function closeWizard() {
                modal.classList.add('hidden');
                document.body.style.overflow = '';
            }

            openBtns.forEach(b => b.addEventListener('click', () => openWizard()));
            if (closeBtn) closeBtn.addEventListener('click', closeWizard);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeWizard();
            });
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && !modal.classList.contains('hidden')) closeWizard();
            });

            // Direct buttons on 23 catalog cards
            document.querySelectorAll('.btn-card-multi').forEach(b => {
                b.addEventListener('click', () => {
                    const slug = b.dataset.gameSlug;
                    openWizard(slug, 'multiplayer');
                });
            });
            document.querySelectorAll('.btn-card-solo').forEach(b => {
                b.addEventListener('click', () => {
                    const slug = b.dataset.gameSlug;
                    openWizard(slug, 'solo');
                });
            });
            document.querySelectorAll('.btn-card-com').forEach(b => {
                b.addEventListener('click', () => {
                    const slug = b.dataset.gameSlug;
                    openWizard(slug, 'vs_com');
                });
            });

            function selectGameOption(opt) {
                gameOptions.forEach(o => o.classList.remove('selected', 'border-emerald-500'));
                opt.classList.add('selected', 'border-emerald-500');

                selectedSlug = opt.dataset.slug;
                selectedName = opt.dataset.name;
                selectedMin = parseInt(opt.dataset.min, 10) || 2;
                selectedMax = parseInt(opt.dataset.max, 10) || 4;

                const lbl = document.getElementById('wizard-selected-game-label');
                if (lbl) lbl.textContent = `${selectedName} Selected`;
                if (sumGame) sumGame.textContent = selectedName;

                buildQuotaButtons();
            }

            gameOptions.forEach(opt => {
                opt.addEventListener('click', () => {
                    selectGameOption(opt);
                    if (window.ClubAudio) window.ClubAudio.hover();
                });
            });

            function buildQuotaButtons() {
                if (!quotaContainer) return;
                quotaContainer.innerHTML = '';
                const min = Math.max(1, selectedMin);
                const max = Math.max(min, selectedMax);

                if (selectedQuota < min || selectedQuota > max) {
                    selectedQuota = max;
                }

                for (let count = min; count <= max; count++) {
                    const isSel = (count === selectedQuota);
                    const qBtn = document.createElement('button');
                    qBtn.type = 'button';
                    qBtn.className = `wizard-chip-btn ${isSel ? 'selected' : ''} p-3.5 rounded-2xl bg-slate-900 border ${isSel ? 'border-amber-400 text-amber-300' : 'border-slate-700 text-white'} font-mono flex flex-col items-center justify-center gap-1 transition-all`;
                    qBtn.dataset.quota = count;
                    qBtn.innerHTML = `
                        <span class="text-sm font-bold">${count} Players</span>
                        <span class="text-[9px] text-slate-400 uppercase">${count === max ? 'Standard Full' : (count === 1 ? 'Solo' : 'Custom Limit')}</span>
                    `;
                    qBtn.addEventListener('click', () => {
                        quotaContainer.querySelectorAll('.wizard-chip-btn').forEach(b => {
                            b.classList.remove('selected', 'border-amber-400', 'text-amber-300');
                            b.classList.add('border-slate-700', 'text-white');
                        });
                        qBtn.classList.add('selected', 'border-amber-400', 'text-amber-300');
                        qBtn.classList.remove('border-slate-700', 'text-white');
                        selectedQuota = count;
                        if (sumQuota) sumQuota.textContent = `${selectedQuota} Players (Strict Limit)`;
                        if (window.ClubAudio) window.ClubAudio.hover();
                    });
                    quotaContainer.appendChild(qBtn);
                }

                if (sumQuota) sumQuota.textContent = `${selectedQuota} Players (Strict Limit)`;
            }

            // Step 3: Privacy
            if (privPrivateCard && privPublicCard) {
                privPrivateCard.addEventListener('click', () => {
                    privPrivateCard.classList.add('selected', 'border-emerald-500');
                    privPublicCard.classList.remove('selected', 'border-cyan-500');
                    selectedPrivacy = 'private';
                    if (sumPrivacy) sumPrivacy.textContent = 'Private (100% Encrypted & Anonymous)';
                    if (window.ClubAudio) window.ClubAudio.hover();
                });
                privPublicCard.addEventListener('click', () => {
                    privPublicCard.classList.add('selected', 'border-cyan-500');
                    privPrivateCard.classList.remove('selected', 'border-emerald-500');
                    selectedPrivacy = 'public';
                    if (sumPrivacy) sumPrivacy.textContent = 'Public Room (Open Lobby)';
                    if (window.ClubAudio) window.ClubAudio.hover();
                });
            }

            // Step 4: Stakes & Coin Balance
            stakeBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    stakeBtns.forEach(b => {
                        b.classList.remove('selected', 'border-amber-400', 'text-amber-300');
                        b.classList.add('border-slate-700', 'text-white');
                    });
                    btn.classList.add('selected', 'border-amber-400', 'text-amber-300');
                    btn.classList.remove('border-slate-700', 'text-white');
                    selectedStake = parseInt(btn.dataset.stake, 10) || 0;
                    if (sumStake) sumStake.textContent = `${selectedStake} Coins`;
                    validateCoins();
                    if (window.ClubAudio) window.ClubAudio.chips();
                });
            });

            function validateCoins() {
                const bal = getMyBalance();
                const insufficient = (bal < selectedStake);
                if (insufficientAlert) {
                    if (insufficient) insufficientAlert.classList.remove('hidden');
                    else insufficientAlert.classList.add('hidden');
                }
                if (nextBtn && step === 4) {
                    nextBtn.disabled = insufficient;
                }
                return !insufficient;
            }

            // Step 5: Fake name
            if (aliasToggle) {
                aliasToggle.addEventListener('change', () => {
                    useAlias = aliasToggle.checked;
                    if (aliasWrapper) {
                        aliasWrapper.style.opacity = useAlias ? '1' : '0.4';
                        aliasWrapper.style.pointerEvents = useAlias ? 'auto' : 'none';
                    }
                    updateAliasSummary();
                });
            }
            if (fakeNameInput) {
                fakeNameInput.addEventListener('input', () => {
                    fakeName = fakeNameInput.value.trim();
                    updateAliasSummary();
                });
            }
            function updateAliasSummary() {
                if (sumAlias) {
                    sumAlias.textContent = useAlias && fakeName ? fakeName : 'Real Username (Unmasked)';
                }
            }

            function renderStep() {
                for (let i = 1; i <= 6; i++) {
                    const pane = document.getElementById(`wizard-pane-${i}`);
                    if (pane) {
                        if (i === step) pane.classList.remove('hidden');
                        else pane.classList.add('hidden');
                    }
                }

                document.querySelectorAll('.wizard-step-indicator').forEach(ind => {
                    const s = parseInt(ind.dataset.step, 10);
                    if (s === step) {
                        ind.className = 'wizard-step-indicator active p-2 rounded-xl border border-emerald-500/60 bg-emerald-950/40 text-center text-emerald-300 font-bold';
                    } else if (s < step) {
                        ind.className = 'wizard-step-indicator p-2 rounded-xl border border-emerald-500/30 text-center text-emerald-400/70';
                    } else {
                        ind.className = 'wizard-step-indicator p-2 rounded-xl border border-slate-800 text-center text-slate-500';
                    }
                });

                if (counter) counter.textContent = `Step ${step} of 6`;
                if (prevBtn) prevBtn.disabled = (step === 1);

                if (step === 4) {
                    validateCoins();
                } else if (nextBtn) {
                    nextBtn.disabled = false;
                }

                if (step === 6) {
                    if (nextBtn) nextBtn.classList.add('hidden');
                } else {
                    if (nextBtn) {
                        nextBtn.classList.remove('hidden');
                        nextBtn.innerHTML = '<span>Next</span> &rarr;';
                    }
                }
            }

            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    if (step > 1) {
                        step--;
                        renderStep();
                        if (window.ClubAudio) window.ClubAudio.deal();
                    }
                });
            }

            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    if (step === 4 && !validateCoins()) return;
                    if (step < 6) {
                        step++;
                        renderStep();
                        if (window.ClubAudio) window.ClubAudio.deal();
                    }
                });
            }

            // Step 6: Create Table Action
            if (launchBtn) {
                launchBtn.addEventListener('click', async () => {
                    const originalHtml = launchBtn.innerHTML;
                    launchBtn.disabled = true;
                    launchBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> টেবিল তৈরি হচ্ছে...';

                    try {
                        let groupId = null;
                        let inviteCode = '';
                        const grpSelect = document.getElementById('hub-group-select');
                        if (grpSelect && grpSelect.value) {
                            groupId = grpSelect.value;
                            const opt = grpSelect.selectedOptions[0];
                            inviteCode = opt ? opt.getAttribute('data-code') : '';
                        }

                        // If user doesn't have an existing group, create one
                        if (!groupId) {
                            const groupRes = await post('/club/api/groups', {
                                name: `${selectedName} ${selectedPrivacy === 'private' ? 'Private' : 'Public'} Arena`,
                                is_private: selectedPrivacy === 'private' ? 1 : 0,
                                fake_name: useAlias ? fakeName : ''
                            });
                            if (groupRes && groupRes.group_id) {
                                groupId = groupRes.group_id;
                                inviteCode = groupRes.invite_code;
                            }
                        }

                        // Ensure fake name alias is registered for the group if enabled
                        if (groupId && useAlias && fakeName) {
                            try {
                                await post(`/club/api/groups/${groupId}/alias`, { fake_name: fakeName });
                            } catch (e) { /* ignore */ }
                        }

                        // Create the table
                        const tableRes = await post(`/club/api/groups/${groupId}/tables`, {
                            game_slug: selectedSlug,
                            name: `${selectedName} Table (${selectedQuota}p)`,
                            max_seats: selectedQuota,
                            stake: selectedStake,
                            is_private: selectedPrivacy === 'private' ? 1 : 0,
                            mode: currentFlowMode || 'multiplayer',
                            fake_name: useAlias ? fakeName : ''
                        });

                        if (tableRes && tableRes.table_id) {
                            createdTableId = tableRes.table_id;
                            if (window.ClubAudio) {
                                window.ClubAudio.win();
                                setTimeout(() => window.ClubAudio && window.ClubAudio.coins(), 300);
                            }
                            const r = launchBtn.getBoundingClientRect();
                            confettiBurst(r.left + r.width / 2, r.top, 90);
                            toast('🎉 টেবিল সফলভাবে তৈরি হয়েছে! কোটা: ১/' + selectedQuota, true);

                            // Switch to success UI
                            document.getElementById('wizard-launch-action-box')?.classList.add('hidden');
                            const hubBox = document.getElementById('wizard-created-hub-box');
                            if (hubBox) hubBox.classList.remove('hidden');

                            const quotaBadge = document.getElementById('wizard-created-quota-badge');
                            if (quotaBadge) quotaBadge.textContent = `কোটা: ১ / ${selectedQuota} জন ভর্তি`;

                            const base = window.location.origin;
                            const tableUrl = `${base}/club/tables/${createdTableId}`;
                            const joinUrl = inviteCode ? `${base}/club/join/${inviteCode}` : tableUrl;

                            const tableLinkBtn = document.getElementById('wizard-created-table-link');
                            if (tableLinkBtn) tableLinkBtn.href = tableUrl;

                            const waBtn = document.getElementById('wizard-created-whatsapp-btn');
                            if (waBtn) {
                                const waMsg = `🃏 Hey! Join my ${selectedPrivacy === 'private' ? 'private' : 'public'} ${selectedName} match on Rubique Card Club! (Quota: ${selectedQuota} players, First-come first-served, Stake: ${selectedStake} coins): ${joinUrl}`;
                                waBtn.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(waMsg)}`;
                            }

                            const copyBtn = document.getElementById('wizard-created-copy-btn');
                            if (copyBtn) {
                                copyBtn.onclick = async () => {
                                    try {
                                        await navigator.clipboard.writeText(joinUrl);
                                        toast('📋 ইনভাইট লিংক কপি হয়েছে! বন্ধুদের মেসেজ দিন।', true);
                                        if (window.ClubAudio) window.ClubAudio.success();
                                    } catch (e) {
                                        toast('ইনভাইট লিঙ্ক: ' + joinUrl, true);
                                    }
                                };
                            }
                        }
                    } catch (err) {
                        toast(err.message || 'টেবিল তৈরিতে সমস্যা হয়েছে', false);
                        launchBtn.disabled = false;
                        launchBtn.innerHTML = originalHtml;
                    }
                });
            }
        },
        toast, post
    };
})();


const ClubTable = (() => {
    let view = null;
    let socket = null;
    let pollTimer = null;
    let live = false;
    // Motion state: diff-based animations so polls/re-renders never re-play
    // old card flights, and we know when a match just started.
    let prevTurn = null;
    let prevStatus = null;
    let prevCenterIds = new Set();
    let justStarted = false;
    let lastLocalMoveAt = 0;
    let firstLoad = true;

    const C = () => window.CLUB;

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    const SUITS = { 'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣' };
    const SUIT_NAMES = { 'S': 'Spades', 'H': 'Hearts', 'D': 'Diamonds', 'C': 'Clubs' };

    function parseCard(c) {
        if (!c || typeof c !== 'string') return null;
        c = c.trim().toUpperCase();
        let s = c.charAt(0);
        let r = c.slice(1);
        if (!SUITS[s]) {
            s = c.slice(-1);
            r = c.slice(0, -1);
        }
        if (!SUITS[s]) return null;
        if (r === 'T') r = '10';
        return { suit: s, symbol: SUITS[s], rank: r, isRed: (s === 'H' || s === 'D') };
    }

    function render3DCard(c, opts = {}) {
        const info = parseCard(c);
        if (!info) {
            return `<div class="playing-card-3d"><div class="card-back"><div class="card-back-pattern">🂠</div></div></div>`;
        }
        const suitSymbol = info.symbol;
        const isRed = info.isRed;
        const suitClass = isRed ? 'suit-red' : 'suit-black';
        const court = (info.rank === 'J' || info.rank === 'Q' || info.rank === 'K' || info.rank === 'A');
        const isPlayable = opts.playable ? 'is-playable' : '';
        const animClass = opts.anim || '';
        const styleAttr = opts.style ? `style="${opts.style}"` : '';
        const actIndex = opts.actionIndex !== undefined ? `data-action-index="${opts.actionIndex}"` : '';

        return `
        <div class="playing-card-3d ${isPlayable} ${animClass} group" data-card="${esc(c)}" ${actIndex} ${styleAttr} onmouseenter="window.ClubAudio && window.ClubAudio.hover()">
            <div class="card-face ${suitClass}">
                <div class="card-corner card-corner-top">
                    <span class="card-val">${esc(info.rank)}</span>
                    <span class="card-suit-sm">${suitSymbol}</span>
                </div>
                <div class="card-center ${court ? 'court-card' : ''}">
                    ${court ? esc(info.rank) : suitSymbol}
                </div>
                <div class="card-corner card-corner-bottom">
                    <span class="card-val">${esc(info.rank)}</span>
                    <span class="card-suit-sm">${suitSymbol}</span>
                </div>
            </div>
        </div>`;
    }

    function cardChip(c) {
        return render3DCard(c);
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

    // Full-table deal ceremony: shuffle overlay + riffle sound + staggered fan
    function startDealSequence(v) {
        const container = document.getElementById('club-table-container');
        if (container) {
            const ov = document.createElement('div');
            ov.className = 'club-shuffle-overlay';
            ov.innerHTML = `
                <div class="shuffle-decks">
                    <div class="shuffle-deck left"></div>
                    <div class="shuffle-deck right"></div>
                    <div class="shuffle-caption">Shuffling</div>
                </div>`;
            container.appendChild(ov);
            setTimeout(() => ov.remove(), 1050);
        }
        if (window.ClubAudio) {
            window.ClubAudio.shuffle();
            const n = (v.game && Array.isArray(v.game.hand)) ? v.game.hand.length : 6;
            setTimeout(() => window.ClubAudio.dealFan(Math.min(n, 14)), 680);
        }
    }

    function render(v) {
        view = v;
        const t = v.table || {};
        const g = v.game || {};
        const mySeat = v.seat;

        // seats strip with active turn glowing gold halo
        const seatsEl = document.getElementById('club-seats');
        if (seatsEl) {
            const turn = (t.status === 'active') ? g.turn : null;
            const finish = v.finish || [];

            // First paint of a live table: deal ceremony (cards fan in with
            // stagger + flick sounds), so refreshing never feels static.
            if (firstLoad) {
                firstLoad = false;
                if (t.status === 'active') {
                    justStarted = true;
                    if (window.ClubAudio) {
                        const n = (g.hand && Array.isArray(g.hand)) ? g.hand.length : 6;
                        setTimeout(() => window.ClubAudio.dealFan(Math.min(n, 14)), 450);
                    }
                }
            }

            // waiting -> active: fire the shuffle + deal sequence once
            if (prevStatus === 'waiting' && t.status === 'active') {
                justStarted = true;
                prevCenterIds = new Set();
                startDealSequence(v);
            }
            // turn advanced: soft awareness tick (never for our own move sounds)
            if (turn !== null && turn !== undefined &&
                prevTurn !== null && turn !== prevTurn &&
                t.status === 'active' && window.ClubAudio) {
                window.ClubAudio.turn();
            }
            prevTurn = turn;
            prevStatus = t.status;

            seatsEl.innerHTML = (v.seats || []).map(s => {
                const isMe = s.seat_index === mySeat;
                const isTurn = s.seat_index === turn;
                const pos = finish.indexOf(s.seat_index);
                const hasCam = !!s.camera_active;
                const rulesOk = !!s.rules_read;

                return `<div class="seat-pod ${justStarted ? 'seat-pop' : ''} p-2.5 sm:p-3 border flex flex-col gap-1.5 transition-all ${isTurn ? 'is-active-turn bg-amber-950/80 border-amber-400 text-amber-200' : (isMe ? 'bg-indigo-950/70 border-indigo-500/40 text-indigo-200' : 'bg-slate-900/80 border-slate-800 text-slate-300')}">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-user-tie text-xs ${isTurn ? 'text-amber-400 animate-bounce' : 'text-slate-500'}"></i>
                        <div class="font-bold flex items-center gap-1.5 leading-none">
                            <span>${esc(s.username)}</span>
                            <span class="text-[9px] opacity-60">#${s.seat_index}</span>
                            ${pos >= 0 ? `<span class="ml-1 px-1 py-0.2 rounded bg-emerald-900 border border-emerald-500/40 text-[9px] text-emerald-300">#${pos + 1}</span>` : ''}
                        </div>
                        ${rulesOk 
                            ? '<span class="strict-rules-seal text-[8px] ml-auto"><i class="fa-solid fa-certificate"></i>RULES OK</span>' 
                            : '<span class="text-[8px] font-mono text-amber-400/80 px-1 py-0.2 rounded bg-amber-950/40 border border-amber-500/20 ml-auto">PENDING</span>'}
                    </div>
                    ${isTurn ? '<div class="text-[9px] text-amber-300 font-mono font-bold">THINKING...</div>' : ''}
                    ${hasCam ? `
                        <div class="player-cam-tile relative mt-1">
                            <div class="cam-live-indicator"><span class="pulse-dot"></span>LIVE CAM</div>
                            <video id="seat-cam-${s.seat_index}" autoplay muted playsinline class="w-full h-full object-cover rounded-lg"></video>
                        </div>
                    ` : ''}
                </div>`;
            }).join('') || '<span class="text-slate-600">No seats yet</span>';

            // Re-attach camera feeds (local + all inbound WebRTC streams) —
            // seats innerHTML is rebuilt on every render, so videos need
            // their srcObject restored each time.
            attachAllStreams();
            maybeRequestRemoteCameras();

            if (turn !== null && turn !== undefined) {
                const me = (v.seats || []).find(s => s.seat_index === mySeat);
                const whose = (v.seats || []).find(s => s.seat_index === turn);
                const hint = document.getElementById('club-turn-hint');
                if (hint) {
                    hint.textContent = (mySeat === turn) ? '★ YOUR TURN TO ACT ★' :
                        'Waiting for ' + (whose ? whose.username : '#' + turn);
                    hint.className = 'text-xs font-mono font-bold ' +
                        (mySeat === turn ? 'text-amber-400 animate-pulse' : 'text-slate-400');
                }
            }
        }

        const potEl = document.getElementById('club-pot');
        if (potEl) {
            const oldPot = parseInt(potEl.textContent, 10) || 0;
            const newPot = v.pot != null ? v.pot : 0;
            if (newPot > oldPot && window.ClubAudio) window.ClubAudio.chips();
            potEl.textContent = newPot;
        }
        const chip = document.getElementById('club-status-chip');
        if (chip) chip.textContent = t.status || '';

        renderControls(v);
        renderGame(v);
        renderLegal(v);
        justStarted = false;
    }

    let localCamStream = null;

    // ---------------- WebRTC mesh (camera share) ----------------
    // One outbound PC per peer while I share (I offer), one inbound PC per
    // peer while they share (they offer). Media is P2P; the socket only
    // relays SDP/ICE between two validated seats of the same table.
    const rtc = { out: {}, in: {}, streams: {}, pendingIce: {}, watchAsked: {} };
    const RTC_CONFIG = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };

    function myUid() {
        if (!view || view.seat === null || view.seat === undefined) return null;
        const s = (view.seats || []).find(x => x.seat_index === view.seat);
        return s ? s.user_id : null;
    }

    function otherSeatUids() {
        const me = myUid();
        return (view ? view.seats : [])
            .filter(s => s.user_id !== me)
            .map(s => s.user_id);
    }

    function sendRtc(toUid, kind, payload) {
        if (socket && socket.connected) {
            socket.emit('webrtc_signal', {
                table_id: C().tableId, to_user: toUid,
                kind: kind, payload: payload
            });
        }
    }

    function seatIndexForUid(uid) {
        if (!view) return null;
        const s = (view.seats || []).find(x => x.user_id === uid);
        return s ? s.seat_index : null;
    }

    function attachSeatStream(uid, stream) {
        const idx = seatIndexForUid(uid);
        if (idx === null) return;
        const el = document.getElementById(`seat-cam-${idx}`);
        if (el && el.srcObject !== stream) {
            el.srcObject = stream;
            el.play().catch(() => {});
        }
    }

    function attachAllStreams() {
        const me = myUid();
        if (localCamStream && me !== null) attachSeatStream(me, localCamStream);
        for (const uid in rtc.streams) attachSeatStream(Number(uid), rtc.streams[uid]);
    }

    function mySeat() { return view ? view.seat : null; }

    function closeInPeer(uid) {
        if (rtc.in[uid]) { try { rtc.in[uid].close(); } catch (e) {} delete rtc.in[uid]; }
        delete rtc.streams[uid];
        delete rtc.pendingIce[uid];
        const idx = seatIndexForUid(uid);
        if (idx !== null) {
            const el = document.getElementById(`seat-cam-${idx}`);
            if (el) el.srcObject = null;
        }
    }

    function ensureOutPeer(uid) {
        if (!localCamStream || rtc.out[uid]) return;
        const pc = new RTCPeerConnection(RTC_CONFIG);
        rtc.out[uid] = pc;
        localCamStream.getTracks().forEach(tr => pc.addTrack(tr, localCamStream));
        pc.onicecandidate = e => { if (e.candidate) sendRtc(uid, 'ice', e.candidate); };
        pc.onnegotiationneeded = async () => {
            try {
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                sendRtc(uid, 'offer', { type: pc.localDescription.type,
                                        sdp: pc.localDescription.sdp });
            } catch (e) { console.warn('rtc offer failed', e); }
        };
        pc.onconnectionstatechange = () => {
            if (['failed', 'closed'].includes(pc.connectionState)) {
                delete rtc.out[uid];
            }
        };
    }

    function makeInPeer(uid) {
        const pc = new RTCPeerConnection(RTC_CONFIG);
        rtc.in[uid] = pc;
        pc.onicecandidate = e => { if (e.candidate) sendRtc(uid, 'ice', e.candidate); };
        pc.ontrack = e => {
            rtc.streams[uid] = e.streams[0];
            attachSeatStream(uid, e.streams[0]);
        };
        pc.onconnectionstatechange = () => {
            if (pc.connectionState === 'failed') closeInPeer(uid);
        };
        return pc;
    }

    async function drainPendingIce(uid, pc) {
        const q = rtc.pendingIce[uid] || [];
        delete rtc.pendingIce[uid];
        for (const c of q) { try { await pc.addIceCandidate(c); } catch (e) {} }
    }

    async function handleRtcSignal(msg) {
        if (!msg || msg.table_id !== C().tableId) return;
        const from = Number(msg.from_user);
        if (from === myUid()) return;
        try {
            if (msg.kind === 'stop') { closeInPeer(from); return; }
            if (msg.kind === 'offer') {
                let pc = rtc.in[from];
                if (!pc) pc = makeInPeer(from);
                await pc.setRemoteDescription(new RTCSessionDescription(msg.payload));
                await drainPendingIce(from, pc);
                const ans = await pc.createAnswer();
                await pc.setLocalDescription(ans);
                sendRtc(from, 'answer', { type: pc.localDescription.type,
                                          sdp: pc.localDescription.sdp });
                return;
            }
            if (msg.kind === 'answer') {
                const pc = rtc.out[from];
                if (pc) {
                    await pc.setRemoteDescription(new RTCSessionDescription(msg.payload));
                    await drainPendingIce(from, pc);
                }
                return;
            }
            if (msg.kind === 'ice') {
                const pc = rtc.in[from] || rtc.out[from];
                if (pc && pc.remoteDescription) {
                    try { await pc.addIceCandidate(msg.payload); } catch (e) {}
                } else {
                    (rtc.pendingIce[from] = rtc.pendingIce[from] || []).push(msg.payload);
                }
            }
        } catch (e) { console.warn('rtc signal failed', e); }
    }

    function startOutMesh() {
        otherSeatUids().forEach(uid => ensureOutPeer(uid));
    }

    function stopOutMesh() {
        otherSeatUids().forEach(uid => sendRtc(uid, 'stop', null));
        for (const uid in rtc.out) { try { rtc.out[uid].close(); } catch (e) {} }
        rtc.out = {};
    }

    // Viewer side: if I see a remote seat sharing but have no inbound PC,
    // ask (once per peer) the sharer to negotiate a fresh offer to me.
    function maybeRequestRemoteCameras() {
        if (!socket || !socket.connected || !view) return;
        for (const s of (view.seats || [])) {
            if (!s.camera_active) continue;
            if (s.user_id === myUid()) continue;
            if (rtc.in[s.user_id]) continue;
            if (rtc.watchAsked[s.user_id]) continue;
            rtc.watchAsked[s.user_id] = true;
            socket.emit('camera_watch', { table_id: C().tableId });
        }
    }

    // ------------------------------------------------------------

    async function toggleCameraStream(v) {
        if (!v.my_rules_read) {
            ClubSection.toast('You must read and agree to strict tournament rules before sharing your camera!', false);
            const m = document.getElementById('modal-strict-rules');
            if (m) m.classList.remove('hidden');
            return;
        }

        if (v.my_camera_active) {
            // Stop camera: tell every peer to tear down, close outbound PCs
            stopOutMesh();
            if (localCamStream) {
                localCamStream.getTracks().forEach(t => t.stop());
                localCamStream = null;
            }
            try {
                await ClubSection.post(C().cameraUrl, { active: false });
                ClubSection.toast('Camera stopped', true);
            } catch (e) {
                ClubSection.toast(e.message, false);
            }
        } else {
            // Start camera
            try {
                localCamStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 320 }, height: { ideal: 240 } },
                    audio: false
                });
                await ClubSection.post(C().cameraUrl, { active: true });
                startOutMesh();
                if (window.ClubAudio) window.ClubAudio.deal();
                ClubSection.toast('🎥 Camera live! Sharing with table.', true);
            } catch (err) {
                ClubSection.toast('Camera access error: ' + err.message, false);
            }
        }
        refresh();
    }

    function renderControls(v) {
        const el = document.getElementById('club-controls');
        if (!el) return;
        const t = v.table || {};
        const seated = v.seat !== null && v.seat !== undefined;
        const btns = [];

        // Strict rules & Camera controls for seated players
        if (seated) {
            if (!v.my_rules_read) {
                btns.push(`<button id="btn-read-strict-rules" class="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-black text-xs font-mono shadow-md flex items-center gap-1.5"><i class="fa-solid fa-book-open"></i> Read Strict Rules</button>`);
                btns.push(`<button disabled class="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-500 text-xs font-mono flex items-center gap-1.5 cursor-not-allowed opacity-50" title="Must read rules first"><i class="fa-solid fa-video-slash"></i> Camera Locked</button>`);
            } else {
                btns.push(`<span class="px-3 py-1.5 rounded-xl bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 text-xs font-mono font-bold flex items-center gap-1.5"><i class="fa-solid fa-check-circle text-emerald-400"></i> Rules Verified</span>`);
                btns.push(`<button id="btn-toggle-camera" class="px-4 py-2 rounded-xl ${v.my_camera_active ? 'bg-rose-600 hover:bg-rose-500' : 'bg-blue-600 hover:bg-blue-500'} text-white font-bold text-xs font-mono shadow-md flex items-center gap-1.5 transition-all"><i class="fa-solid ${v.my_camera_active ? 'fa-video-slash' : 'fa-video'}"></i> ${v.my_camera_active ? 'Stop Camera' : 'Share Camera'}</button>`);
            }
        }

        if (t.status === 'waiting') {
            if (!seated) btns.push(`<button class="club-ctrl px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-900/30" data-url="${C().joinUrl}"><i class="fa-solid fa-chair mr-1.5"></i>Join Table</button>`);
            else {
                btns.push(`<button class="club-ctrl px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold" data-url="${C().leaveUrl}"><i class="fa-solid fa-door-open mr-1.5"></i>Leave</button>`);
                btns.push(`<button class="club-ctrl px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white text-xs font-bold shadow-xl shadow-amber-950/40" data-url="${C().startUrl}" data-sound="shuffle"><i class="fa-solid fa-play mr-1.5"></i>Start Match (${(v.seats || []).length}/${v.max_players || '?'} &bull; min ${v.min_players || '?'})</button>`);
            }
            btns.push(`<button class="club-ctrl px-3 py-2 rounded-xl bg-rose-950/50 hover:bg-rose-900/80 border border-rose-800 text-rose-300 text-xs font-bold" data-url="${C().abandonUrl}">Cancel Table</button>`);
        } else if (t.status === 'active') {
            if (!seated) btns.push(`<span class="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 text-xs font-mono"><i class="fa-solid fa-eye text-cyan-400 mr-1.5"></i>Spectating Table</span>`);
            btns.push(`<button class="club-ctrl px-3.5 py-2 rounded-xl bg-rose-950/60 hover:bg-rose-900 border border-rose-800 text-rose-200 text-xs font-bold" data-url="${C().abandonUrl}" data-confirm="Abandon the table in play? All escrowed stakes are refunded.">Abandon</button>`);
        } else {
            btns.push(`<span class="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 text-xs font-mono">Table ${esc(t.status)}</span>`);
        }
        el.innerHTML = btns.join('');

        // Wire strict rules button
        const rulesBtn = document.getElementById('btn-read-strict-rules');
        if (rulesBtn) {
            rulesBtn.addEventListener('click', () => {
                const m = document.getElementById('modal-strict-rules');
                if (m) m.classList.remove('hidden');
                if (window.ClubAudio) window.ClubAudio.hover();
            });
        }

        // Wire modal acknowledgment button
        const modalAckBtn = document.getElementById('modal-strict-ack-btn');
        if (modalAckBtn && !modalAckBtn._wired) {
            modalAckBtn._wired = true;
            modalAckBtn.addEventListener('click', async () => {
                try {
                    modalAckBtn.disabled = true;
                    await ClubSection.post(C().strictRulesUrl, {});
                    const m = document.getElementById('modal-strict-rules');
                    if (m) m.classList.add('hidden');
                    if (window.ClubAudio) window.ClubAudio.win();
                    ClubSection.toast('Strict Tournament Rules Acknowledged & Camera Unlocked!', true);
                    refresh();
                } catch (e) {
                    ClubSection.toast(e.message, false);
                } finally {
                    modalAckBtn.disabled = false;
                }
            });
        }

        // Wire camera toggle button
        const camBtn = document.getElementById('btn-toggle-camera');
        if (camBtn) {
            camBtn.addEventListener('click', () => toggleCameraStream(v));
        }

        el.querySelectorAll('.club-ctrl').forEach(b => {
            b.addEventListener('click', async () => {
                if (b.dataset.confirm && !window.confirm(b.dataset.confirm)) return;
                if (b.dataset.sound === 'shuffle' && window.ClubAudio) {
                    window.ClubAudio.shuffle();
                }
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
                <div class="text-center py-12 space-y-3">
                    <div class="w-16 h-16 rounded-3xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 text-2xl mx-auto shadow-xl animate-pulse">
                        <i class="fa-solid fa-hourglass-half"></i>
                    </div>
                    <div class="text-base font-bold text-white font-outfit">Waiting for Players to Sit</div>
                    <div class="text-xs text-slate-400 font-mono">
                        ${esc(v.game_name || '')} requires ${v.min_players || '?'}-${v.max_players || '?'} players &bull; ${(v.seats || []).length} seated
                    </div>
                    <div class="text-xs text-slate-500 font-mono max-w-lg mx-auto leading-relaxed pt-2">${esc(v.rules || '')}</div>
                </div>`;
            return;
        }
        if (t.status !== 'active') {
            el.innerHTML = `<div class="text-center py-10 text-slate-400 font-mono text-xs">Table closed (${esc(t.status)}).</div>`;
            return;
        }

        // Win ceremony: fanfare + coin pour + confetti burst over the felt
        if (g.over && !window._clubWinSoundFired) {
            window._clubWinSoundFired = true;
            if (window.ClubAudio) {
                window.ClubAudio.win();
                setTimeout(() => window.ClubAudio.coins(), 750);
            }
            if (typeof ClubSection !== 'undefined' && ClubSection.confettiBurst) {
                ClubSection.confettiBurst(window.innerWidth / 2, window.innerHeight / 3, 140);
            }
        } else if (!g.over) {
            window._clubWinSoundFired = false;
        }

        const panels = [];

        if (g.over) {
            panels.push(`<div class="px-5 py-4 rounded-2xl bg-gradient-to-r from-emerald-950 via-teal-950 to-emerald-950 border border-emerald-500/50 text-emerald-200 font-mono text-sm font-bold text-center shadow-xl flex items-center justify-center gap-3">
                <i class="fa-solid fa-trophy text-amber-400 text-xl animate-bounce"></i>
                <span>Match Over &bull; Settlement Processed &bull; Zero-Sum Balances Distributed</span>
            </div>`);
        }

        // 1. Center Table Cards Surface (Tricks / Community / Piles)
        // Diff against the previous render: only genuinely new cards fly in,
        // so 2.5s polling never re-throws the whole pile.
        const centerKeys = ['trick', 'pile', 'discard', 'community', 'table_cards', 'market', 'center', 'face_up', 'revealed', 'top', 'trump', 'current'];
        const activeCenter = centerKeys.filter(k => g[k] !== undefined && g[k] !== null);
        const nextCenterIds = new Set();
        let newCenterCount = 0;

        const centerAnim = (id) => {
            nextCenterIds.add(id);
            if (prevCenterIds.has(id)) return '';      // seen before: stay put
            newCenterCount++;
            return 'anim-card-throw';
        };

        let centerCardsHtml = '';
        activeCenter.forEach(k => {
            const val = g[k];
            if (Array.isArray(val) && val.length > 0) {
                const isCardList = val.every(x => typeof x === 'string' && x.length <= 4);
                const isObjList = val.every(x => typeof x === 'object' && x !== null && x.card);
                centerCardsHtml += `
                <div class="p-3.5 rounded-2xl bg-black/40 border border-amber-500/20 backdrop-blur-md">
                    <div class="text-[10px] font-mono uppercase text-amber-400/80 font-bold mb-2 flex items-center justify-between">
                        <span>${esc(k.replace(/_/g, ' '))} (${val.length})</span>
                    </div>
                    <div class="flex flex-wrap gap-2 justify-center items-center">
                        ${isCardList ? val.map((c, idx) => {
                            const angle = ((idx % 7) - 3) * 3;
                            return render3DCard(c, {
                                anim: centerAnim(k + ':' + c + ':' + idx),
                                style: `transform: rotate(${angle}deg); margin: 0 -4px;`
                            });
                        }).join('') : (isObjList ? val.map((entry, idx) => {
                            const angle = ((idx % 7) - 3) * 4;
                            const who = (v.seats || []).find(s => s.seat_index == entry.seat);
                            return `
                            <div class="flex flex-col items-center">
                                <span class="text-[9px] font-mono text-slate-400 mb-1">${esc(who ? who.username : '#' + entry.seat)}</span>
                                ${render3DCard(entry.card, { anim: centerAnim(k + ':' + entry.card + '@' + entry.seat + ':' + idx), style: `transform: rotate(${angle}deg);` })}
                            </div>`;
                        }).join('') : `<div class="font-mono text-xs text-slate-300">${esc(JSON.stringify(val))}</div>`)}
                    </div>
                </div>`;
            } else if (typeof val === 'string' && val.length <= 4) {
                centerCardsHtml += `
                <div class="p-3 rounded-2xl bg-black/40 border border-amber-500/20 backdrop-blur-md flex flex-col items-center">
                    <span class="text-[10px] font-mono text-amber-400/80 font-bold mb-1">${esc(k)}</span>
                    ${render3DCard(val, { anim: centerAnim(k + ':' + val) })}
                </div>`;
            } else if (val !== undefined && val !== null) {
                centerCardsHtml += `
                <div class="px-3.5 py-2 rounded-xl bg-black/40 border border-slate-800 font-mono text-xs flex items-center gap-2">
                    <span class="text-slate-400">${esc(k)}:</span>
                    <strong class="text-amber-300">${esc(typeof val === 'object' ? JSON.stringify(val) : val)}</strong>
                </div>`;
            }
        });

        // A card landed on the felt from someone else's move: whoosh it in.
        if (newCenterCount > 0 && (Date.now() - lastLocalMoveAt) > 900 && window.ClubAudio) {
            window.ClubAudio.throw();
        }
        prevCenterIds = nextCenterIds;

        if (centerCardsHtml) {
            panels.push(`
            <div class="space-y-2">
                <div class="flex items-center justify-between text-xs font-mono text-amber-300 font-bold px-1">
                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-diamond text-amber-400"></i> TABLE FELT SURFACE</span>
                    <span class="text-[10px] text-slate-400">POT: <strong class="text-amber-300">${v.pot || 0}</strong> COINS</span>
                </div>
                <div class="center-trick-surface flex flex-wrap gap-4 items-center justify-center p-6 rounded-3xl min-h-[170px]">
                    ${centerCardsHtml}
                </div>
            </div>`);
        }

        // 2. Player's Own Hand Fanned Out
        if (g.hand && Array.isArray(g.hand)) {
            const hand = g.hand;
            // Map legal actions targeting cards
            const legalCardMoves = new Map();
            (v.legal || []).forEach((a, idx) => {
                if (a && a.card) legalCardMoves.set(a.card, idx);
                else if (a && Array.isArray(a.cards)) a.cards.forEach(c => legalCardMoves.set(c, idx));
            });

            const mid = (hand.length - 1) / 2;
            const handCardsHtml = hand.map((card, idx) => {
                const rot = (idx - mid) * 3.2;
                const transY = Math.abs(idx - mid) * 2.8;
                const actIdx = legalCardMoves.get(card);
                const isPlayable = actIdx !== undefined;

                return render3DCard(card, {
                    playable: isPlayable,
                    actionIndex: actIdx,
                    style: `--rest-rot:${rot}deg; transform: rotate(${rot}deg) translateY(${transY}px); z-index: ${idx + 10};` +
                        (justStarted ? ` --deal-delay:${(idx * 0.07).toFixed(2)}s;` : '')
                });
            }).join('');

            panels.push(`
            <div class="space-y-1">
                <div class="flex items-center justify-between px-2 text-xs font-mono">
                    <span class="text-slate-300 font-bold flex items-center gap-2">
                        <i class="fa-solid fa-hand text-indigo-400"></i> YOUR HAND (${hand.length} CARDS)
                    </span>
                    <span class="text-[10px] text-slate-500">Click any highlighted card to play</span>
                </div>
                <div class="player-hand-fanned ${justStarted ? 'deal-stagger' : ''} px-4" id="club-fanned-hand">
                    ${handCardsHtml}
                </div>
            </div>`);
        }

        // 3. Opponent Counts and Round Scores
        if (g.counts || (g.scores && Object.keys(g.scores).length)) {
            panels.push(`
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                ${g.counts ? `
                <div class="p-3 rounded-2xl bg-black/40 border border-slate-800">
                    <div class="text-[10px] text-slate-500 uppercase font-bold mb-2">Cards In Hand</div>
                    <div class="flex flex-wrap gap-2">
                        ${Object.entries(g.counts).map(([seat, n]) => {
                            const who = (v.seats || []).find(s => s.seat_index == seat);
                            const mine = seat == v.seat;
                            return `<span class="px-2.5 py-1 rounded-xl border text-[11px] ${mine ? 'bg-indigo-950 border-indigo-500/50 text-indigo-200 font-bold' : 'bg-slate-900 border-slate-800 text-slate-300'}">
                                ${esc(who ? who.username : '#' + seat)}: <strong class="text-white ml-1">${esc(n)}</strong>
                            </span>`;
                        }).join('')}
                    </div>
                </div>` : ''}

                ${g.scores && Object.keys(g.scores).length ? `
                <div class="p-3 rounded-2xl bg-black/40 border border-slate-800">
                    <div class="text-[10px] text-slate-500 uppercase font-bold mb-2">Scores / Points</div>
                    <div class="flex flex-wrap gap-2">
                        ${Object.entries(g.scores).map(([seat, sc]) => {
                            const who = (v.seats || []).find(s => s.seat_index == seat);
                            return `<span class="px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-[11px]">
                                ${esc(who ? who.username : '#' + seat)}: <strong class="text-cyan-300 ml-1">${esc(sc)}</strong>
                            </span>`;
                        }).join('')}
                    </div>
                </div>` : ''}
            </div>`);
        }

        // 4. Game Log
        if (g.log && g.log.length) {
            panels.push(`
            <div class="p-3.5 rounded-2xl bg-black/40 border border-slate-800 font-mono text-[11px]">
                <div class="text-[10px] text-slate-500 uppercase font-bold mb-2 flex items-center justify-between">
                    <span>LIVE TABLE LOG</span>
                    <i class="fa-solid fa-scroll text-slate-600"></i>
                </div>
                <div class="max-h-32 overflow-y-auto space-y-1 text-slate-300 scrollbar-thin">
                    ${g.log.slice().reverse().map(l => {
                        const who = (v.seats || []).find(s => s.seat_index == l.seat);
                        return `<div><span class="text-amber-400/80 font-bold">${esc(who ? who.username : (l.seat != null ? '#' + l.seat : 'TABLE'))}:</span> ${esc(l.text)}</div>`;
                    }).join('')}
                </div>
            </div>`);
        }

        el.innerHTML = panels.join('') || '<div class="text-slate-500 font-mono text-xs text-center py-6">Waiting for state...</div>';

        // Connect click-to-play for fanned cards in player's hand
        el.querySelectorAll('.player-hand-fanned .playing-card-3d.is-playable').forEach(cardEl => {
            cardEl.addEventListener('click', () => {
                const actIdx = parseInt(cardEl.dataset.actionIndex, 10);
                const legalActs = Array.isArray(v.legal) ? v.legal : [];
                if (!isNaN(actIdx) && legalActs[actIdx]) {
                    sendMove(legalActs[actIdx]);
                }
            });
        });
    }

    function renderLegal(v) {
        const el = document.getElementById('club-legal');
        if (!el) return;
        const legal = Array.isArray(v.legal) ? v.legal : [];
        if (v.seat === null || v.seat === undefined || v.table.status !== 'active') {
            el.innerHTML = '<span class="text-slate-500 text-xs font-mono">Not seated at this table.</span>';
            return;
        }
        if (!legal.length) {
            el.innerHTML = '<span class="text-slate-400 text-xs font-mono flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-slate-600 animate-ping"></span>Waiting for turn or game has completed.</span>';
            return;
        }

        el.innerHTML = legal.map((a, i) => {
            const isSlap = a.action === 'slap' || a.action === 'challenge' || a.action === 'grab';
            const btnClass = isSlap
                ? 'club-move px-6 py-3 rounded-2xl bg-gradient-to-r from-rose-600 via-amber-600 to-rose-600 hover:from-rose-500 hover:to-amber-500 text-white font-extrabold text-sm uppercase tracking-wider shadow-xl shadow-rose-950/60 border border-amber-400/80 animate-pulse hover:scale-105 active:scale-95 transition-all flex items-center gap-2'
                : 'club-move px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-indigo-600 border border-slate-700 hover:border-indigo-400 text-white text-xs font-mono font-bold transition-all shadow-md';

            const icon = isSlap ? '<i class="fa-solid fa-bolt text-amber-300"></i> ' : '';
            return `<button class="${btnClass}" data-i="${i}">${icon}${esc(actionLabel(a))}</button>`;
        }).join('');

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

    // Move rejected: show the error, and pop the strict-rules modal when the
    // server says the player has not acknowledged the rules yet.
    function surfaceMoveError(msg) {
        showErr(msg);
        if (msg && /Strict Rules/i.test(msg)) {
            const m = document.getElementById('modal-strict-rules');
            if (m) m.classList.remove('hidden');
        }
    }

    async function sendMove(action) {
        showErr(null);
        lastLocalMoveAt = Date.now();
        // Sound Dispatch
        if (window.ClubAudio) {
            const act = action && action.action;
            if (act === 'slap' || act === 'challenge' || act === 'grab') {
                window.ClubAudio.slap();
                const feltEl = document.querySelector('.casino-table-felt');
                if (feltEl) {
                    feltEl.classList.remove('table-slap-impact');
                    void feltEl.offsetWidth; // force reflow
                    feltEl.classList.add('table-slap-impact');
                }
            } else if (act === 'play' || act === 'declare' || act === 'draw_pass') {
                window.ClubAudio.throw();
            } else if (act === 'bet' || act === 'raise') {
                window.ClubAudio.chips();
            } else {
                window.ClubAudio.deal();
            }
        }
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
                    surfaceMoveError((ack && ack.error) || 'Move rejected');
                }
                return;
            }
            const data = await ClubSection.post(C().moveUrl, { action });
            if (data) {
                if (data.view) render(data.view);
                if (data.settlement) showSettlement(data.settlement);
            }
        } catch (e) {
            surfaceMoveError(e.message);
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
        socket.on('webrtc_signal', (msg) => { handleRtcSignal(msg); });
        socket.on('camera_watch_from', (d) => {
            if (d && d.table_id === C().tableId &&
                d.user_id !== myUid() && localCamStream) {
                ensureOutPeer(Number(d.user_id));
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
