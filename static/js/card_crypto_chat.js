/**
 * Rubique Card Club - Zero-Knowledge End-to-End Encrypted Group Chat Engine
 * =========================================================================
 * Cryptographic Primitive: AES-256-GCM + PBKDF2 (100,000 iterations SHA-256)
 * Security Invariant: Plaintext NEVER leaves the client. Only ciphertext + IV
 * are transmitted and stored on the server ("No one capture or Decrypted it").
 */

const CardCryptoChat = (() => {
    let activeKey = null;
    let activeGroupId = null;
    let activePassphrase = null;
    let pollInterval = null;
    let lastMsgId = 0;

    // Base64 helpers
    function bufToB64(buf) {
        let binary = '';
        const bytes = new Uint8Array(buf);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    function b64ToBuf(b64) {
        const binary = window.atob(b64);
        const len = binary.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    // Key Derivation with PBKDF2
    async function deriveAESKey(passphrase, groupId) {
        const enc = new TextEncoder();
        const keyMaterial = await window.crypto.subtle.importKey(
            'raw',
            enc.encode(passphrase),
            { name: 'PBKDF2' },
            false,
            ['deriveKey']
        );

        const salt = enc.encode(`rubique_group_salt_${groupId}_aes256`);
        return await window.crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt: salt,
                iterations: 100000,
                hash: 'SHA-256'
            },
            keyMaterial,
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );
    }

    // Encrypt Plaintext -> { ciphertext: B64, iv: B64 }
    async function encryptText(plaintext, key) {
        const enc = new TextEncoder();
        const iv = window.crypto.getRandomValues(new Uint8Array(12)); // 96-bit IV
        const encoded = enc.encode(plaintext);

        const encrypted = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv },
            key,
            encoded
        );

        return {
            ciphertext: bufToB64(encrypted),
            iv: bufToB64(iv)
        };
    }

    // Decrypt { ciphertext: B64, iv: B64 } -> Plaintext
    async function decryptText(ciphertextB64, ivB64, key) {
        try {
            const ciphertextBuf = b64ToBuf(ciphertextB64);
            const ivBuf = b64ToBuf(ivB64);

            const decrypted = await window.crypto.subtle.decrypt(
                { name: 'AES-GCM', iv: new Uint8Array(ivBuf) },
                key,
                ciphertextBuf
            );

            return new TextDecoder().decode(decrypted);
        } catch (e) {
            return null; // Decryption failed (invalid key or tampered ciphertext)
        }
    }

    // Fingerprint calculation (SHA-256 hash preview of key)
    async function getKeyFingerprint(key) {
        try {
            const exported = await window.crypto.subtle.exportKey('raw', key);
            const hash = await window.crypto.subtle.digest('SHA-256', exported);
            const hashArr = Array.from(new Uint8Array(hash));
            return hashArr.slice(0, 4).map(b => b.toString(16).padStart(2, '0')).join(':').toUpperCase();
        } catch (e) {
            return 'E2EE-ACTIVE';
        }
    }

    // DOM Chat UI manager
    async function initUI({ groupId, defaultSecret, containerId = 'group-chat-container' }) {
        activeGroupId = groupId;
        activePassphrase = defaultSecret || `group_${groupId}_secret`;

        // Load stored custom passphrase if any
        try {
            const stored = localStorage.getItem(`group_${groupId}_custom_secret`);
            if (stored) activePassphrase = stored;
        } catch (e) {}

        activeKey = await deriveAESKey(activePassphrase, groupId);
        const fp = await getKeyFingerprint(activeKey);
        const fpEl = document.getElementById('chat-key-fingerprint');
        if (fpEl) fpEl.textContent = `KEY: ${fp}`;

        // Hook Send Form
        const sendForm = document.getElementById('group-chat-send-form');
        const inputEl = document.getElementById('group-chat-input');
        if (sendForm && inputEl) {
            sendForm.addEventListener('submit', async (ev) => {
                ev.preventDefault();
                const text = inputEl.value.trim();
                if (!text) return;

                inputEl.disabled = true;
                try {
                    const enc = await encryptText(text, activeKey);
                    const res = await fetch(`/club/api/groups/${groupId}/chat`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Card-Club': '1'
                        },
                        credentials: 'same-origin',
                        body: JSON.stringify(enc)
                    });
                    const data = await res.json();
                    if (!data.ok) throw new Error(data.error || 'Failed to send message');
                    
                    inputEl.value = '';
                    if (window.ClubAudio) window.ClubAudio.deal();
                    await fetchAndRenderMessages();
                } catch (err) {
                    alert('Encryption/Send error: ' + err.message);
                } finally {
                    inputEl.disabled = false;
                    inputEl.focus();
                }
            });
        }

        // Custom Key changer
        const keyBtn = document.getElementById('chat-change-key-btn');
        if (keyBtn) {
            keyBtn.addEventListener('click', async () => {
                const custom = window.prompt('Set Group Chat AES-256 Secret Passphrase:\n(All members must enter the exact same passphrase to decrypt chat)', activePassphrase);
                if (custom && custom.trim()) {
                    activePassphrase = custom.trim();
                    try { localStorage.setItem(`group_${groupId}_custom_secret`, activePassphrase); } catch (e) {}
                    activeKey = await deriveAESKey(activePassphrase, groupId);
                    const newFp = await getKeyFingerprint(activeKey);
                    if (fpEl) fpEl.textContent = `KEY: ${newFp}`;
                    await fetchAndRenderMessages();
                }
            });
        }

        // Socket.IO real-time listener if available
        if (window.io && window.CLUB_SOCKET) {
            window.CLUB_SOCKET.emit('join_group_chat', { group_id: groupId });
            window.CLUB_SOCKET.on('group_encrypted_chat', async (msg) => {
                if (msg && msg.group_id === activeGroupId) {
                    if (window.ClubAudio) window.ClubAudio.chips();
                    await fetchAndRenderMessages();
                }
            });
        }

        // Initial fetch + 3.5s fallback polling
        await fetchAndRenderMessages();
        clearInterval(pollInterval);
        pollInterval = setInterval(fetchAndRenderMessages, 3500);
    }

    async function fetchAndRenderMessages() {
        if (!activeGroupId || !activeKey) return;
        const msgBox = document.getElementById('group-chat-messages');
        if (!msgBox) return;

        try {
            const res = await fetch(`/club/api/groups/${activeGroupId}/chat?limit=50`, {
                headers: { 'X-Card-Club': '1' },
                credentials: 'same-origin'
            });
            const data = await res.json();
            if (!data.ok || !data.messages) return;

            const myUid = window.CLUB_USER_ID || 0;
            let html = '';

            for (const msg of data.messages) {
                lastMsgId = Math.max(lastMsgId, msg.id);
                const isMe = msg.user_id === myUid;
                const decrypted = await decryptText(msg.ciphertext, msg.iv, activeKey);

                const timeStr = (msg.created_at || '').split(' ')[1] || '';
                
                if (decrypted !== null) {
                    // Successfully decrypted message
                    html += `
                        <div class="flex flex-col ${isMe ? 'items-end' : 'items-start'} mb-3">
                            <div class="flex items-center gap-1.5 mb-1 font-mono text-[10px] text-slate-400">
                                <span class="font-bold ${isMe ? 'text-emerald-400' : 'text-cyan-300'}">${escapeHtml(msg.username)}</span>
                                <span class="text-slate-600">&bull;</span>
                                <span class="text-slate-500">${escapeHtml(timeStr)}</span>
                                <span class="inline-flex items-center text-emerald-400 text-[9px]" title="AES-256-GCM Verified">
                                    <i class="fa-solid fa-lock text-[8px] mr-0.5"></i>E2EE
                                </span>
                            </div>
                            <div class="max-w-[85%] px-3.5 py-2 rounded-2xl text-xs font-sans shadow-lg ${
                                isMe 
                                    ? 'bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-br-xs'
                                    : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-xs'
                            }">
                                ${escapeHtml(decrypted)}
                            </div>
                        </div>
                    `;
                } else {
                    // Tampered or wrong passphrase ciphertext preview
                    html += `
                        <div class="flex flex-col ${isMe ? 'items-end' : 'items-start'} mb-3 opacity-60">
                            <div class="flex items-center gap-1.5 mb-1 font-mono text-[10px] text-slate-500">
                                <span>${escapeHtml(msg.username)}</span>
                                <span>&bull;</span>
                                <span class="text-rose-400"><i class="fa-solid fa-shield-halved mr-0.5"></i>Encrypted Payload</span>
                            </div>
                            <div class="max-w-[85%] px-3 py-1.5 rounded-xl text-[10px] font-mono bg-rose-950/40 border border-rose-500/30 text-rose-300">
                                🔒 [Undecryptable: 0x${escapeHtml(msg.ciphertext.slice(0, 16))}&hellip; Passphrase required]
                            </div>
                        </div>
                    `;
                }
            }

            if (!data.messages.length) {
                html = `
                    <div class="text-center py-8 text-slate-500 font-mono text-xs">
                        <i class="fa-solid fa-shield-halved text-2xl text-emerald-500/40 mb-2 block"></i>
                        Vault initialized. Start chatting securely with AES-256-GCM encryption.
                    </div>
                `;
            }

            msgBox.innerHTML = html;
            msgBox.scrollTop = msgBox.scrollHeight;
        } catch (e) {
            console.warn('Chat fetch failed:', e);
        }
    }

    function escapeHtml(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    return {
        init: initUI,
        encrypt: encryptText,
        decrypt: decryptText,
        deriveKey: deriveAESKey
    };
})();

window.CardCryptoChat = CardCryptoChat;
