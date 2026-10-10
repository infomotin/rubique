/* Card Club client: HTTP API helpers, group forms, live table play.
 * Transport strategy: Socket.IO websocket push when available, automatic
 * fallback to 2.5s state polling - the game stays fully playable either way
 * because every move also has an HTTP endpoint. */

// ============================================================================
// ClubCards: High-Fidelity Classical Graphical Casino Card Art & Engine
// Authentic two-way reversible royal portraits (King, Queen, Jack),
// grand baroque engraved master Aces, and Bicycle-standard pip geometry.
// ============================================================================
const ClubCards = (() => {
    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    const SUITS = {
        'S': { sym: '♠', red: false, name: 'Spades' },
        'H': { sym: '♥', red: true,  name: 'Hearts' },
        'D': { sym: '♦', red: true,  name: 'Diamonds' },
        'C': { sym: '♣', red: false, name: 'Clubs' }
    };

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
        return {
            suit: s,
            symbol: SUITS[s].sym,
            rank: r,
            isRed: SUITS[s].red,
            name: SUITS[s].name
        };
    }

    const PIP_LAYOUTS = {
        '2': [
            { x: 50, y: 22, flip: false },
            { x: 50, y: 78, flip: true }
        ],
        '3': [
            { x: 50, y: 22, flip: false },
            { x: 50, y: 50, flip: false },
            { x: 50, y: 78, flip: true }
        ],
        '4': [
            { x: 28, y: 22, flip: false },
            { x: 72, y: 22, flip: false },
            { x: 28, y: 78, flip: true },
            { x: 72, y: 78, flip: true }
        ],
        '5': [
            { x: 28, y: 22, flip: false },
            { x: 72, y: 22, flip: false },
            { x: 50, y: 50, flip: false },
            { x: 28, y: 78, flip: true },
            { x: 72, y: 78, flip: true }
        ],
        '6': [
            { x: 28, y: 22, flip: false },
            { x: 72, y: 22, flip: false },
            { x: 28, y: 50, flip: false },
            { x: 72, y: 50, flip: false },
            { x: 28, y: 78, flip: true },
            { x: 72, y: 78, flip: true }
        ],
        '7': [
            { x: 28, y: 22, flip: false },
            { x: 72, y: 22, flip: false },
            { x: 50, y: 36, flip: false },
            { x: 28, y: 50, flip: false },
            { x: 72, y: 50, flip: false },
            { x: 28, y: 78, flip: true },
            { x: 72, y: 78, flip: true }
        ],
        '8': [
            { x: 28, y: 22, flip: false },
            { x: 72, y: 22, flip: false },
            { x: 50, y: 36, flip: false },
            { x: 28, y: 50, flip: false },
            { x: 72, y: 50, flip: false },
            { x: 50, y: 64, flip: true },
            { x: 28, y: 78, flip: true },
            { x: 72, y: 78, flip: true }
        ],
        '9': [
            { x: 28, y: 20, flip: false },
            { x: 72, y: 20, flip: false },
            { x: 28, y: 39, flip: false },
            { x: 72, y: 39, flip: false },
            { x: 50, y: 50, flip: false },
            { x: 28, y: 61, flip: true },
            { x: 72, y: 61, flip: true },
            { x: 28, y: 80, flip: true },
            { x: 72, y: 80, flip: true }
        ],
        '10': [
            { x: 28, y: 19, flip: false },
            { x: 72, y: 19, flip: false },
            { x: 50, y: 30, flip: false },
            { x: 28, y: 40, flip: false },
            { x: 72, y: 40, flip: false },
            { x: 28, y: 60, flip: true },
            { x: 72, y: 60, flip: true },
            { x: 50, y: 70, flip: true },
            { x: 28, y: 81, flip: true },
            { x: 72, y: 81, flip: true }
        ]
    };

    function getPipsHtml(rank, symbol, isRed) {
        const layout = PIP_LAYOUTS[rank];
        if (!layout) return '';
        return layout.map(p => {
            const flipClass = p.flip ? ' pip-flipped' : '';
            return `<span class="card-pip-item${flipClass}" style="left:${p.x}%; top:${p.y}%;">${symbol}</span>`;
        }).join('');
    }

    function getAceSpadesSvg() {
        return `<svg class="card-ace-svg" viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
            <defs>
                <radialGradient id="spade-glow" cx="50%" cy="45%" r="60%">
                    <stop offset="0%" stop-color="#334155" />
                    <stop offset="100%" stop-color="#090d16" />
                </radialGradient>
                <linearGradient id="gold-foil" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#fef08a" />
                    <stop offset="50%" stop-color="#d97706" />
                    <stop offset="100%" stop-color="#78350f" />
                </linearGradient>
            </defs>
            <g stroke="url(#gold-foil)" fill="none" stroke-width="1.2" stroke-linecap="round" opacity="0.85">
                <path d="M 50,8 C 42,4 32,8 35,16 C 37,21 44,20 48,16" />
                <path d="M 50,8 C 58,4 68,8 65,16 C 63,21 56,20 52,16" />
                <circle cx="50" cy="7" r="1.5" fill="#f59e0b" stroke="none" />
                <path d="M 24,35 C 15,40 12,56 20,66 C 26,74 34,70 32,62 C 30,56 22,57 20,63" />
                <path d="M 76,35 C 85,40 88,56 80,66 C 74,74 66,70 68,62 C 70,56 78,57 80,63" />
                <path d="M 28,82 C 18,88 20,104 32,106 C 40,108 44,98 38,94" />
                <path d="M 72,82 C 82,88 80,104 68,106 C 60,108 56,98 62,94" />
            </g>
            <g filter="drop-shadow(0 3px 5px rgba(0,0,0,0.45))">
                <path d="M 50,18 C 48,27 22,54 22,72 C 22,86 34,92 44,86 C 47,84 48,81 50,77 C 52,81 53,84 56,86 C 66,92 78,86 78,72 C 78,54 52,27 50,18 Z" fill="url(#spade-glow)" stroke="#020617" stroke-width="1.5" />
                <path d="M 47,75 L 43,98 C 40,100 36,101 34,102 L 66,102 C 64,101 60,100 57,98 L 53,75 Z" fill="url(#spade-glow)" stroke="#020617" stroke-width="1.2" />
            </g>
            <g stroke="#94a3b8" fill="none" stroke-width="0.6" opacity="0.45">
                <ellipse cx="50" cy="58" rx="14" ry="16" />
                <ellipse cx="50" cy="58" rx="9" ry="11" />
                <path d="M 50,42 L 50,74 M 36,58 L 64,58 M 40,47 L 60,69 M 40,69 L 60,47" />
                <circle cx="50" cy="58" r="3" fill="#f59e0b" stroke="#78350f" stroke-width="0.5" />
            </g>
            <g>
                <path d="M 22,112 Q 50,107 78,112 L 75,121 Q 50,116 25,121 Z" fill="#fef3c7" stroke="#b45309" stroke-width="0.75" />
                <text x="50" y="118.5" font-family="'Cinzel', 'Playfair Display', Georgia, serif" font-size="5.2" font-weight="900" fill="#78350f" text-anchor="middle" letter-spacing="1.8">RUBIQUE CLUB</text>
            </g>
        </svg>`;
    }

    function getAceHeartsSvg() {
        return `<svg class="card-ace-svg" viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
            <defs>
                <radialGradient id="heart-glow" cx="45%" cy="40%" r="65%">
                    <stop offset="0%" stop-color="#ef4444" />
                    <stop offset="70%" stop-color="#b91c1c" />
                    <stop offset="100%" stop-color="#7f1d1d" />
                </radialGradient>
                <linearGradient id="gold-heart-foil" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#fef08a" />
                    <stop offset="50%" stop-color="#d97706" />
                    <stop offset="100%" stop-color="#92400e" />
                </linearGradient>
            </defs>
            <g stroke="url(#gold-heart-foil)" fill="none" stroke-width="1.2" stroke-linecap="round" opacity="0.85">
                <path d="M 50,14 C 42,7 30,12 34,22 C 37,28 44,26 48,20" />
                <path d="M 50,14 C 58,7 70,12 66,22 C 63,28 56,26 52,20" />
                <path d="M 22,46 C 14,54 14,72 24,80 C 32,86 38,78 34,70" />
                <path d="M 78,46 C 86,54 86,72 76,80 C 68,86 62,78 66,70" />
                <path d="M 44,17 L 46,12 L 50,15 L 54,12 L 56,17 Z" fill="#f59e0b" stroke="#78350f" stroke-width="0.5" />
            </g>
            <g filter="drop-shadow(0 3px 6px rgba(185,28,28,0.4))">
                <path d="M 50,96 C 32,78 18,63 18,44 C 18,29 30,18 45,18 C 47,18 49,19 50,21 C 51,19 53,18 55,18 C 70,18 82,29 82,44 C 82,63 68,78 50,96 Z" fill="url(#heart-glow)" stroke="#991b1b" stroke-width="1.2" />
            </g>
            <g stroke="#fecaca" fill="none" stroke-width="0.6" opacity="0.45">
                <ellipse cx="50" cy="48" rx="14" ry="12" />
                <ellipse cx="50" cy="48" rx="8" ry="7" />
                <path d="M 50,34 L 50,62 M 36,48 L 64,48 M 41,39 L 59,57 M 41,57 L 59,39" />
                <circle cx="50" cy="48" r="2.5" fill="#fef08a" stroke="#b45309" stroke-width="0.5" />
            </g>
            <g>
                <path d="M 24,108 Q 50,103 76,108 L 73,117 Q 50,112 27,117 Z" fill="#fef3c7" stroke="#b45309" stroke-width="0.75" />
                <text x="50" y="114.5" font-family="'Cinzel', 'Playfair Display', Georgia, serif" font-size="5" font-weight="900" fill="#78350f" text-anchor="middle" letter-spacing="1.5">ROYAL HEARTS</text>
            </g>
        </svg>`;
    }

    function getAceDiamondsSvg() {
        return `<svg class="card-ace-svg" viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
            <defs>
                <radialGradient id="diam-glow" cx="50%" cy="50%" r="65%">
                    <stop offset="0%" stop-color="#f87171" />
                    <stop offset="60%" stop-color="#dc2626" />
                    <stop offset="100%" stop-color="#991b1b" />
                </radialGradient>
                <linearGradient id="gold-diam-foil" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#fef08a" />
                    <stop offset="50%" stop-color="#d97706" />
                    <stop offset="100%" stop-color="#78350f" />
                </linearGradient>
            </defs>
            <g stroke="url(#gold-diam-foil)" fill="none" stroke-width="1.2" stroke-linecap="round" opacity="0.85">
                <path d="M 50,12 C 40,6 28,14 34,26 C 38,32 46,28 48,22" />
                <path d="M 50,12 C 60,6 72,14 66,26 C 62,32 54,28 52,22" />
                <path d="M 20,46 C 10,54 10,72 20,80 C 28,86 34,78 30,72" />
                <path d="M 80,46 C 90,54 90,72 80,80 C 72,86 66,78 70,72" />
            </g>
            <g filter="drop-shadow(0 3px 6px rgba(220,38,38,0.4))">
                <polygon points="50,18 84,58 50,98 16,58" fill="url(#diam-glow)" stroke="#7f1d1d" stroke-width="1.2" />
                <polygon points="50,18 50,98 32,58" fill="#fca5a5" opacity="0.3" />
                <polygon points="50,18 84,58 50,58" fill="#fee2e2" opacity="0.25" />
                <polygon points="16,58 50,58 50,98" fill="#7f1d1d" opacity="0.35" />
                <polygon points="50,34 68,58 50,82 32,58" fill="#ef4444" stroke="#fecaca" stroke-width="0.8" opacity="0.6" />
                <circle cx="50" cy="58" r="3.5" fill="#ffffff" opacity="0.8" />
            </g>
            <g>
                <path d="M 22,110 Q 50,105 78,110 L 75,119 Q 50,114 25,119 Z" fill="#fef3c7" stroke="#b45309" stroke-width="0.75" />
                <text x="50" y="116.5" font-family="'Cinzel', 'Playfair Display', Georgia, serif" font-size="5" font-weight="900" fill="#78350f" text-anchor="middle" letter-spacing="1.5">ROYAL DIAMOND</text>
            </g>
        </svg>`;
    }

    function getAceClubsSvg() {
        return `<svg class="card-ace-svg" viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
            <defs>
                <radialGradient id="club-glow" cx="48%" cy="42%" r="65%">
                    <stop offset="0%" stop-color="#334155" />
                    <stop offset="70%" stop-color="#0f172a" />
                    <stop offset="100%" stop-color="#020617" />
                </radialGradient>
                <linearGradient id="gold-club-foil" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#fef08a" />
                    <stop offset="50%" stop-color="#d97706" />
                    <stop offset="100%" stop-color="#78350f" />
                </linearGradient>
            </defs>
            <g stroke="url(#gold-club-foil)" fill="none" stroke-width="1.2" stroke-linecap="round" opacity="0.85">
                <path d="M 50,10 C 40,5 28,12 34,22 C 38,28 46,26 48,20" />
                <path d="M 50,10 C 60,5 72,12 66,22 C 62,28 54,26 52,20" />
                <path d="M 20,44 C 10,52 10,70 20,78 C 28,84 34,76 30,70" />
                <path d="M 80,44 C 90,52 90,70 80,78 C 72,84 66,76 70,70" />
            </g>
            <g filter="drop-shadow(0 3px 5px rgba(0,0,0,0.45))">
                <circle cx="50" cy="40" r="19" fill="url(#club-glow)" stroke="#020617" stroke-width="1.2" />
                <circle cx="34" cy="62" r="19" fill="url(#club-glow)" stroke="#020617" stroke-width="1.2" />
                <circle cx="66" cy="62" r="19" fill="url(#club-glow)" stroke="#020617" stroke-width="1.2" />
                <circle cx="50" cy="54" r="14" fill="url(#club-glow)" />
                <path d="M 47,66 L 43,96 C 40,98 35,99 33,100 L 67,100 C 65,99 60,98 57,96 L 53,66 Z" fill="url(#club-glow)" stroke="#020617" stroke-width="1.2" />
            </g>
            <g stroke="#94a3b8" fill="none" stroke-width="0.6" opacity="0.45">
                <circle cx="50" cy="40" r="8" />
                <circle cx="34" cy="62" r="8" />
                <circle cx="66" cy="62" r="8" />
                <circle cx="50" cy="54" r="4" fill="#f59e0b" stroke="#78350f" stroke-width="0.5" />
            </g>
            <g>
                <path d="M 22,110 Q 50,105 78,110 L 75,119 Q 50,114 25,119 Z" fill="#fef3c7" stroke="#b45309" stroke-width="0.75" />
                <text x="50" y="116.5" font-family="'Cinzel', 'Playfair Display', Georgia, serif" font-size="5" font-weight="900" fill="#78350f" text-anchor="middle" letter-spacing="1.5">ROYAL CLUB</text>
            </g>
        </svg>`;
    }

    function getAceSvg(suit, symbol, isRed) {
        if (suit === 'S') return getAceSpadesSvg();
        if (suit === 'H') return getAceHeartsSvg();
        if (suit === 'D') return getAceDiamondsSvg();
        return getAceClubsSvg();
    }

    function getKingSvg(suit, symbol, isRed) {
        const crownFill = !isRed ? '#f43f5e' : '#f59e0b';
        const tunicPrimary = !isRed ? '#0d9488' : '#dc2626';
        const tunicSecondary = !isRed ? '#f43f5e' : '#ea580c';
        const tabletBg = !isRed ? '#0d9488' : '#fef08a';
        const suitColor = !isRed ? '#111827' : '#dc2626';
        const clipId = `k-split-${suit}-${Math.random().toString(36).substr(2, 6)}`;
        const halfId = `k-half-${suit}-${Math.random().toString(36).substr(2, 6)}`;
        
        const half = `
            <rect x="22" y="24" width="56" height="60" fill="${tunicSecondary}" rx="1" />
            <rect x="42" y="32" width="36" height="52" fill="${tunicPrimary}" rx="1" />
            <rect x="70" y="8" width="6" height="68" fill="#e2e8f0" stroke="#111827" stroke-width="1.1" />
            <rect x="67" y="22" width="12" height="4" fill="#f59e0b" stroke="#111827" stroke-width="1" rx="1" />
            <circle cx="73" cy="7" r="2.2" fill="#f59e0b" stroke="#111827" stroke-width="1" />
            <line x1="73" y1="26" x2="73" y2="76" stroke="#94a3b8" stroke-width="1" />
            <polygon points="48,8 45,20 66,20 63,12 56,18 53,8" fill="${crownFill}" stroke="#111827" stroke-width="1.2" stroke-linejoin="round" />
            <circle cx="48" cy="7" r="1.8" fill="#f59e0b" stroke="#111827" stroke-width="1" />
            <circle cx="53" cy="7" r="1.8" fill="#f59e0b" stroke="#111827" stroke-width="1" />
            <circle cx="63" cy="11" r="1.8" fill="#f59e0b" stroke="#111827" stroke-width="1" />
            <path d="M 45,20 C 47,30 50,42 58,46 C 68,50 74,40 76,46 C 78,52 74,62 70,68 C 65,72 58,68 54,62" fill="#f59e0b" stroke="#111827" stroke-width="1.2" stroke-linecap="round" />
            <path d="M 48,22 C 50,32 54,42 62,44 C 70,46 74,42 76,48" fill="none" stroke="#111827" stroke-width="1" stroke-linecap="round" />
            <path d="M 45,20 L 35,20 L 35,32 L 38,32 C 40,34 40,38 37,39 L 37,42 C 41,45 44,48 44,56 L 54,56 C 54,46 48,40 48,38 L 47,20 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" stroke-linejoin="round" />
            <line x1="39" y1="24" x2="45" y2="24" stroke="#111827" stroke-width="1.5" stroke-linecap="round" />
            <path d="M 39,27 Q 42,30 45,27" fill="none" stroke="#111827" stroke-width="1.3" stroke-linecap="round" />
            <path d="M 33,35 C 36,33 42,33 46,36 C 42,42 34,42 33,35 Z" fill="#f59e0b" stroke="#111827" stroke-width="1" stroke-linejoin="round" />
            <path d="M 36,40 C 33,48 37,56 46,54 C 44,49 42,44 42,40 Z" fill="#f59e0b" stroke="#111827" stroke-width="1.1" stroke-linejoin="round" />
            <path d="M 18,66 C 18,52 24,46 38,46 L 42,56 C 40,62 34,68 22,70 Z" fill="${tunicPrimary}" stroke="#111827" stroke-width="1.2" />
            <path d="M 48,46 C 56,46 64,50 64,66 L 48,66 Z" fill="${tunicPrimary}" stroke="#111827" stroke-width="1.2" />
            <path d="M 42,46 L 42,78 L 48,78 L 48,46 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" />
            <polygon points="42,48 48,51 42,54" fill="#111827" />
            <polygon points="48,54 42,57 48,60" fill="#111827" />
            <polygon points="42,60 48,63 42,66" fill="#111827" />
            <polygon points="48,66 42,69 48,72" fill="#111827" />
            <polygon points="42,72 48,75 42,78" fill="#111827" />
            <g transform="translate(23, 27)">
                <polygon points="0,-13 13,0 0,13 -13,0" fill="${tabletBg}" stroke="#111827" stroke-width="1.3" />
                <polygon points="0,-9 9,0 0,9 -9,0" fill="none" stroke="#ffffff" stroke-width="0.8" opacity="0.6" />
                <text x="0" y="4.5" text-anchor="middle" font-size="12" font-weight="900" fill="${suitColor}">${symbol}</text>
            </g>
            <path d="M 17,39 C 17,34 21,30 26,31 C 25,35 23,37 24,40 C 22,39 21,42 22,45 L 19,45 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M 68,64 C 70,68 72,74 72,78 C 70,77 69,74 68,75 C 67,74 66,76 65,74 L 64,68 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
        `;

        return `<svg class="card-court-svg" viewBox="0 0 100 146" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
            <defs>
                <clipPath id="${clipId}">
                    <polygon points="0,0 100,0 100,60 0,86" />
                </clipPath>
            </defs>
            <g clip-path="url(#${clipId})">
                ${half}
            </g>
            <g transform="rotate(180, 50, 73)" clip-path="url(#${clipId})">
                ${half}
            </g>
            <line x1="0" y1="86" x2="100" y2="60" stroke="#111827" stroke-width="1.3" stroke-linecap="round" />
        </svg>`;
    }

    function getQueenSvg(suit, symbol, isRed) {
        const crownFill = isRed ? '#0d9488' : '#f59e0b';
        const tunicPrimary = isRed ? '#0d9488' : '#1e293b';
        const tunicSecondary = isRed ? '#f43f5e' : '#0284c7';
        const blockAccent = isRed ? '#fb923c' : '#f59e0b';
        const suitColor = isRed ? '#e11d48' : '#111827';
        const clipId = `q-split-${suit}-${Math.random().toString(36).substr(2, 6)}`;
        
        const half = `
            <rect x="22" y="24" width="56" height="60" fill="${tunicSecondary}" rx="1" />
            <rect x="22" y="52" width="28" height="32" fill="${blockAccent}" rx="1" />
            <polygon points="46,14 43,26 62,26 60,18 53,24 51,14" fill="${crownFill}" stroke="#111827" stroke-width="1.2" stroke-linejoin="round" />
            <circle cx="46" cy="13" r="1.8" fill="#f59e0b" stroke="#111827" stroke-width="1" />
            <circle cx="51" cy="13" r="1.8" fill="#f59e0b" stroke="#111827" stroke-width="1" />
            <circle cx="60" cy="17" r="1.8" fill="#f59e0b" stroke="#111827" stroke-width="1" />
            <path d="M 43,26 C 45,35 48,46 56,48 C 65,50 72,44 76,48 C 80,52 74,62 70,68 C 65,74 58,70 54,64" fill="#f59e0b" stroke="#111827" stroke-width="1.2" stroke-linecap="round" />
            <path d="M 46,28 C 48,36 52,44 60,46 C 68,48 74,44 76,50" fill="none" stroke="#111827" stroke-width="1" stroke-linecap="round" />
            <path d="M 50,30 C 53,38 56,44 64,46" fill="none" stroke="#111827" stroke-width="1" stroke-linecap="round" />
            <path d="M 43,26 L 33,26 L 33,39 L 36,39 C 39,41 39,45 36,46 L 36,49 C 41,52 44,56 44,64 L 54,64 C 54,52 48,46 47,44 L 46,26 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" stroke-linejoin="round" />
            <line x1="38" y1="31" x2="44" y2="31" stroke="#111827" stroke-width="1.5" stroke-linecap="round" />
            <path d="M 38,34 Q 41,37 44,34" fill="none" stroke="#111827" stroke-width="1.3" stroke-linecap="round" />
            <line x1="39" y1="35" x2="38" y2="38" stroke="#111827" stroke-width="0.8" />
            <line x1="41" y1="36" x2="41" y2="39" stroke="#111827" stroke-width="0.8" />
            <line x1="43" y1="35" x2="44" y2="38" stroke="#111827" stroke-width="0.8" />
            <path d="M 36,42 L 39,42" stroke="#e11d48" stroke-width="2" stroke-linecap="round" />
            <path d="M 22,70 C 22,54 28,48 44,48 L 47,60 C 44,66 38,72 26,74 Z" fill="${tunicPrimary}" stroke="#111827" stroke-width="1.2" stroke-linejoin="round" />
            <path d="M 54,48 C 62,48 70,52 70,68 L 52,68 C 50,60 52,54 54,48 Z" fill="${tunicPrimary}" stroke="#111827" stroke-width="1.2" stroke-linejoin="round" />
            <path d="M 34,54 Q 44,60 48,54" fill="#111827" />
            <path d="M 46,46 L 46,80 L 52,80 L 52,46 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" />
            <polygon points="46,48 52,51 46,54" fill="#111827" />
            <polygon points="52,54 46,57 52,60" fill="#111827" />
            <polygon points="46,60 52,63 46,66" fill="#111827" />
            <polygon points="52,66 46,69 52,72" fill="#111827" />
            <polygon points="46,72 52,75 46,78" fill="#111827" />
            <g stroke="#111827" stroke-width="1" stroke-linecap="round">
                <line x1="25" y1="21" x2="25" y2="18" />
                <line x1="25" y1="35" x2="25" y2="38" />
                <line x1="18" y1="28" x2="15" y2="28" />
                <line x1="32" y1="28" x2="35" y2="28" />
                <line x1="20" y1="23" x2="18" y2="21" />
                <line x1="30" y1="23" x2="32" y2="21" />
                <line x1="20" y1="33" x2="18" y2="35" />
                <line x1="30" y1="33" x2="32" y2="35" />
            </g>
            <text x="25" y="32" text-anchor="middle" font-size="13" font-weight="900" fill="${suitColor}">${symbol}</text>
            <path d="M 20,44 C 20,40 24,36 30,37 C 29,40 26,42 27,45 C 25,44 24,47 25,50 L 22,50 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M 72,66 C 74,70 76,75 76,80 C 74,79 73,76 72,77 C 71,76 70,78 69,76 L 68,70 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
        `;

        return `<svg class="card-court-svg" viewBox="0 0 100 146" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
            <defs>
                <clipPath id="${clipId}">
                    <polygon points="0,0 100,0 100,60 0,86" />
                </clipPath>
            </defs>
            <g clip-path="url(#${clipId})">
                ${half}
            </g>
            <g transform="rotate(180, 50, 73)" clip-path="url(#${clipId})">
                ${half}
            </g>
            <line x1="0" y1="86" x2="100" y2="60" stroke="#111827" stroke-width="1.3" stroke-linecap="round" />
        </svg>`;
    }

    function getJackSvg(suit, symbol, isRed) {
        const capFill = !isRed ? '#f43f5e' : '#0284c7';
        const tunicPrimary = !isRed ? '#2563eb' : '#ea580c';
        const tunicSecondary = !isRed ? '#0d9488' : '#f59e0b';
        const suitColor = !isRed ? '#111827' : '#dc2626';
        const tabletBg = !isRed ? '#fef08a' : '#ffffff';
        const clipId = `j-split-${suit}-${Math.random().toString(36).substr(2, 6)}`;

        const half = `
            <rect x="22" y="24" width="56" height="60" fill="${tunicSecondary}" rx="1" />
            <rect x="38" y="32" width="38" height="52" fill="${tunicPrimary}" rx="1" />
            <line x1="72" y1="4" x2="72" y2="76" stroke="#78350f" stroke-width="2" stroke-linecap="round" />
            <polygon points="72,3 69,12 72,10 75,12" fill="#cbd5e1" stroke="#111827" stroke-width="1" />
            <polygon points="72,10 77,14 72,17" fill="#cbd5e1" stroke="#111827" stroke-width="1" />
            <path d="M 40,20 C 40,12 56,8 66,14 C 64,22 56,22 40,20 Z" fill="${capFill}" stroke="#111827" stroke-width="1.2" />
            <path d="M 64,12 C 70,6 74,4 78,8 C 76,12 70,14 65,14" fill="#ffffff" stroke="#111827" stroke-width="1" />
            <circle cx="56" cy="18" r="2" fill="#f59e0b" stroke="#111827" stroke-width="1" />
            <path d="M 40,20 C 42,28 46,38 52,42 C 60,44 64,36 68,42 C 70,48 68,56 64,62" fill="#b45309" stroke="#111827" stroke-width="1.2" stroke-linecap="round" />
            <path d="M 40,20 L 32,20 L 32,32 L 35,32 C 37,34 37,38 34,39 L 34,42 C 38,45 42,48 42,56 L 52,56 C 52,46 46,40 45,38 L 44,20 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" stroke-linejoin="round" />
            <line x1="36" y1="24" x2="42" y2="24" stroke="#111827" stroke-width="1.5" stroke-linecap="round" />
            <circle cx="39" cy="28" r="1.5" fill="#111827" />
            <path d="M 34,36 L 37,36" stroke="#e11d48" stroke-width="1.5" stroke-linecap="round" />
            <path d="M 18,66 C 18,52 24,46 38,46 L 42,56 C 40,62 34,68 22,70 Z" fill="${tunicPrimary}" stroke="#111827" stroke-width="1.2" />
            <path d="M 48,46 C 56,46 64,50 64,66 L 48,66 Z" fill="${tunicPrimary}" stroke="#111827" stroke-width="1.2" />
            <path d="M 40,46 L 40,78 L 46,78 L 46,46 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" />
            <polygon points="40,48 46,51 40,54" fill="#111827" />
            <polygon points="46,54 40,57 46,60" fill="#111827" />
            <polygon points="40,60 46,63 40,66" fill="#111827" />
            <polygon points="46,66 40,69 46,72" fill="#111827" />
            <polygon points="40,72 46,75 40,78" fill="#111827" />
            <g transform="translate(24, 28)">
                <circle cx="0" cy="0" r="11" fill="${tabletBg}" stroke="#111827" stroke-width="1.2" />
                <circle cx="0" cy="0" r="8" fill="none" stroke="#f59e0b" stroke-width="0.8" />
                <text x="0" y="4" text-anchor="middle" font-size="11" font-weight="900" fill="${suitColor}">${symbol}</text>
            </g>
            <path d="M 18,39 C 18,34 22,30 27,31 C 26,35 24,37 25,40 C 23,39 22,42 23,45 L 20,45 Z" fill="#ffffff" stroke="#111827" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="72" cy="42" r="3.5" fill="#ffffff" stroke="#111827" stroke-width="1.1" />
        `;

        return `<svg class="card-court-svg" viewBox="0 0 100 146" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
            <defs>
                <clipPath id="${clipId}">
                    <polygon points="0,0 100,0 100,60 0,86" />
                </clipPath>
            </defs>
            <g clip-path="url(#${clipId})">
                ${half}
            </g>
            <g transform="rotate(180, 50, 73)" clip-path="url(#${clipId})">
                ${half}
            </g>
            <line x1="0" y1="86" x2="100" y2="60" stroke="#111827" stroke-width="1.3" stroke-linecap="round" />
        </svg>`;
    }

    function render3DCard(c, opts = {}) {
        const info = parseCard(c);
        if (!info) {
            return `<div class="playing-card-3d"><div class="card-back"><div class="card-back-pattern">🂠</div></div></div>`;
        }
        const suitSymbol = info.symbol;
        const isRed = info.isRed;
        const suitClass = isRed ? 'suit-red' : 'suit-black';
        const isPlayable = opts.playable ? 'is-playable' : '';
        const animClass = opts.anim || '';
        const styleAttr = opts.style ? `style="${opts.style}"` : '';
        const actIndex = opts.actionIndex !== undefined ? `data-action-index="${opts.actionIndex}"` : '';

        let centerHtml = '';
        if (info.rank === 'K') {
            centerHtml = `<div class="card-center court-graphic-container">${getKingSvg(info.suit, suitSymbol, isRed)}</div>`;
        } else if (info.rank === 'Q') {
            centerHtml = `<div class="card-center court-graphic-container">${getQueenSvg(info.suit, suitSymbol, isRed)}</div>`;
        } else if (info.rank === 'J') {
            centerHtml = `<div class="card-center court-graphic-container">${getJackSvg(info.suit, suitSymbol, isRed)}</div>`;
        } else if (info.rank === 'A') {
            centerHtml = `<div class="card-center ace-graphic-container">${getAceSvg(info.suit, suitSymbol, isRed)}</div>`;
        } else if (PIP_LAYOUTS[info.rank]) {
            centerHtml = `<div class="card-pips-matrix">${getPipsHtml(info.rank, suitSymbol, isRed)}</div>`;
        } else {
            centerHtml = `<div class="card-center"><span style="font-size:1.6rem">${suitSymbol}</span></div>`;
        }

        return `
        <div class="playing-card-3d ${isPlayable} ${animClass} group" data-card="${esc(c)}" ${actIndex} ${styleAttr} onmouseenter="window.ClubAudio && window.ClubAudio.hover()">
            <div class="card-face ${suitClass}">
                <div class="card-inner-frame"></div>
                <div class="card-corner card-corner-top">
                    <span class="card-val">${esc(info.rank)}</span>
                    <span class="card-suit-sm">${suitSymbol}</span>
                </div>
                ${centerHtml}
                <div class="card-corner card-corner-bottom">
                    <span class="card-val">${esc(info.rank)}</span>
                    <span class="card-suit-sm">${suitSymbol}</span>
                </div>
            </div>
        </div>`;
    }

    return {
        parseCard,
        render3DCard,
        getKingSvg,
        getQueenSvg,
        getJackSvg,
        getAceSvg,
        getPipsHtml,
        SUITS
    };
})();

