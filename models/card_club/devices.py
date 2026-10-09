"""Device binding: one site registration per machine (multi-account guard).

Key strength:
  strong  = X-Device-Mac header or a client fingerprint (JS: UA + screen +
            language) - unambiguous, enforced at register AND login.
  weak    = sha256(ip + user-agent) - only used as a last resort; enforced
            at register time only (shared NAT / proxies would otherwise
            lock out legitimate users).

Replace `compose_device_key` with hardware attestation (WebAuthn / MDM) for
production - limitations documented in docs/CARD_CLUB_SETUP.md.
"""

import hashlib

from models.db import query_one, execute_insert, query_all

DEVICE_BINDING_ENABLED = True


def _sha(text):
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def compose_device_key(request, form_fallback=None):
    """Returns (strength, key) - strength in {'strong', 'weak'}."""
    mac = request.headers.get("X-Device-Mac") or request.form.get("device_mac")
    if mac:
        return "strong", _sha("mac:" + mac.strip().lower())
    fp = form_fallback or request.form.get("device_fp")
    if fp:
        return "strong", _sha("fp:" + fp.strip())
    ip = request.remote_addr or "0.0.0.0"
    ua = request.headers.get("User-Agent", "")
    return "weak", _sha(f"net:{ip}|{ua}")


def _lookup(key):
    row = query_one(
        "SELECT user_id FROM device_registrations WHERE device_key = %s",
        "SELECT user_id FROM device_registrations WHERE device_key = ?",
        (key,))
    if not row:
        return None
    return int(row["user_id"] if isinstance(row, dict) else row[0])


def bind_device(user_id, key):
    if _lookup(key) is None:
        try:
            execute_insert(
                "INSERT INTO device_registrations (device_key, user_id) VALUES (%s,%s)",
                "INSERT INTO device_registrations (device_key, user_id) VALUES (?,?)",
                (key, user_id))
        except Exception:
            pass  # concurrent bind race - someone else owns it now


def check_registration(user_id, key):
    """Returns (ok, message). Blocks when the device is bound to another
    user (multi-account guard)."""
    if not DEVICE_BINDING_ENABLED:
        return True, ""
    owner = _lookup(key)
    if owner is not None and owner != int(user_id):
        return False, ("This device is already registered to another "
                       "account. One account per device.")
    return True, ""


def check_login(user, key):
    """Returns (ok, message). A user with bound devices may only log in
    from a bound device when the request carries a strong key."""
    if not DEVICE_BINDING_ENABLED:
        return True, ""
    strength, val = key
    uid = int(user["id"] if isinstance(user, dict) else user[0])
    owner = _lookup(val)
    if owner == uid:
        return True, ""
    rows = query_all(
        "SELECT device_key FROM device_registrations WHERE user_id = %s",
        "SELECT device_key FROM device_registrations WHERE user_id = ?",
        (uid,))
    bound = {r["device_key"] if isinstance(r, dict) else r[0] for r in rows or []}
    if not bound:
        bind_device(uid, val)
        return True, ""
    if strength == "weak":
        return True, ""               # cannot disambiguate behind NAT
    if val in bound:
        return True, ""
    return False, "This account is bound to a different device."
