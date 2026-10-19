"""Cookie transport foundation. Disabled until the coordinated frontend cutover."""
import hashlib
import hmac
import secrets

from flask import current_app, jsonify, request
from .session_tokens import session_lookup_values


def cookie_auth_enabled():
    return current_app.config.get('COOKIE_AUTH_ENABLED', False)


def cookie_name(kind):
    prefix = '__Host-iw-' if current_app.config['SESSION_COOKIE_SECURE'] else 'iw-dev-'
    return prefix + kind


def request_session_token():
    if cookie_auth_enabled():
        # Never silently fall back to bearer credentials in cookie mode.
        return request.cookies.get(cookie_name('session'), '')
    return request.headers.get('Authorization', '').replace('Bearer ', '')


def revoke_presented_cookie(db):
    if cookie_auth_enabled():
        values = session_lookup_values(request_session_token())
        if values:
            db.execute('DELETE FROM user_sessions WHERE token IN (?, ?)', values)


def csrf_value(binding):
    key = current_app.config['SECRET_KEY'].encode('utf-8')
    return hmac.new(key, ('csrf:' + binding).encode('utf-8'), hashlib.sha256).hexdigest()


def set_private_cookie(response, kind, value, max_age):
    response.set_cookie(cookie_name(kind), value, max_age=max_age, path='/',
                        secure=current_app.config['SESSION_COOKIE_SECURE'],
                        httponly=True, samesite='Lax')


def session_version(token):
    key = current_app.config['SECRET_KEY'].encode('utf-8')
    return hmac.new(key, ('version:' + token).encode('utf-8'), hashlib.sha256).hexdigest()


def session_response(payload, status=200):
    if not cookie_auth_enabled():
        return jsonify(payload), status
    payload = dict(payload)
    token = payload.pop('token')
    # This identifier is not an authentication credential. It supports stale-401
    # protection without exposing the session token to JavaScript.
    payload['sessionVersion'] = session_version(token)
    response = jsonify(payload)
    response.status_code = status
    set_private_cookie(response, 'session', token, 7 * 24 * 60 * 60)
    response.headers['Cache-Control'] = 'no-store'
    return response


def install_cookie_auth(app):
    @app.get('/api/auth/csrf')
    def csrf_bootstrap():
        if not cookie_auth_enabled():
            return jsonify({'success': False, 'error': 'Not found'}), 404
        origin = request.headers.get('Origin')
        if origin not in current_app.config['COOKIE_AUTH_ORIGINS']:
            return jsonify({'success': False, 'error': 'Origin not allowed'}), 403
        session = request_session_token()
        seed = request.cookies.get(cookie_name('csrf')) or secrets.token_urlsafe(32)
        response = jsonify({'csrfToken': csrf_value(session or seed)})
        if not session:
            set_private_cookie(response, 'csrf', seed, 3600)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.before_request
    def check_csrf():
        if not cookie_auth_enabled() or not request.path.startswith('/api/'):
            return None
        expected_version = request.headers.get('X-Session-Version')
        if expected_version and not hmac.compare_digest(expected_version.encode('utf-8'), session_version(request_session_token()).encode('ascii')):
            return jsonify({'success': False, 'error': 'Session changed. Please refresh.'}), 403
        # Compatibility: this existing GET marks messages read. Protect that
        # side effect until a separate read-receipt mutation is introduced.
        reads_messages = request.endpoint == 'messages.get_messages'
        if request.method == 'OPTIONS' or (request.method in ('GET', 'HEAD') and not reads_messages):
            return None
        if request.headers.get('Origin') not in current_app.config['COOKIE_AUTH_ORIGINS']:
            return jsonify({'success': False, 'error': 'Origin not allowed'}), 403
        binding = request_session_token() or request.cookies.get(cookie_name('csrf'), '')
        supplied = request.headers.get('X-CSRF-Token', '')
        if not binding or not hmac.compare_digest(supplied.encode('utf-8'), csrf_value(binding).encode('ascii')):
            return jsonify({'success': False, 'error': 'CSRF validation failed'}), 403
        return None

    @app.after_request
    def private_responses(response):
        if cookie_auth_enabled() and (request_session_token() or request.path.startswith('/api/auth/')):
            response.headers['Cache-Control'] = 'no-store'
            response.vary.add('Cookie')
        if cookie_auth_enabled() and request.endpoint == 'auth.logout' and response.status_code == 200:
            set_private_cookie(response, 'session', '', 0)
            set_private_cookie(response, 'csrf', '', 0)
        return response
