/**
 * CubePermutation AI - Responsive Screen Resolution & Multi-View Engine
 * ======================================================================
 * 1. Automatically detects device screen resolution & viewport dimensions.
 * 2. Provides 3 Responsive Modes: [ 💻 Desktop Mode, 📱 Tablet Mode, 📲 Mobile Mode ].
 * 3. Dynamically triggers Three.js 3D canvas resize and layout optimization.
 * 4. Includes live Resolution HUD & Viewport Simulation Switcher.
 */

(function() {
    let currentViewMode = localStorage.getItem('cube_ai_view_mode') || 'auto';

    function getDeviceCategory(width) {
        if (width >= 1024) return { name: 'Desktop', icon: 'fa-desktop', mode: 'desktop' };
        if (width >= 640) return { name: 'Tablet', icon: 'fa-tablet-screen-button', mode: 'tablet' };
        return { name: 'Mobile', icon: 'fa-mobile-screen-button', mode: 'mobile' };
    }

    function updateResolutionHUD() {
        const w = window.innerWidth;
        const h = window.innerHeight;
        const autoCat = getDeviceCategory(w);

        const badgeIcon = document.getElementById('device-hud-icon');
        const badgeLabel = document.getElementById('device-hud-label');
        const badgeRes = document.getElementById('device-hud-res');

        const activeMode = currentViewMode === 'auto' ? autoCat.mode : currentViewMode;
        const activeCat = activeMode === 'desktop' ? { name: 'Desktop Mode', icon: 'fa-desktop' } :
                          activeMode === 'tablet' ? { name: 'Tablet Mode', icon: 'fa-tablet-screen-button' } :
                          { name: 'Mobile Phone', icon: 'fa-mobile-screen-button' };

        if (badgeIcon) badgeIcon.className = `fa-solid ${activeCat.icon} text-cyan-400`;
        if (badgeLabel) badgeLabel.textContent = currentViewMode === 'auto' ? `Auto (${autoCat.name})` : activeCat.name;
        if (badgeRes) badgeRes.textContent = `${w}×${h}`;

        // Set body and html classes
        document.body.classList.remove('view-mode-auto', 'view-mode-desktop', 'view-mode-tablet', 'view-mode-mobile');
        document.body.classList.add(`view-mode-${currentViewMode}`);
        document.documentElement.setAttribute('data-device-category', autoCat.mode);
        document.documentElement.setAttribute('data-active-view-mode', activeMode);
        document.documentElement.setAttribute('data-view-mode', currentViewMode);

        // Update dropdown menu active states
        document.querySelectorAll('.device-mode-option').forEach(opt => {
            const isMatch = opt.dataset.mode === currentViewMode;
            if (isMatch) {
                opt.classList.add('bg-cyan-950/80', 'font-bold', 'border', 'border-cyan-500/40');
            } else {
                opt.classList.remove('bg-cyan-950/80', 'font-bold', 'border', 'border-cyan-500/40');
            }
        });
    }

    window.setViewMode = function(mode) {
        currentViewMode = mode;
        localStorage.setItem('cube_ai_view_mode', mode);
        updateResolutionHUD();

        // Trigger 3D WebGL resize
        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 100);

        // Sound tone
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(mode === 'mobile' ? 520 : mode === 'tablet' ? 640 : 780, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.08);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.08);
        } catch(e) {}
    };

    window.addEventListener('resize', () => {
        updateResolutionHUD();
    });

    document.addEventListener('DOMContentLoaded', () => {
        updateResolutionHUD();

        // Device Mode Selector Dropdown handlers
        const deviceBtn = document.getElementById('device-mode-toggle-btn');
        const deviceMenu = document.getElementById('device-mode-dropdown-menu');

        deviceBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            deviceMenu?.classList.toggle('hidden');
        });

        document.addEventListener('click', () => {
            deviceMenu?.classList.add('hidden');
        });

        document.querySelectorAll('.device-mode-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.preventDefault();
                const mode = opt.dataset.mode;
                if (mode) {
                    window.setViewMode(mode);
                    deviceMenu?.classList.add('hidden');
                }
            });
        });
    });
})();
