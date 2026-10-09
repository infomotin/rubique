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
    let isMuted = false;
    let currentVolume = 0.85;

    // Load persisted settings
    try {
        isMuted = localStorage.getItem('card_club_muted') === 'true';
        const savedVol = localStorage.getItem('card_club_volume');
        if (savedVol !== null) currentVolume = parseFloat(savedVol);
    } catch (e) {}

    function getContext() {
        if (!audioCtx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!AudioContextClass) return null;
            audioCtx = new AudioContextClass();
            masterGain = audioCtx.createGain();
            masterGain.gain.setValueAtTime(isMuted ? 0 : currentVolume, audioCtx.currentTime);
            masterGain.connect(audioCtx.destination);
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

    return {
        // =============================================================
        // 1. CARD SHUFFLE / MIXING RIFFLE SOUND
        // =============================================================
        shuffle() {
            if (isMuted) return;
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
            const ctx = getContext();
            if (!ctx) return;
            const now = ctx.currentTime;

            const osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(3200, now);

            const gain = ctx.createGain();
            gain.gain.setValueAtTime(0.025, now);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.015);

            osc.connect(gain);
            gain.connect(masterGain);
            osc.start(now);
            osc.stop(now + 0.02);
        },

        // Controls
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