window.ClubCards = ClubCards;
window.render3DCard = ClubCards.render3DCard;

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
                    const sampleCards = ['AS', 'KH', 'JS', 'QD', 'KC', 'AH'];
                    const pick = sampleCards[Math.floor(Math.random() * sampleCards.length)];
                    slapTarget.innerHTML = ClubCards.render3DCard(pick, { anim: 'anim-card-slap relative' });
                });
            }

            // Action: Card Throw
            const throwBtn = document.getElementById('hero-act-throw');
            const throwTarget = document.getElementById('hero-throw-dropzone');
            if (throwBtn && throwTarget) {
                throwBtn.addEventListener('click', () => {
                    if (window.ClubAudio) window.ClubAudio.throw();

                    const rot = (Math.random() * 24 - 12).toFixed(1);
                    const sampleCards = ['10D', 'AC', '9H', 'JC', 'QS', 'KD'];
                    const pick = sampleCards[Math.floor(Math.random() * sampleCards.length)];
                    const cardHtml = ClubCards.render3DCard(pick, {
                        anim: 'anim-card-flight relative',
                        style: `--throw-rot:${rot}deg; --throw-from-x:${(Math.random() * 80 - 40).toFixed(0)}px; --throw-from-y:150px; --throw-to-x:0px; --throw-to-y:0px;`
                    });
                    throwTarget.innerHTML = cardHtml;
                });
            }

            // Action: Deal cards
            const dealBtn = document.getElementById('hero-act-deal');
            const dealTarget = document.getElementById('hero-deal-dropzone');
            if (dealBtn && dealTarget) {
                dealBtn.addEventListener('click', () => {
                    dealTarget.innerHTML = '';
                    const sampleCards = ['AS', 'KH', 'QD', 'JC', '10S'];
                    sampleCards.forEach((c, idx) => {
                        setTimeout(() => {
                            if (window.ClubAudio) window.ClubAudio.deal();
                            const wrap = document.createElement('div');
                            wrap.innerHTML = ClubCards.render3DCard(c, {
                                anim: 'anim-card-deal',
                                style: idx === 0 ? '' : 'margin-left: -24px;'
                            });
                            const el = wrap.firstElementChild;
                            if (el) {
                                el.addEventListener('mouseenter', () => window.ClubAudio && window.ClubAudio.hover());
                                dealTarget.appendChild(el);
                            }
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
        return ClubCards.render3DCard(c, opts);
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
