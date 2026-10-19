"""Versioned hashes for high-entropy session tokens; not password hashing.

Legacy raw-token lookup remains temporarily for existing sessions. Never accept
a stored digest as a bearer credential, including through that legacy fallback.
"""
import hashlib

SESSION_HASH_PREFIX = 'sha256:'


def hash_session_token(token):
    return SESSION_HASH_PREFIX + hashlib.sha256(token.encode('utf-8')).hexdigest()


def session_lookup_values(token):
    if not isinstance(token, str):
        return None
    token = token.strip()
    if not token or len(token) > 128 or token.startswith(SESSION_HASH_PREFIX):
        return None
    return hash_session_token(token), token
