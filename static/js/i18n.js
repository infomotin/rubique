/**
 * CubePermutation AI - Frontend Internationalization (i18n) Engine
 * ================================================================
 * Enables real-time language switching without page reloads.
 * Synchronizes with Flask backend session (/set-language/<lang>).
 * Supports English (en), Bengali (bn), Hindi (hi), Russian (ru), Chinese (zh).
 */

(function() {
    // Current Active Language
    let currentLang = localStorage.getItem('cube_ai_lang') || 'en';

    // Sound effect on language change
    function playLangTone() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(650, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.08);
            gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.12);
        } catch(e) {}
    }

    // Apply language to all elements in the DOM
    function applyLanguage(lang) {
        if (!window.TRANSLATIONS || !window.TRANSLATIONS[lang]) return;
        currentLang = lang;
        localStorage.setItem('cube_ai_lang', lang);

        const dict = window.TRANSLATIONS[lang];
        const defaultDict = window.TRANSLATIONS['en'] || {};

        // 1. Text elements
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (dict[key] !== undefined) {
                el.textContent = dict[key];
            } else if (defaultDict[key] !== undefined) {
                el.textContent = defaultDict[key];
            }
        });

        // 2. HTML elements with formatted text
        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            if (dict[key] !== undefined) {
                el.innerHTML = dict[key];
            } else if (defaultDict[key] !== undefined) {
                el.innerHTML = defaultDict[key];
            }
        });

        // 3. Placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (dict[key] !== undefined) {
                el.setAttribute('placeholder', dict[key]);
            } else if (defaultDict[key] !== undefined) {
                el.setAttribute('placeholder', defaultDict[key]);
            }
        });

        // 4. Titles / Tooltips
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            if (dict[key] !== undefined) {
                el.setAttribute('title', dict[key]);
            } else if (defaultDict[key] !== undefined) {
                el.setAttribute('title', defaultDict[key]);
            }
        });

        // 5. Update Language Switcher UI Selectors
        document.querySelectorAll('.lang-selector-btn').forEach(btn => {
            if (btn.dataset.lang === lang) {
                btn.classList.add('active-lang', 'border-indigo-500', 'bg-indigo-950/80');
            } else {
                btn.classList.remove('active-lang', 'border-indigo-500', 'bg-indigo-950/80');
            }
        });

        const activeLangDisplay = document.getElementById('current-lang-display');
        if (activeLangDisplay) {
            const flagMap = {
                'en': '🇬🇧 EN',
                'bn': '🇧🇩 বাংলা',
                'hi': '🇮🇳 हिन्दी',
                'ru': '🇷🇺 RU',
                'zh': '🇨🇳 中文'
            };
            activeLangDisplay.textContent = flagMap[lang] || '🇬🇧 EN';
        }

        // Notify backend of language change asynchronously
        try {
            fetch('/set-language/' + lang, { method: 'POST' });
        } catch(e) {}
    }

    // Global helper
    window.setLanguage = function(lang) {
        applyLanguage(lang);
        playLangTone();
    };

    window.getTranslation = function(key) {
        if (window.TRANSLATIONS && window.TRANSLATIONS[currentLang] && window.TRANSLATIONS[currentLang][key]) {
            return window.TRANSLATIONS[currentLang][key];
        }
        return key;
    };

    // Auto-init on page load
    document.addEventListener('DOMContentLoaded', () => {
        // Read backend language if passed in body tag
        const bodyLang = document.body.dataset.lang;
        if (bodyLang && !localStorage.getItem('cube_ai_lang')) {
            currentLang = bodyLang;
        } else if (localStorage.getItem('cube_ai_lang')) {
            currentLang = localStorage.getItem('cube_ai_lang');
        }
        applyLanguage(currentLang);

        // Bind language dropdown buttons
        document.querySelectorAll('.lang-select-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.preventDefault();
                const targetLang = opt.dataset.lang;
                window.setLanguage(targetLang);
                // Close dropdown
                const menu = document.getElementById('lang-dropdown-menu');
                if (menu) menu.classList.add('hidden');
            });
        });

        // Toggle language dropdown menu
        const langToggleBtn = document.getElementById('lang-toggle-btn');
        const langMenu = document.getElementById('lang-dropdown-menu');
        if (langToggleBtn && langMenu) {
            langToggleBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                langMenu.classList.toggle('hidden');
            });

            document.addEventListener('click', () => {
                langMenu.classList.add('hidden');
            });
        }
    });
})();
