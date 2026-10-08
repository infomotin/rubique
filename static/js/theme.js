/**
 * CubePermutation AI - Ultra-Modern Child & Teen Theme & Accent Engine
 * ====================================================================
 * - Seamlessly toggles Dark / Light Mode with WCAG AAA accessible high-contrast palettes.
 * - Dynamic 6-Color Accent Customizer (Indigo, Emerald, Amber, Rose, Purple, Cyan).
 * - Tactile Web Audio feedback for kids and young learners.
 * - Persistent preferences via localStorage.
 */

(function() {
    let currentTheme = localStorage.getItem('cube_ai_theme') || 'dark';
    let currentAccent = localStorage.getItem('cube_ai_accent') || 'indigo';

    function applyTheme(theme) {
        currentTheme = theme;
        localStorage.setItem('cube_ai_theme', theme);

        const htmlEl = document.documentElement;
        const bodyEl = document.body;
        const themeIcon = document.getElementById('theme-toggle-icon');
        const themeLabel = document.getElementById('theme-toggle-label');

        if (theme === 'light') {
            htmlEl.classList.remove('dark');
            htmlEl.classList.add('light');
            bodyEl.classList.remove('dark');
            bodyEl.classList.add('light');
            if (themeIcon) {
                themeIcon.className = 'fa-solid fa-sun text-amber-500';
            }
            if (themeLabel) themeLabel.textContent = 'Light';
        } else {
            htmlEl.classList.remove('light');
            htmlEl.classList.add('dark');
            bodyEl.classList.remove('light');
            bodyEl.classList.add('dark');
            if (themeIcon) {
                themeIcon.className = 'fa-solid fa-moon text-indigo-400';
            }
            if (themeLabel) themeLabel.textContent = 'Dark';
        }

        // Trigger resize on 3D WebGL canvases
        window.dispatchEvent(new Event('resize'));
    }

    function applyAccent(accent) {
        currentAccent = accent;
        localStorage.setItem('cube_ai_accent', accent);
        document.documentElement.setAttribute('data-accent', accent);

        // Update active rings on accent buttons if present
        document.querySelectorAll('.accent-picker-btn').forEach(btn => {
            if (btn.dataset.accent === accent) {
                btn.classList.add('ring-2', 'ring-white', 'scale-110');
            } else {
                btn.classList.remove('ring-2', 'ring-white', 'scale-110');
            }
        });
    }

    window.toggleTheme = function() {
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(nextTheme);

        // Web Audio Tone
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(nextTheme === 'light' ? 740 : 480, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.09);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.09);
        } catch(e) {}
    };

    window.setAccentTheme = function(accent) {
        applyAccent(accent);
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(820, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.07);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.07);
        } catch(e) {}
    };

    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(currentTheme);
        applyAccent(currentAccent);

        const themeToggleBtn = document.getElementById('theme-toggle-btn');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', window.toggleTheme);
        }

        // Setup accent picker dropdown toggle & listeners
        const accentToggleBtn = document.getElementById('accent-toggle-btn');
        const accentMenu = document.getElementById('accent-dropdown-menu');

        accentToggleBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            accentMenu?.classList.toggle('hidden');
        });

        document.addEventListener('click', () => {
            accentMenu?.classList.add('hidden');
        });

        document.querySelectorAll('.accent-select-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.preventDefault();
                const acc = opt.dataset.accent;
                if (acc) {
                    window.setAccentTheme(acc);
                    accentMenu?.classList.add('hidden');
                }
            });
        });
    });
})();
