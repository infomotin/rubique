/**
 * CubePermutation AI - Dark / Light Theme Engine
 * ===============================================
 * Seamlessly switches between Cyber Dark Mode and Clean Light Mode.
 * Persists user preference in localStorage.
 */

(function() {
    let currentTheme = localStorage.getItem('cube_ai_theme') || 'dark';

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

        // Trigger resize on 3D canvases
        window.dispatchEvent(new Event('resize'));
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
            osc.frequency.setValueAtTime(nextTheme === 'light' ? 700 : 500, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.06, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.08);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.08);
        } catch(e) {}
    };

    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(currentTheme);

        const themeToggleBtn = document.getElementById('theme-toggle-btn');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', window.toggleTheme);
        }
    });
})();
