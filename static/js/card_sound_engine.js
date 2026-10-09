/**
 * Rubique Card Club - Ultra High-Fidelity Web Audio Sound Engine
 * ===============================================================
 * Generates organic, high-definition physical audio synthesis without
 * external audio file dependencies.
 *
 * Audio Profiles:
 * 1. Card Shuffle / Mixing (Rapid realistic 36-card riffle flutter + deck tap)
 * 2. Card Slap (Explosive physical slap impact transient + felt sub-thud)
 * 3. Card Throw / Slide (Aerodynamic whoosh + velvet glide friction)
 * 4. Card Deal (Crisp snap-flick from dealer shoe)
 * 5. Chip / Coin Clink (High-resonance dual ceramic/metal clink)
 * 6. Victory Fanfare (Celebratory crystal bell triad chords)
 * 7. Card Hover / Touch (Ultra-subtle micro-flick tactile response)
 */

const ClubAudio = (() => {
    let audioCtx = null;
    let masterGain = null;
    let reverbSend = null;
    let isMuted = false;
    let currentVolume = 0.85;

    // Load persisted settings
    try {
        isMuted = localStorage.getItem('card_club_muted') === 'true';
        const savedVol = localStorage.getItem('card_club_volume');
        if (savedVol !== null) currentVolume = parseFloat(savedVol);
    } catch (e) {}

    // Random in range - keeps every performance organic/unique
    function rr(a, b) { return a + Math.random() * (b - a); }

    // Procedural room impulse response (concert-hall style, no audio files)
    function makeImpulse(ctx, seconds, decay) {
        const rate = ctx.sampleRate;
        const len = Math.max(1, Math.floor(rate * seconds));
        const impulse = ctx.createBuffer(2, len, rate);
        for (let ch = 0; ch < 2; ch++) {
            const data = impulse.getChannelData(ch);
            for (let i = 0; i < len; i++) {
                const t = i / len;
                data[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, decay);
            }
        }
        return impulse;
    }

    function getContext() {
        if (!audioCtx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!AudioContextClass) return null;
            audioCtx = new AudioContextClass();

            // Master fader
            masterGain = audioCtx.createGain();
            masterGain.gain.setValueAtTime(isMuted ? 0 : currentVolume, audioCtx.currentTime);

            // Dry path -> destination
            masterGain.connect(audioCtx.destination);

            // Wet path: master -> convolver room -> output gain -> destination.
            // Every sound automatically gains a cohesive "casino room" ambience
            // without per-sound routing changes.
            try {
                const convolver = audioCtx.createConvolver();
                convolver.buffer = makeImpulse(audioCtx, 1.35, 3.2);
                reverbSend = audioCtx.createGain();
                reverbSend.gain.value = 0.22;
                const wetOut = audioCtx.createGain();
                wetOut.gain.value = 0.55;
                masterGain.connect(reverbSend);
                reverbSend.connect(convolver);
                convolver.connect(wetOut);
                wetOut.connect(audioCtx.destination);
            } catch (e) { reverbSend = null; }
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        return audioCtx;
    }

    // Helper: Generate shaped noise buffer
    function createNoiseBuffer(ctx, duration) {
        const bufferSize = Math.max(1, Math.floor(ctx.sampleRate * duration));
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        return buffer;
    }

    function pulseVisualizer(ms = 500) {
        if (isMuted) return;
        const els = document.querySelectorAll('.audio-visualizer-container, #club-audio-visualizer');
        els.forEach(el => {
            el.classList.add('is-audio-playing');
            clearTimeout(el._eqTimer);
            el._eqTimer = setTimeout(() => el.classList.remove('is-audio-playing'), ms);
        });
    }

    return {
        // =============================================================
        // 1. CARD SHUFFLE / MIXING RIFFLE SOUND
        // =============================================================
        shuffle() {
            if (isMuted) return;
            pulseVisualizer(750);
            const ctx = getContext();

            if (!ctx) return;
            const now = ctx.currentTime;

            const cardCount = 34; // 34 micro-flicks
            const totalDuration = 0.65;
            const flickInterval = totalDuration / cardCount;

            // Multi-card riffle waterfall
            for (let i = 0; i < cardCount; i++) {
                const t = now + (i * flickInterval) + (Math.random() * 0.005);
                const noise = ctx.createBufferSource();
                noise.buffer = createNoiseBuffer(ctx, 0.015);

                const filter = ctx.createBiquadFilter();
                filter.type = 'bandpass';
                filter.frequency.setValueAtTime(1600 + Math.random() * 1800, t);
                filter.Q.setValueAtTime(3.5, t);

                const gain = ctx.createGain();
                const vel = 0.08 + (Math.sin((i / cardCount) * Math.PI) * 0.16);
                gain.gain.setValueAtTime(0, t);
                gain.gain.linearRampToValueAtTime(vel, t + 0.002);
                gain.gain.exponentialRampToValueAtTime(0.001, t + 0.014);

                noise.connect(filter);
                filter.connect(gain);
                gain.connect(masterGain);

                noise.start(t);
                noise.stop(t + 0.015);
            }

            // Air friction cascade whoosh
            const sweepSource = ctx.createBufferSource();
            sweepSource.buffer = createNoiseBuffer(ctx, 0.55);
            const sweepFilter = ctx.createBiquadFilter();
            sweepFilter.type = 'lowpass';
            sweepFilter.frequency.setValueAtTime(600, now);
            sweepFilter.frequency.linearRampToValueAtTime(2200, now + 0.3);
            sweepFilter.frequency.linearRampToValueAtTime(400, now + 0.55);

            const sweepGain = ctx.createGain();
            sweepGain.gain.setValueAtTime(0.01, now);
            sweepGain.gain.linearRampToValueAtTime(0.12, now + 0.25);
            sweepGain.gain.exponentialRampToValueAtTime(0.001, now + 0.55);

            sweepSource.connect(sweepFilter);
            sweepFilter.connect(sweepGain);
            sweepGain.connect(masterGain);
            sweepSource.start(now + 0.05);
            sweepSource.stop(now + 0.6);

            // Final satisfying deck closure tap
            const tapOsc = ctx.createOscillator();
            tapOsc.type = 'triangle';
            tapOsc.frequency.setValueAtTime(140, now + 0.62);
            tapOsc.frequency.exponentialRampToValueAtTime(45, now + 0.72);

            const tapGain = ctx.createGain();
            tapGain.gain.setValueAtTime(0.24, now + 0.62);
            tapGain.gain.exponentialRampToValueAtTime(0.001, now + 0.73);

            tapOsc.connect(tapGain);
            tapGain.connect(masterGain);
            tapOsc.start(now + 0.62);
            tapOsc.stop(now + 0.74);
        },

        // =============================================================
        // 2. CARD SLAP / SLAM SOUND
        // =============================================================
        slap() {
            if (isMuted) return;
            pulseVisualizer(300);
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            // Attack 1: Explosive sharp paper snap transient
            const snapNoise = ctx.createBufferSource();
            snapNoise.buffer = createNoiseBuffer(ctx, 0.05);
            const snapFilter = ctx.createBiquadFilter();
            snapFilter.type = 'bandpass';
            snapFilter.frequency.setValueAtTime(3200, now);
            snapFilter.frequency.exponentialRampToValueAtTime(800, now + 0.04);
            snapFilter.Q.setValueAtTime(2.0, now);

            const snapGain = ctx.createGain();
            snapGain.gain.setValueAtTime(0.45, now);
            snapGain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

            snapNoise.connect(snapFilter);
            snapFilter.connect(snapGain);
            snapGain.connect(masterGain);
            snapNoise.start(now);
            snapNoise.stop(now + 0.05);

            // Attack 2: Pitch drop snap
            const osc = ctx.createOscillator();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(950, now);
            osc.frequency.exponentialRampToValueAtTime(90, now + 0.08);

            const oscFilter = ctx.createBiquadFilter();
            oscFilter.type = 'lowpass';
            oscFilter.frequency.setValueAtTime(1800, now);

            const oscGain = ctx.createGain();
            oscGain.gain.setValueAtTime(0.35, now);
            oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);

            osc.connect(oscFilter);
            oscFilter.connect(oscGain);
            oscGain.connect(masterGain);
            osc.start(now);
            osc.stop(now + 0.1);

            // Table resonance: Heavy wooden felt sub-thud
            const thud = ctx.createOscillator();
            thud.type = 'sine';
            thud.frequency.setValueAtTime(110, now + 0.005);
            thud.frequency.exponentialRampToValueAtTime(35, now + 0.18);

            const thudGain = ctx.createGain();
            thudGain.gain.setValueAtTime(0.4, now + 0.005);
            thudGain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

            thud.connect(thudGain);
            thudGain.connect(masterGain);
            thud.start(now + 0.005);
            thud.stop(now + 0.19);
        },

        // =============================================================
        // 3. CARD THROW / GLIDE SOUND
        // =============================================================
        throw() {
            if (isMuted) return;
            pulseVisualizer(350);
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            // Air glide whoosh
            const noise = ctx.createBufferSource();
            noise.buffer = createNoiseBuffer(ctx, 0.22);

            const filter = ctx.createBiquadFilter();
            filter.type = 'bandpass';
            filter.frequency.setValueAtTime(2400, now);
            filter.frequency.exponentialRampToValueAtTime(650, now + 0.2);
            filter.Q.setValueAtTime(2.2, now);

            const gain = ctx.createGain();
            gain.gain.setValueAtTime(0.01, now);
            gain.gain.linearRampToValueAtTime(0.28, now + 0.04);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);

            noise.connect(filter);
            filter.connect(gain);
            gain.connect(masterGain);
            noise.start(now);
            noise.stop(now + 0.23);

            // Soft felt touch landing
            const landOsc = ctx.createOscillator();
            landOsc.type = 'triangle';
            landOsc.frequency.setValueAtTime(180, now + 0.16);
            landOsc.frequency.exponentialRampToValueAtTime(70, now + 0.24);

            const landGain = ctx.createGain();
            landGain.gain.setValueAtTime(0.12, now + 0.16);
            landGain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

            landOsc.connect(landGain);
            landGain.connect(masterGain);
            landOsc.start(now + 0.16);
            landOsc.stop(now + 0.25);
        },

        // =============================================================
        // 4. CARD DEAL SOUND
        // =============================================================
        deal() {
            if (isMuted) return;
            pulseVisualizer(250);
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            const noise = ctx.createBufferSource();
            noise.buffer = createNoiseBuffer(ctx, 0.07);

            const filter = ctx.createBiquadFilter();
            filter.type = 'bandpass';
            filter.frequency.setValueAtTime(1900, now);
            filter.Q.setValueAtTime(3.0, now);

            const gain = ctx.createGain();
            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.065);

            noise.connect(filter);
            filter.connect(gain);
            gain.connect(masterGain);
            noise.start(now);
            noise.stop(now + 0.07);
        },

        // =============================================================
        // 5. CHIP / COIN CLINK SOUND
        // =============================================================
        chips() {
            if (isMuted) return;
            pulseVisualizer(300);
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            const freqs = [2200, 3150, 4800];
            freqs.forEach((freq, idx) => {
                const osc = ctx.createOscillator();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq + (Math.random() * 80 - 40), now + (idx * 0.015));

                const gain = ctx.createGain();
                const startT = now + (idx * 0.015);
                gain.gain.setValueAtTime(0.18 / (idx + 1), startT);
                gain.gain.exponentialRampToValueAtTime(0.001, startT + 0.12);

                osc.connect(gain);
                gain.connect(masterGain);
                osc.start(startT);
                osc.stop(startT + 0.13);
            });
        },

        // =============================================================
        // 6. VICTORY FANFARE SOUND
        // =============================================================
        win() {
            if (isMuted) return;
            pulseVisualizer(800);
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            const notes = [
                { f: 523.25, t: 0.00, d: 0.18 }, // C5
                { f: 659.25, t: 0.14, d: 0.18 }, // E5
                { f: 783.99, t: 0.28, d: 0.22 }, // G5
                { f: 1046.50, t: 0.44, d: 0.55 }, // C6
                { f: 1318.51, t: 0.44, d: 0.55 }, // E6 harmonic
            ];

            notes.forEach(n => {
                const osc = ctx.createOscillator();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(n.f, now + n.t);

                const gain = ctx.createGain();
                gain.gain.setValueAtTime(0.2, now + n.t);
                gain.gain.exponentialRampToValueAtTime(0.001, now + n.t + n.d);

                osc.connect(gain);
                gain.connect(masterGain);
                osc.start(now + n.t);
                osc.stop(now + n.t + n.d + 0.02);
            });
        },

        // =============================================================
        // 7. CARD HOVER / TOUCH TACTILE
        // =============================================================
        hover() {
            if (isMuted) return;
            pulseVisualizer(120);
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            const osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(rr(3000, 3600), now);

            const gain = ctx.createGain();
            gain.gain.setValueAtTime(0.025, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.015);

            osc.connect(gain);
            gain.connect(masterGain);
            osc.start(now);
            osc.stop(now + 0.02);
        },

        // =============================================================
        // 8. CARD FLIP (reveal) - two-stage paper flip with air catch
        // =============================================================
        flip() {
            if (isMuted) return;
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            // Stage 1: finger snaps card over
            const n1 = ctx.createBufferSource();
            n1.buffer = createNoiseBuffer(ctx, 0.04);
            const f1 = ctx.createBiquadFilter();
            f1.type = 'bandpass';
            f1.frequency.setValueAtTime(rr(2400, 3000), now);
            f1.Q.value = 2.5;
            const g1 = ctx.createGain();
            g1.gain.setValueAtTime(0.28, now);
            g1.gain.exponentialRampToValueAtTime(0.001, now + 0.035);
            n1.connect(f1); f1.connect(g1); g1.connect(masterGain);
            n1.start(now); n1.stop(now + 0.04);

            // Stage 2: card lands face-up (soft tick + air)
            const n2 = ctx.createBufferSource();
            n2.buffer = createNoiseBuffer(ctx, 0.05);
            const f2 = ctx.createBiquadFilter();
            f2.type = 'highpass';
            f2.frequency.setValueAtTime(900, now + 0.05);
            const g2 = ctx.createGain();
            g2.gain.setValueAtTime(0.001, now + 0.05);
            g2.gain.linearRampToValueAtTime(0.22, now + 0.058);
            g2.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
            n2.connect(f2); f2.connect(g2); g2.connect(masterGain);
            n2.start(now + 0.05); n2.stop(now + 0.1);

            const tick = ctx.createOscillator();
            tick.type = 'triangle';
            tick.frequency.setValueAtTime(rr(700, 850), now + 0.055);
            tick.frequency.exponentialRampToValueAtTime(280, now + 0.1);
            const tg = ctx.createGain();
            tg.gain.setValueAtTime(0.12, now + 0.055);
            tg.gain.exponentialRampToValueAtTime(0.001, now + 0.11);
            tick.connect(tg); tg.connect(masterGain);
            tick.start(now + 0.055); tick.stop(now + 0.12);
        },

        // =============================================================
        // 9. TURN TICK - soft table-clock awareness ping
        // =============================================================
        turn() {
            if (isMuted) return;
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            const osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(1180, now);
            const gain = ctx.createGain();
            gain.gain.setValueAtTime(0.09, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.14);
            osc.connect(gain); gain.connect(masterGain);
            osc.start(now); osc.stop(now + 0.15);

            const harm = ctx.createOscillator();
            harm.type = 'sine';
            harm.frequency.setValueAtTime(2360, now);
            const hg = ctx.createGain();
            hg.gain.setValueAtTime(0.03, now);
            hg.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);
            harm.connect(hg); hg.connect(masterGain);
            harm.start(now); harm.stop(now + 0.1);
        },

        // =============================================================
        // 10. COIN POUR - payout cascade of raining coins
        // =============================================================
        coins() {
            if (isMuted) return;
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            const drops = 22;
            for (let i = 0; i < drops; i++) {
                const t = now + i * rr(0.028, 0.055);
                const f = rr(1700, 5200);
                const osc = ctx.createOscillator();
                osc.type = Math.random() < 0.5 ? 'sine' : 'triangle';
                osc.frequency.setValueAtTime(f, t);
                osc.frequency.exponentialRampToValueAtTime(f * rr(0.55, 0.8), t + 0.07);
                const g = ctx.createGain();
                g.gain.setValueAtTime(0, t);
                g.gain.linearRampToValueAtTime(rr(0.05, 0.14), t + 0.004);
                g.gain.exponentialRampToValueAtTime(0.001, t + rr(0.06, 0.12));
                osc.connect(g); g.connect(masterGain);
                osc.start(t); osc.stop(t + 0.14);
            }

            // metallic shimmer bed under the cascade
            const bed = ctx.createBufferSource();
            bed.buffer = createNoiseBuffer(ctx, 0.7);
            const bf = ctx.createBiquadFilter();
            bf.type = 'bandpass';
            bf.frequency.setValueAtTime(3400, now);
            bf.frequency.linearRampToValueAtTime(5600, now + 0.6);
            bf.Q.value = 1.6;
            const bg = ctx.createGain();
            bg.gain.setValueAtTime(0.05, now);
            bg.gain.linearRampToValueAtTime(0.09, now + 0.25);
            bg.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
            bed.connect(bf); bf.connect(bg); bg.connect(masterGain);
            bed.start(now); bed.stop(now + 0.72);
        },

        // =============================================================
        // 11. SUCCESS CHIME - actions confirmed (create/accept/verify)
        // =============================================================
        success() {
            if (isMuted) return;
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            const notes = [
                { f: 659.25, t: 0.00 },
                { f: 830.61, t: 0.07 },
                { f: 987.77, t: 0.14 },
                { f: 1318.51, t: 0.22 },
            ];
            notes.forEach((n, i) => {
                const osc = ctx.createOscillator();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(n.f, now + n.t);
                const g = ctx.createGain();
                g.gain.setValueAtTime(0.001, now + n.t);
                g.gain.linearRampToValueAtTime(0.14 - i * 0.02, now + n.t + 0.012);
                g.gain.exponentialRampToValueAtTime(0.001, now + n.t + 0.45);
                osc.connect(g); g.connect(masterGain);
                osc.start(now + n.t); osc.stop(now + n.t + 0.5);
            });
        },

        // =============================================================
        // 12. ERROR BUZZ - rejected action
        // =============================================================
        error() {
            if (isMuted) return;
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            for (let i = 0; i < 2; i++) {
                const t = now + i * 0.11;
                const osc = ctx.createOscillator();
                osc.type = 'square';
                osc.frequency.setValueAtTime(196, t);
                const f = ctx.createBiquadFilter();
                f.type = 'lowpass';
                f.frequency.value = 900;
                const g = ctx.createGain();
                g.gain.setValueAtTime(0.12, t);
                g.gain.exponentialRampToValueAtTime(0.001, t + 0.085);
                osc.connect(f); f.connect(g); g.connect(masterGain);
                osc.start(t); osc.stop(t + 0.09);
            }
        },

        // =============================================================
        // 13. DEAL FAN - n staggered crisp flicks from the shoe
        // =============================================================
        dealFan(count) {
            if (isMuted) return;
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;
            const n = Math.max(1, Math.min(count || 5, 26));
            for (let i = 0; i < n; i++) {
                const t = now + i * 0.11;
                const noise = ctx.createBufferSource();
                noise.buffer = createNoiseBuffer(ctx, 0.07);
                const filter = ctx.createBiquadFilter();
                filter.type = 'bandpass';
                filter.frequency.setValueAtTime(rr(1700, 2300), t);
                filter.Q.setValueAtTime(rr(2.6, 3.6), t);
                const gain = ctx.createGain();
                gain.gain.setValueAtTime(0, t);
                gain.gain.linearRampToValueAtTime(rr(0.16, 0.26), t + 0.004);
                gain.gain.exponentialRampToValueAtTime(0.001, t + 0.062);
                noise.connect(filter); filter.connect(gain); gain.connect(masterGain);
                noise.start(t); noise.stop(t + 0.07);
            }
        },

        // =============================================================
        // Controls
        // =============================================================
        unlock() {
            // Called on the first user gesture (autoplay policy).
            const ctx = getContext();
            if (ctx && ctx.state === 'suspended') ctx.resume();
            return !!ctx;
        },

        setMuted(muted) {
            isMuted = !!muted;
            try { localStorage.setItem('card_club_muted', String(isMuted)); } catch (e) {}
            if (masterGain && audioCtx) {
                masterGain.gain.setValueAtTime(isMuted ? 0 : currentVolume, audioCtx.currentTime);
            }
            return isMuted;
        },

        toggleMute() {
            return this.setMuted(!isMuted);
        },

        isMuted() {
            return isMuted;
        },

        setVolume(vol) {
            currentVolume = Math.max(0, Math.min(1, vol));
            try { localStorage.setItem('card_club_volume', String(currentVolume)); } catch (e) {}
            if (masterGain && audioCtx && !isMuted) {
                masterGain.gain.setValueAtTime(currentVolume, audioCtx.currentTime);
            }
        },

        getVolume() {
            return currentVolume;
        }
    };
})();

// Attach globally
window.ClubAudio = ClubAudio;
