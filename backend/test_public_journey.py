"""Local release smoke test. Uses disposable SQLite, never the preview database.

Run: .venv/Scripts/python.exe backend/test_public_journey.py -v
"""
import contextlib
import ast
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class PublicJourneyTest(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(patch.dict(os.environ, {
            'DATABASE_URL': '', 'DATABASE_PATH': str(root / 'journey.db'),
            'FLASK_ENV': 'development', 'SECRET_KEY': 'isolated-test-secret-not-for-deployment',
            'GEMINI_API_KEY': '',
            'RATE_LIMIT_REDIS_URL': '', 'RATE_LIMIT_NAMESPACE': '',
            'TRUSTED_PROXY_CIDRS': '', 'TRUSTED_PROXY_X_FOR': '0', 'TRUSTED_PROXY_X_PROTO': '0',
        }))
        # Legacy backend auth logs contain response details; don't echo them.
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        from app import create_app
        self.app = create_app({'TESTING': True, 'DATABASE': str(root / 'journey.db'), 'UPLOAD_FOLDER': str(root / 'uploads')})
        self.client = self.app.test_client()
        # Storage/authorization fixtures use header-only video bytes. Real ffprobe
        # and validation behavior are tested separately, never bypassed in the app.
        from app.video_validation import probe_video
        self.real_video_probe = probe_video
        self.enterContext(patch('app.video_validation.probe_video', return_value={
            'format': {'duration': '1'}, 'streams': [{'codec_type': 'video', 'codec_name': 'h264', 'width': 16, 'height': 16}]}))

    def register(self, username):
        response = self.client.post('/api/auth/signup', json={
            'username': username, 'email': f'{username}@example.test',
            'password': 'FixtureOnly-Pass123!',
        })
        self.assertEqual(response.status_code, 201, 'fixture registration failed')
        data = response.get_json()
        return {'Authorization': f"Bearer {data['token']}"}, data['user']['id']

    def test_shared_limiter_failure_stops_route_without_leaking_details(self):
        from app.rate_limits import RateLimitUnavailable
        from app.routes.ai import ai_service
        with patch.object(self.app.extensions['rate_limiter'], 'check', side_effect=RateLimitUnavailable('fixture-private')):
            with patch.object(ai_service, 'chat') as chat:
                response = self.client.post('/api/chatbot', json={'query': 'fixture'})
                chat.assert_not_called()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['Retry-After'], '5')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertNotIn('fixture-private', response.get_data(as_text=True))

    def test_explicit_proxy_trust_is_limited_to_configured_peers(self):
        from flask import Flask, request, jsonify
        from app.trusted_proxy import configure_trusted_proxy
        proxy_app = Flask('isolated_proxy')
        proxy_app.config.update(TRUSTED_PROXY_CIDRS='10.20.0.0/24', TRUSTED_PROXY_X_FOR='1', TRUSTED_PROXY_X_PROTO='1')
        configure_trusted_proxy(proxy_app)

        @proxy_app.get('/')
        def details():
            return jsonify({'ip': request.remote_addr, 'secure': request.is_secure, 'host': request.host})

        client = proxy_app.test_client()
        headers = {'X-Forwarded-For': 'spoofed-first-hop, 192.0.2.44', 'X-Forwarded-Proto': 'https', 'X-Forwarded-Host': 'attacker.test'}
        untrusted = client.get('/', headers=headers, environ_overrides={'REMOTE_ADDR': '198.51.100.1'}).get_json()
        self.assertEqual(untrusted, {'ip': '198.51.100.1', 'secure': False, 'host': 'localhost'})
        trusted = client.get('/', headers=headers, environ_overrides={'REMOTE_ADDR': '10.20.0.5'}).get_json()
        self.assertEqual(trusted, {'ip': '192.0.2.44', 'secure': True, 'host': 'localhost'})
        for config in ({'TRUSTED_PROXY_X_FOR': '1'}, {'TRUSTED_PROXY_X_PROTO': '-1'},
                       {'TRUSTED_PROXY_CIDRS': '0.0.0.0/0'}, {'TRUSTED_PROXY_CIDRS': 'not-a-network'}):
            candidate = Flask('bad_proxy')
            candidate.config.update(config)
            with self.assertRaises(ValueError):
                configure_trusted_proxy(candidate)

    def test_endpoint_limits_ignore_spoofed_forwarding_and_preserve_other_budgets(self):
        for index in range(10):
            response = self.client.post('/api/auth/login', json={'username': 'absent', 'password': 'fixture'},
                headers={'X-Forwarded-For': f'198.51.100.{index}'})
            self.assertEqual(response.status_code, 401)
        blocked = self.client.post('/api/auth/login', json={'username': 'absent', 'password': 'fixture'},
            headers={'X-Forwarded-For': '203.0.113.99'})
        self.assertEqual(blocked.status_code, 429)
        self.assertGreater(int(blocked.headers['Retry-After']), 0)
        self.assertEqual(blocked.headers['Cache-Control'], 'no-store')
        self.assertEqual(self.client.post('/api/auth/forgot-password', json={'email': 'absent@example.test'}).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/login', json={'username': 'absent', 'password': 'fixture'},
            environ_overrides={'REMOTE_ADDR': '127.0.0.2'}).status_code, 401)

    def test_rules_price_estimate_does_not_load_unused_model(self):
        from app.routes.ai import ai_service
        with patch('os.path.exists', return_value=True), patch('joblib.load') as load:
            result = ai_service.estimate_price('Toyota', 'Camry', 2026, {})
            self.assertEqual(result, {'value': 19800, 'low': 14850, 'high': 24750, 'currency': 'JOD'})
            load.assert_not_called()

    def test_ai_limits_prevent_provider_calls_and_are_separate(self):
        from app.routes.ai import ai_service
        with patch.object(ai_service, 'chat', return_value='fixture response') as chat:
            for _ in range(10):
                self.assertEqual(self.client.post('/api/chatbot', json={'query': 'fixture'}).status_code, 200)
            self.assertEqual(self.client.post('/api/chatbot', json={'query': 'fixture'}).status_code, 429)
            self.assertEqual(chat.call_count, 10)
        # Separate AI endpoints retain their budget; this malformed request
        # fails validation without making a real provider call.
        self.assertEqual(self.client.post('/api/price-estimate', json={}).status_code, 400)

    def test_admin_limits_do_not_bypass_authentication(self):
        for _ in range(20):
            self.assertEqual(self.client.put('/api/dealers/applications/1/approve').status_code, 401)
        self.assertEqual(self.client.put('/api/dealers/applications/1/approve').status_code, 429)
        self.assertEqual(self.client.put('/api/dealers/applications/1/reject').status_code, 401)

    def test_upload_preflight_does_not_spend_budget(self):
        for _ in range(8):
            self.assertIn(self.client.options('/api/uploads/videos').status_code, (200, 204))
        for _ in range(5):
            self.assertEqual(self.client.post('/api/uploads/videos').status_code, 401)
        self.assertEqual(self.client.post('/api/uploads/videos').status_code, 429)
        self.assertEqual(self.client.post('/api/uploads/images').status_code, 401)

    def test_security_headers_on_errors_and_https(self):
        for path in ('/api/cars', '/api/not-a-route', '/api/auth/verify'):
            response = self.client.get(path)
            self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
            self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy'])
            self.assertIn('camera=()', response.headers['Permissions-Policy'])
            self.assertNotIn('Strict-Transport-Security', response.headers)
        secure = self.client.get('/api/cars', base_url='https://localhost')
        self.assertEqual(secure.headers['Strict-Transport-Security'], 'max-age=31536000')
        self.assertIn("default-src 'none'", secure.headers['Content-Security-Policy'])
        forged = self.client.get('/api/cars', headers={'X-Forwarded-Proto': 'https'})
        self.assertNotIn('Strict-Transport-Security', forged.headers)
        docs = self.client.get('/api/docs/')
        self.assertEqual(docs.status_code, 200)
        self.assertNotIn('default-src', docs.headers['Content-Security-Policy'])

    def test_password_writes_use_werkzeug_default(self):
        from app.db import get_db
        from werkzeug.security import generate_password_hash, check_password_hash
        expected_method = generate_password_hash('fixture-probe').split('$', 1)[0]
        headers, user_id = self.register('hash_default_fixture')

        def check_stored(password):
            with self.app.app_context():
                stored = get_db().execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()['password_hash']
                self.assertTrue(stored.split('$', 1)[0] == expected_method, 'Expected maintained hash method')
                self.assertTrue(check_password_hash(stored, password), 'Stored password must verify')

        check_stored('FixtureOnly-Pass123!')
        response = self.client.patch('/api/auth/profile', headers=headers, json={
            'current_password': 'FixtureOnly-Pass123!', 'password': 'Changed-Fixture123!',
        })
        self.assertEqual(response.status_code, 200)
        check_stored('Changed-Fixture123!')
        with self.app.app_context():
            db = get_db()
            db.execute('INSERT INTO password_resets (token, user_id, expires_at) VALUES (?, ?, ?)',
                       ('fixture-hash-reset', user_id, '2099-01-01 00:00:00'))
            db.commit()
        response = self.client.post('/api/auth/reset-password', json={
            'token': 'fixture-hash-reset', 'password': 'Reset-Fixture123!',
        })
        self.assertEqual(response.status_code, 200)
        check_stored('Reset-Fixture123!')

    def test_legacy_password_upgrades_only_after_successful_login(self):
        from app.db import get_db
        from werkzeug.security import generate_password_hash, check_password_hash
        _, user_id = self.register('legacy_hash_fixture')
        legacy = generate_password_hash('FixtureOnly-Pass123!', method='pbkdf2:sha256:260000')
        with self.app.app_context():
            db = get_db()
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (legacy, user_id))
            db.commit()

        def stored_hash():
            with self.app.app_context():
                return get_db().execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()['password_hash']

        credentials = {'username': 'legacy_hash_fixture', 'password': 'Wrong-Fixture123!'}
        self.assertEqual(self.client.post('/api/auth/login', json=credentials).status_code, 401)
        self.assertTrue(stored_hash() == legacy, 'Failed login must not change hash')
        credentials['password'] = 'FixtureOnly-Pass123!'
        self.assertEqual(self.client.post('/api/auth/login', json=credentials).status_code, 200)
        upgraded = stored_hash()
        self.assertFalse(upgraded.startswith('pbkdf2:sha256:260000$'))
        self.assertTrue(check_password_hash(upgraded, credentials['password']))
        self.assertEqual(self.client.post('/api/auth/login', json=credentials).status_code, 200)
        self.assertTrue(stored_hash() == upgraded, 'Modern hashes must not be rewritten on every login')

    def test_password_upgrade_rolls_back_with_session_failure(self):
        from app.db import get_db
        from werkzeug.security import generate_password_hash
        _, user_id = self.register('rollback_hash_fixture')
        legacy = generate_password_hash('FixtureOnly-Pass123!', method='pbkdf2:sha256:260000')
        with self.app.app_context():
            db = get_db()
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (legacy, user_id))
            db.commit()
        with patch('app.routes.auth.revoke_presented_cookie', side_effect=RuntimeError('Fixture failure')):
            response = self.client.post('/api/auth/login', json={
                'username': 'rollback_hash_fixture', 'password': 'FixtureOnly-Pass123!',
            })
        self.assertEqual(response.status_code, 500)
        with self.app.app_context():
            db = get_db()
            stored = db.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()['password_hash']
            self.assertTrue(stored == legacy, 'Hash upgrade and session creation must be atomic')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM user_sessions WHERE user_id = ?', (user_id,)).fetchone()[0], 1)

    def test_password_upgrade_compare_and_swap_miss_denies_session(self):
        from app.db import get_db
        from unittest.mock import Mock
        from werkzeug.security import generate_password_hash
        _, user_id = self.register('changed_hash_fixture')
        legacy = generate_password_hash('FixtureOnly-Pass123!', method='pbkdf2:sha256:260000')
        with self.app.app_context():
            db = get_db()
            db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (legacy, user_id))
            db.commit()
            wrapped = Mock(wraps=db)

            def execute(sql, params=None):
                if sql.startswith('UPDATE users SET password_hash'):
                    self.assertIn('AND password_hash = ? RETURNING id', sql)
                    return Mock(fetchone=Mock(return_value=None))
                return db.execute(sql, params)

            wrapped.execute.side_effect = execute
            with patch('app.routes.auth.get_db', return_value=wrapped):
                response = self.client.post('/api/auth/login', json={
                    'username': 'changed_hash_fixture', 'password': 'FixtureOnly-Pass123!',
                })
            self.assertEqual(response.status_code, 401)
            wrapped.rollback.assert_called_once()
            self.assertEqual(db.execute('SELECT COUNT(*) FROM user_sessions WHERE user_id = ?', (user_id,)).fetchone()[0], 1)

    def test_password_reset_origin_validation(self):
        from app.frontend_origin import resolve_reset_origin, password_reset_url
        origins = ['https://www.example.test', 'https://example.test']
        self.assertEqual(resolve_reset_origin(None, origins), origins[0])
        self.assertEqual(resolve_reset_origin('https://stg.example.test/', origins), 'https://stg.example.test')
        self.assertEqual(resolve_reset_origin(None, ['http://localhost:3000'], development=True), 'http://localhost:3000')
        for invalid in ('', 'https://a.test,https://b.test', 'https://user:secret@a.test',
                        'https://a.test/account', 'https://a.test?redirect=x', 'https://a.test#x',
                        'javascript:alert(1)', '//a.test', 'https://*.test', 'https://a.test:bad',
                        'https://a.test\\evil', 'https://a.\ntest', 'http://localhost:3000'):
            with self.subTest(case=invalid):
                with self.assertRaises(ValueError):
                    resolve_reset_origin(invalid, origins)
        self.assertEqual(password_reset_url(origins[0], 'fixture+&'),
                         'https://www.example.test/account?reset_token=fixture%2B%26')

    def test_reset_email_uses_canonical_account_route_not_request_host(self):
        import re
        from urllib.parse import urlsplit, parse_qs
        self.register('reset_origin_fixture')
        self.app.config['PASSWORD_RESET_ORIGIN'] = 'https://accounts.example.test'
        with patch('app.routes.auth.send_auth_email', return_value=True) as send:
            response = self.client.post('/api/auth/forgot-password',
                json={'email': 'reset_origin_fixture@example.test'},
                headers={'Host': 'attacker.example', 'Origin': 'https://attacker.example'})
        self.assertEqual(response.status_code, 200)
        send.assert_called_once()
        body = send.call_args.args[2]
        destination = urlsplit(re.search(r'href="([^"]+)"', body).group(1))
        self.assertEqual(destination.scheme, 'https')
        self.assertEqual(destination.netloc, 'accounts.example.test')
        self.assertEqual(destination.path, '/account')
        reset_value = parse_qs(destination.query)['reset_token'][0]
        self.assertTrue(bool(reset_value))
        from app.db import get_db
        with self.app.app_context():
            row = get_db().execute('SELECT token FROM password_resets').fetchone()
            self.assertTrue(row['token'] == reset_value, 'Email must carry the stored reset credential')

    def test_reset_origin_factory_configuration(self):
        from app import create_app
        with patch.dict(os.environ, {'FRONTEND_ORIGIN': 'https://www.example.test,https://example.test'}):
            configured = create_app({'TESTING': True, 'DATABASE': self.app.config['DATABASE'],
                                    'UPLOAD_FOLDER': self.app.config['UPLOAD_FOLDER'],
                                    'PASSWORD_RESET_ORIGIN': None})
        self.assertEqual(configured.config['PASSWORD_RESET_ORIGIN'], 'https://www.example.test')
        self.assertEqual(configured.config['COOKIE_AUTH_ORIGINS'], ['https://www.example.test', 'https://example.test'])

    def enable_cookie_mode(self, secure=False):
        from app import create_app
        self.app = create_app({
            'TESTING': True, 'DATABASE': self.app.config['DATABASE'],
            'UPLOAD_FOLDER': self.app.config['UPLOAD_FOLDER'],
            'COOKIE_AUTH_ENABLED': True, 'SESSION_COOKIE_SECURE': secure,
            'COOKIE_AUTH_ORIGINS': ['http://localhost:3000'],
        })
        self.client = self.app.test_client()

    def cookie_csrf_headers(self, client=None):
        client = client or self.client
        response = client.get('/api/auth/csrf', headers={'Origin': 'http://localhost:3000'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        return {'Origin': 'http://localhost:3000', 'X-CSRF-Token': response.get_json()['csrfToken']}

    def test_cookie_login_mutation_logout_and_csrf_binding(self):
        self.enable_cookie_mode()
        anonymous_csrf = self.cookie_csrf_headers()
        payload = {'username': 'cookie_fixture', 'email': 'cookie@example.test', 'password': 'FixtureOnly-Pass123!'}
        self.assertEqual(self.client.post('/api/auth/signup', json=payload).status_code, 403)
        signup = self.client.post('/api/auth/signup', json=payload, headers=anonymous_csrf)
        self.assertEqual(signup.status_code, 201)
        self.assertNotIn('token', signup.get_json())
        self.assertIn('sessionVersion', signup.get_json())
        cookie = self.client.get_cookie('iw-dev-session')
        self.assertTrue(cookie.http_only)
        self.assertEqual(cookie.same_site, 'Lax')
        self.assertEqual(cookie.path, '/')
        self.assertEqual(self.client.get('/api/auth/verify').status_code, 200)
        listing = {'make': 'Toyota', 'model': 'Camry', 'year': 2021, 'price': 15000}
        self.assertEqual(self.client.post('/api/cars', json=listing, headers=anonymous_csrf).status_code, 403)
        current_csrf = self.cookie_csrf_headers()
        self.assertEqual(self.client.post('/api/cars', json=listing, headers=current_csrf).status_code, 201)
        self.assertEqual(self.client.post('/api/auth/logout', headers=current_csrf).status_code, 200)
        self.assertIsNone(self.client.get_cookie('iw-dev-session'))
        self.assertEqual(self.client.get('/api/auth/verify').status_code, 401)

    def test_cookie_csrf_origin_cors_and_bearer_rejection(self):
        bearer, _ = self.register('cookie_legacy')
        self.enable_cookie_mode()
        self.assertEqual(self.client.get('/api/auth/verify', headers=bearer).status_code, 401)
        csrf = self.cookie_csrf_headers()
        for origin in ('http://evil.example', 'null', ''):
            headers = {**csrf, 'Origin': origin}
            self.assertEqual(self.client.post('/api/auth/logout', headers=headers).status_code, 403)
        other_client = self.app.test_client()
        self.cookie_csrf_headers(other_client)
        self.assertEqual(other_client.post('/api/auth/logout', headers=csrf).status_code, 403)
        response = self.client.options('/api/cars', headers={
            'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'X-CSRF-Token',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'http://localhost:3000')
        self.assertEqual(response.headers['Access-Control-Allow-Credentials'], 'true')
        evil = self.client.get('/api/auth/csrf', headers={'Origin': 'http://evil.example'})
        self.assertEqual(evil.status_code, 403)
        self.assertNotIn('Access-Control-Allow-Origin', evil.headers)
        self.assertEqual(self.client.get('/api/messages/conversations/1').status_code, 403)
        self.assertEqual(self.client.get('/api/messages/conversations/1', headers=csrf).status_code, 401)

    def test_cookie_secure_attributes_and_anonymous_upload_denial(self):
        self.enable_cookie_mode(secure=True)
        csrf = self.cookie_csrf_headers()
        seed = self.client.get_cookie('__Host-iw-csrf')
        self.assertTrue(seed.secure)
        self.assertTrue(seed.http_only)
        self.assertTrue(seed.origin_only)
        self.assertEqual(seed.path, '/')
        # Passing CSRF does not grant authentication.
        self.assertEqual(self.client.post('/api/uploads/images', headers=csrf).status_code, 401)
        self.assertEqual(self.client.post('/api/uploads/videos', headers=csrf).status_code, 401)

    def test_cookie_rotation_and_logout_failure(self):
        from app.routes.auth import get_user_from_token
        from unittest.mock import Mock
        self.enable_cookie_mode()
        account = {'username': 'rotate_fixture', 'email': 'rotate@example.test', 'password': 'FixtureOnly-Pass123!'}
        signup = self.client.post('/api/auth/signup', json=account, headers=self.cookie_csrf_headers())
        self.assertEqual(signup.status_code, 201)
        old_cookie = self.client.get_cookie('iw-dev-session').value
        login = self.client.post('/api/auth/login', json=account, headers=self.cookie_csrf_headers())
        self.assertEqual(login.status_code, 200)
        second_cookie = self.client.get_cookie('iw-dev-session').value
        self.assertTrue(old_cookie != second_cookie)
        with self.app.app_context():
            self.assertIsNone(get_user_from_token(old_cookie))
        old_version = login.get_json()['sessionVersion']
        changed = self.client.patch('/api/auth/profile', headers=self.cookie_csrf_headers(), json={
            'current_password': account['password'], 'password': 'Rotated-Fixture123!',
        })
        self.assertEqual(changed.status_code, 200)
        self.assertNotIn('token', changed.get_json())
        self.assertNotEqual(changed.get_json()['sessionVersion'], old_version)
        with self.app.app_context():
            self.assertIsNone(get_user_from_token(second_cookie))
        self.assertEqual(self.client.get('/api/auth/verify', headers={'X-Session-Version': old_version}).status_code, 403)
        current = self.client.get('/api/auth/verify')
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.get_json()['sessionVersion'], changed.get_json()['sessionVersion'])
        csrf = self.cookie_csrf_headers()
        database = Mock()
        database.execute.side_effect = RuntimeError('fixture failure')
        with patch('app.routes.auth.get_db', return_value=database), self.assertLogs('app.routes.auth', level='ERROR'):
            failed = self.client.post('/api/auth/logout', headers=csrf)
        self.assertEqual(failed.status_code, 500)
        self.assertIsNotNone(self.client.get_cookie('iw-dev-session'))
        self.assertEqual(self.client.get('/api/auth/verify').status_code, 200)

    def test_login_logout_and_password_reset_session_contract(self):
        from app.db import get_db
        initial, user_id = self.register('session_fixture')
        logged_in = self.client.post('/api/auth/login', json={
            'username': 'session_fixture', 'password': 'FixtureOnly-Pass123!',
        })
        self.assertEqual(logged_in.status_code, 200)
        second = {'Authorization': f"Bearer {logged_in.get_json()['token']}"}
        from app.session_tokens import hash_session_token
        with self.app.app_context():
            stored = get_db().execute('SELECT token FROM user_sessions WHERE user_id = ?', (user_id,)).fetchall()
            self.assertTrue(hash_session_token(logged_in.get_json()['token']) in [row['token'] for row in stored])
        self.assertNotEqual(initial, second)
        self.assertEqual(self.client.get('/api/auth/verify', headers=second).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/logout', headers=initial).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/verify', headers=initial).status_code, 401)
        self.assertEqual(self.client.get('/api/auth/verify', headers=second).status_code, 200)
        # Seed only the disposable database; never send email or reveal real tokens.
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO password_resets (token, user_id, expires_at) VALUES (?, ?, ?)",
                       ('fixture-reset-token', user_id, '2099-01-01 00:00:00'))
            db.commit()
        payload = {'token': 'fixture-reset-token', 'password': 'Replacement-Pass123!'}
        reset_client = self.app.test_client()
        reset_client.environ_base['REMOTE_ADDR'] = '127.0.0.2'
        self.assertEqual(reset_client.post('/api/auth/reset-password', json=payload).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/verify', headers=second).status_code, 401)
        self.assertEqual(reset_client.post('/api/auth/reset-password', json=payload).status_code, 400)
        self.assertEqual(self.client.post('/api/auth/login', json={
            'username': 'session_fixture', 'password': 'FixtureOnly-Pass123!',
        }).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/login', json={
            'username': 'session_fixture', 'password': 'Replacement-Pass123!',
        }).status_code, 200)

    def test_google_signin_new_and_returning_users(self):
        from unittest.mock import Mock
        from app.routes import auth
        from app.db import get_db
        verifier = Mock()
        verifier.verify_oauth2_token.return_value = {
            'sub': 'fixture-google-subject', 'email': 'google-fixture@example.test',
            'email_verified': True,
        }
        with patch.object(auth, 'HAS_GOOGLE_AUTH', True), \
                patch.object(auth, 'GOOGLE_CLIENT_ID', 'fixture-client'), \
                patch.object(auth, 'id_token', verifier, create=True), \
                patch.object(auth, 'google_requests', Mock(), create=True):
            first = self.client.post('/api/auth/google', json={'credential': 'fixture-credential'})
            self.assertEqual(first.status_code, 200)
            second = self.client.post('/api/auth/google', json={'credential': 'fixture-credential'})
            self.assertEqual(second.status_code, 200)
            self.assertEqual(first.get_json()['user']['id'], second.get_json()['user']['id'])
            headers = {'Authorization': f"Bearer {second.get_json()['token']}"}
            self.assertEqual(self.client.get('/api/auth/verify', headers=headers).status_code, 200)
            verifier.verify_oauth2_token.side_effect = ValueError('invalid fixture credential')
            with self.assertLogs(auth.logger, level='WARNING'):
                self.assertEqual(self.client.post('/api/auth/google', json={'credential': 'bad-fixture'}).status_code, 401)
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) FROM users').fetchone()[0], 1)
            from app.session_tokens import hash_session_token
            stored = [row['token'] for row in get_db().execute('SELECT token FROM user_sessions').fetchall()]
            self.assertTrue(hash_session_token(first.get_json()['token']) in stored)
            self.assertTrue(hash_session_token(second.get_json()['token']) in stored)

    def test_session_hash_storage_and_digest_replay_rejection(self):
        from app.db import get_db
        from app.session_tokens import hash_session_token
        headers, user_id = self.register('hash_fixture')
        raw_token = headers['Authorization'].removeprefix('Bearer ')
        with self.app.app_context():
            stored = get_db().execute('SELECT token FROM user_sessions WHERE user_id = ?', (user_id,)).fetchone()['token']
        self.assertTrue(stored == hash_session_token(raw_token), 'Session must store the digest')
        self.assertTrue(stored != raw_token, 'Session must not store raw credentials')
        stolen_digest = {'Authorization': f'Bearer {stored}'}
        self.assertEqual(self.client.get('/api/auth/verify', headers=stolen_digest).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/logout', headers=stolen_digest).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/verify', headers=headers).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/logout', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/verify', headers=headers).status_code, 401)

    def test_legacy_session_compatibility_and_input_validation(self):
        from app.db import get_db
        from app.session_tokens import session_lookup_values
        _, user_id = self.register('legacy_fixture')
        with self.app.app_context():
            db = get_db()
            db.execute('INSERT INTO user_sessions (token, user_id, expires_at) VALUES (?, ?, ?)',
                       ('legacy-fixture-token', user_id, '2099-01-01 00:00:00'))
            db.commit()
        headers = {'Authorization': 'Bearer legacy-fixture-token'}
        self.assertEqual(self.client.get('/api/auth/verify', headers=headers).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/logout', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/verify', headers=headers).status_code, 401)
        for value in (None, '', ' ', 'x' * 129, 'sha256:fixture-digest'):
            self.assertIsNone(session_lookup_values(value))

    def assert_writes_rejected(self, headers):
        with patch('app.routes.system.init_cloudinary') as cloud:
            response = self.client.post('/api/cars', headers=headers, json={
                'make': 'Toyota', 'model': 'Camry', 'year': 2021, 'price': 15000,
            })
            self.assertEqual(response.status_code, 401)
            for kind, extension in [('images', 'png'), ('videos', 'mp4')]:
                response = self.client.post(f'/api/uploads/{kind}', headers=headers,
                    data={'file': (io.BytesIO(b'authorization fixture'), f'test.{extension}')})
                self.assertEqual(response.status_code, 401)
            cloud.assert_not_called()
        self.assertEqual(self.client.get('/api/cars').get_json()['total'], 0)
        self.assertEqual(list(Path(self.app.config['UPLOAD_FOLDER']).glob('*')), [])

    def test_auth_logging_accepts_only_fixed_event_messages(self):
        from app.routes import auth
        tree = ast.parse(Path(auth.__file__).read_text(encoding='utf-8'))
        log_calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            self.assertFalse(isinstance(node.func, ast.Name) and node.func.id == 'print',
                             'Auth must not print request or exception data')
            if (isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == 'logger'):
                log_calls.append(node)
                self.assertIn(node.func.attr, ('info', 'warning', 'error'))
                self.assertEqual(len(node.args), 1)
                self.assertEqual(node.keywords, [])
                self.assertIsInstance(node.args[0], ast.Constant)
                self.assertTrue(node.args[0].value.startswith('auth.'))
        self.assertGreater(len(log_calls), 0)

    def test_verification_does_not_print_session_or_identity(self):
        seller, _ = self.register('log_fixture_seller')
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            self.assertEqual(self.client.get('/api/auth/verify', headers=seller).status_code, 200)
            self.assertEqual(self.client.get('/api/auth/verify').status_code, 401)
        self.assertEqual(output.getvalue(), '', 'Verification must not print sensitive data')

    def test_database_explicit_logs_are_constant(self):
        from app import db
        tree = ast.parse(Path(db.__file__).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                self.assertEqual(len(node.args), 1)
                self.assertIsInstance(node.args[0], ast.Constant)
                self.assertIsInstance(node.args[0].value, str)

    def test_unexpected_errors_are_safe_and_http_errors_keep_semantics(self):
        from werkzeug.exceptions import RequestEntityTooLarge

        @self.app.get('/api/test-unexpected')
        def unexpected():
            raise RuntimeError('private-fixture-value')

        @self.app.get('/api/test-size-limit')
        def size_limit():
            raise RequestEntityTooLarge()

        with self.assertLogs(self.app.logger, level='ERROR') as captured:
            response = self.client.get('/api/test-unexpected')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {'success': False, 'error': 'Internal server error'})
        self.assertEqual([r.getMessage() for r in captured.records], ['request.unexpected_error'])
        self.assertTrue(all(r.exc_info is None for r in captured.records))
        self.assertEqual(self.client.get('/api/does-not-exist').status_code, 404)
        response = self.client.post('/api/test-unexpected')
        self.assertEqual(response.status_code, 405)
        self.assertIn('GET', response.headers['Allow'])
        self.assertEqual(self.client.get('/api/test-size-limit').status_code, 413)

    def test_health_errors_are_safe(self):
        from app.services.ai_service import ai_service
        with patch('app.routes.system.get_db', side_effect=RuntimeError('private-fixture-value')), \
                patch.object(ai_service, 'gemini_model', None), \
                patch.object(ai_service, '_init_error', 'private-fixture-value', create=True):
            response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'degraded')
        self.assertEqual(data['database_error'], 'Database unavailable')
        self.assertEqual(data['ai_error'], 'AI unavailable')

    def test_ai_provider_failures_do_not_disclose_details(self):
        import json
        from unittest.mock import Mock
        from app.services.ai_service import AIService
        with patch.object(AIService, '_init_gemini'):
            service = AIService()
            for failure in ('private-fixture-value', 'quota private-fixture-value',
                            'safety private-fixture-value', 'invalid api key private-fixture-value'):
                with self.subTest(category=failure.split()[0]):
                    service.gemini_model = Mock()
                    service.gemini_model.generate_content.side_effect = RuntimeError(failure)
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                        results = [service.chat('test question', []),
                                   service.chat('', [], 'aW1hZ2U='),
                                   service.analyze_image('aW1hZ2U='),
                                   service.listing_assistant('test listing', [])]
                    self.assertNotIn('private-fixture-value', json.dumps(results) + output.getvalue())
                    self.assertTrue(results[2]['error'])
                    self.assertIsNone(results[3]['listing_data'])
            service.gemini_model = None
            service._init_error = 'private-fixture-value'
            results = [service.chat('test', []), service.analyze_image('aW1hZ2U=')]
            self.assertNotIn('private-fixture-value', json.dumps(results))

    def test_ai_malformed_vision_and_success_contracts(self):
        from unittest.mock import Mock
        from app.services.ai_service import AIService
        with patch.object(AIService, '_init_gemini'):
            service = AIService()
        service.gemini_model = Mock()
        service.gemini_model.generate_content.return_value.text = 'private-fixture-value'
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = service.analyze_image('aW1hZ2U=')
        self.assertTrue(result['error'])
        self.assertNotIn('private-fixture-value', output.getvalue())
        service.gemini_model.generate_content.return_value.text = 'A useful answer'
        self.assertEqual(service.chat('test', []), {'text': 'A useful answer', 'listing_data': None})
        service.gemini_model.generate_content.return_value.text = '{"make":"Toyota","model":"Camry"}'
        self.assertEqual(service.analyze_image('aW1hZ2U='), {'make': 'Toyota', 'model': 'Camry', 'error': False})

    def test_ai_explicit_logs_never_interpolate_data(self):
        from app.services import ai_service
        from app.routes import ai
        for module in (ai_service, ai):
            tree = ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    self.assertEqual(len(node.args), 1)
                    value = node.args[0]
                    self.assertTrue(isinstance(value, ast.Constant) or (
                        isinstance(value, ast.JoinedStr) and all(isinstance(v, ast.Constant) for v in value.values)))
                if isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, ('print_exc', 'print_exception'))

    def test_ai_initialization_failure_is_safe_without_network(self):
        from unittest.mock import Mock
        from app.services import ai_service as module
        provider = Mock()
        provider.configure.side_effect = RuntimeError('private-fixture-value')
        output = io.StringIO()
        with patch.object(module, 'GEMINI_AVAILABLE', True), patch.object(module, 'genai', provider), \
                patch.dict(os.environ, {'GEMINI_API_KEY': 'dummy-test-value'}), \
                contextlib.redirect_stdout(output):
            service = module.AIService()
        self.assertEqual(service._init_error, 'AI initialization failed')
        self.assertIsNone(service.gemini_model)
        self.assertNotIn('private-fixture-value', output.getvalue())
        provider.list_models.assert_not_called()

    def test_non_ai_routes_do_not_print_dynamic_data_or_tracebacks(self):
        from app.routes import cars
        root = Path(cars.__file__).parent
        for filename in ('cars.py', 'favorites.py', 'dealers.py', 'messages.py',
                         'listings.py', 'reviews.py', 'system.py'):
            tree = ast.parse((root / filename).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    self.assertEqual(len(node.args), 1, filename)
                    self.assertIsInstance(node.args[0], ast.Constant, filename)
                if isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, ('print_exc', 'print_exception'), filename)

    def test_listing_and_favorite_write_failures_are_safe(self):
        from unittest.mock import Mock
        database = Mock()
        database.execute.side_effect = RuntimeError('private-fixture-value')
        with patch('app.routes.cars.require_auth', return_value={'id': 1}), \
                patch('app.routes.cars.get_db', return_value=database):
            response = self.client.post('/api/cars', json={
                'make': 'Toyota', 'model': 'Camry', 'year': 2021, 'price': 15000,
            })
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()['error'], 'Failed to create listing')
        database.rollback.assert_called_once()
        with patch('app.routes.favorites.get_user_from_token', return_value={'id': 1}), \
                patch('app.routes.favorites.get_db', return_value=database), \
                patch('app.routes.favorites.ensure_favorites_table'):
            added = self.client.post('/api/favorites', json={'car_id': 1})
            removed = self.client.delete('/api/favorites/1')
        self.assertEqual(added.status_code, 500)
        self.assertEqual(removed.status_code, 500)
        self.assertEqual(added.get_json()['error'], 'Failed to add favorite')
        self.assertEqual(removed.get_json()['error'], 'Failed to remove favorite')

    def test_auth_error_logs_do_not_include_exception_details(self):
        from app.routes import auth
        from unittest.mock import Mock
        database = Mock()
        database.execute.side_effect = RuntimeError('private-fixture-value')
        with self.app.app_context(), patch.object(auth, 'get_db', return_value=database):
            with self.assertLogs(auth.logger, level='ERROR') as captured:
                self.assertIsNone(auth.get_user_from_token('fixture-session-value'))
        self.assertEqual([record.getMessage() for record in captured.records],
                         ['auth.session_lookup_failed'])
        with patch.object(auth, 'SMTP_HOST', 'smtp.example.test'), patch.object(auth, 'SMTP_USER', 'fixture'), \
                patch.object(auth.smtplib, 'SMTP', side_effect=RuntimeError('private-fixture-value')):
            with self.assertLogs(auth.logger, level='ERROR') as captured:
                self.assertFalse(auth.send_auth_email('recipient@example.test', 'subject', 'reset fixture'))
        self.assertEqual([record.getMessage() for record in captured.records], ['auth.email_failed'])

    def test_auth_email_verifies_tls_before_login_and_uses_socket_timeout(self):
        import ssl
        from unittest.mock import call, ANY
        from app.routes import auth
        with patch.object(auth, 'SMTP_HOST', 'smtp.example.test'), \
                patch.object(auth, 'SMTP_USER', 'fixture'), \
                patch.object(auth, 'SMTP_PASS', 'fixture-password'), \
                patch.object(auth.smtplib, 'SMTP') as smtp:
            self.assertTrue(auth.send_auth_email('recipient@example.test', 'subject', 'reset fixture'))
            smtp.assert_called_once_with('smtp.example.test', auth.SMTP_PORT, timeout=10)
            server = smtp.return_value.__enter__.return_value
            context = server.starttls.call_args.kwargs['context']
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)
            self.assertEqual(server.method_calls, [call.starttls(context=context),
                             call.login('fixture', 'fixture-password'), call.send_message(ANY)])

    def test_auth_email_tls_failure_never_sends_credentials_or_retries(self):
        import ssl
        from app.routes import auth
        with patch.object(auth, 'SMTP_HOST', 'smtp.example.test'), \
                patch.object(auth, 'SMTP_USER', 'fixture'), \
                patch.object(auth.smtplib, 'SMTP') as smtp:
            server = smtp.return_value.__enter__.return_value
            server.starttls.side_effect = ssl.SSLCertVerificationError('private-fixture-detail')
            with self.assertLogs(auth.logger, level='ERROR') as captured:
                self.assertFalse(auth.send_auth_email('recipient@example.test', 'subject', 'reset fixture'))
            smtp.assert_called_once()
            server.login.assert_not_called()
            server.send_message.assert_not_called()
            self.assertEqual([record.getMessage() for record in captured.records], ['auth.email_failed'])

    def test_forgot_password_smtp_timeout_preserves_generic_response(self):
        from app.routes import auth
        self.register('smtp_timeout')
        with patch.object(auth, 'SMTP_HOST', 'smtp.example.test'), \
                patch.object(auth, 'SMTP_USER', 'fixture'), \
                patch.object(auth.smtplib, 'SMTP', side_effect=TimeoutError('private-fixture-detail')) as smtp:
            with self.assertLogs(auth.logger, level='ERROR') as captured:
                known = self.client.post('/api/auth/forgot-password', json={'email': 'smtp_timeout@example.test'})
            unknown = self.client.post('/api/auth/forgot-password', json={'email': 'absent@example.test'})
            self.assertEqual(known.status_code, 200)
            self.assertEqual(unknown.status_code, 200)
            self.assertEqual(known.get_json(), unknown.get_json())
            smtp.assert_called_once()
            self.assertEqual([record.getMessage() for record in captured.records], ['auth.email_failed'])

    def test_auth_email_missing_configuration_does_not_connect(self):
        from app.routes import auth
        with patch.object(auth, 'SMTP_HOST', ''), patch.object(auth.smtplib, 'SMTP') as smtp:
            with self.assertLogs(auth.logger, level='WARNING'):
                self.assertFalse(auth.send_auth_email('recipient@example.test', 'subject', 'reset fixture'))
            smtp.assert_not_called()

    def test_missing_and_invalid_sessions_cannot_write(self):
        self.assert_writes_rejected({})
        self.assert_writes_rejected({'Authorization': 'Bearer invalid-fixture-token'})

    def test_revoked_and_expired_sessions_cannot_write(self):
        revoked, _ = self.register('revoked_seller')
        self.assertEqual(self.client.post('/api/auth/logout', headers=revoked).status_code, 200)
        self.assert_writes_rejected(revoked)
        expired, user_id = self.register('expired_seller')
        from app.db import get_db
        with self.app.app_context():
            db = get_db()
            db.execute("UPDATE user_sessions SET expires_at = '2000-01-01 00:00:00' WHERE user_id = ?", (user_id,))
            db.commit()
        self.assert_writes_rejected(expired)

    def test_preflight_remains_public(self):
        for endpoint in ['/api/cars', '/api/uploads/images', '/api/uploads/videos']:
            response = self.client.options(endpoint, headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'authorization',
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn('POST', response.headers['Access-Control-Allow-Methods'])

    def test_authenticated_uploads_keep_local_response_contract(self):
        seller, _ = self.register('upload_seller')
        from PIL import Image
        image = io.BytesIO()
        Image.new('RGB', (2, 2), 'blue').save(image, format='PNG')
        # Video fixture proves header/storage handling, not codec playability.
        fixtures = {'png': image.getvalue(), 'mp4': b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42'}
        with patch('app.routes.system.init_cloudinary', return_value=False):
            for kind, extension in [('images', 'png'), ('videos', 'mp4')]:
                response = self.client.post(f'/api/uploads/{kind}', headers=seller,
                    data={'file': (io.BytesIO(fixtures[extension]), f'test.{extension}')})
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertTrue(data['success'])
                self.assertTrue(data['path'].startswith(f'/api/uploads/{kind}/'))
                self.assertTrue((Path(self.app.config['UPLOAD_FOLDER']) / data['filename']).is_file())

    def test_upload_rejections_do_not_call_storage(self):
        seller, _ = self.register('media_validation')
        from PIL import Image
        image = io.BytesIO()
        Image.new('RGB', (2, 2)).save(image, format='PNG')
        with patch('app.routes.system.init_cloudinary') as storage:
            for filename, content in [('fake.png', b'<script>fixture</script>'),
                                      ('empty.png', b''), ('wrong.jpg', image.getvalue()),
                                      ('truncated.png', image.getvalue()[:30])]:
                response = self.client.post('/api/uploads/images', headers=seller,
                    data={'file': (io.BytesIO(content), filename)})
                self.assertEqual(response.status_code, 400)
            response = self.client.post('/api/uploads/videos', headers=seller,
                data={'file': (io.BytesIO(b'not a movie'), 'movie.mp4')})
            self.assertEqual(response.status_code, 400)
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(image.getvalue()), 'image.png', 'text/html')})
            self.assertEqual(response.status_code, 400)
            self.app.config['IMAGE_UPLOAD_MAX_BYTES'] = 10
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(image.getvalue()), 'image.png')})
            self.assertEqual(response.status_code, 400)
            storage.assert_not_called()
        self.assertFalse(any(Path(self.app.config['UPLOAD_FOLDER']).iterdir()))

    def test_real_video_validation_through_upload_route(self):
        import shutil
        import subprocess
        encoder = os.environ.get('FFMPEG_PATH') or shutil.which('ffmpeg')
        probe = os.environ.get('FFPROBE_PATH') or shutil.which('ffprobe')
        if not encoder or not probe:
            if os.environ.get('REQUIRE_VIDEO_TOOLS') == '1':
                self.fail('Required video tools missing')
            self.skipTest('Real video tools unavailable')
        seller, _ = self.register('real_video')
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.app.config['FFPROBE_PATH'] = probe
        with patch('app.video_validation.probe_video', side_effect=self.real_video_probe), patch('app.routes.system.init_cloudinary', return_value=False):
            for duration, expected in ((1, 200), (121, 400)):
                path = root / f'video-{duration}.mp4'
                subprocess.run([encoder, '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=32x32:r=1',
                                '-t', str(duration), '-c:v', 'mpeg4', '-threads', '1', str(path)],
                               timeout=15, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                response = self.client.post('/api/uploads/videos', headers=seller,
                    data={'file': (io.BytesIO(path.read_bytes()), 'video.mp4')})
                self.assertEqual(response.status_code, expected)
            self.assertEqual(len(list(Path(self.app.config['UPLOAD_FOLDER']).glob('*.mp4'))), 1)

    def test_video_probe_failures_precede_storage_and_reservations(self):
        seller, _ = self.register('video_probe')
        from app.video_validation import VideoValidatorUnavailable
        header = b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42'
        with patch('app.routes.system.init_cloudinary') as storage, patch('app.routes.system.reserve_upload') as quota:
            with patch('app.video_validation.probe_video', side_effect=VideoValidatorUnavailable('private-path')):
                response = self.client.post('/api/uploads/videos', headers=seller, data={'file': (io.BytesIO(header), 'video.mp4')})
                self.assertEqual(response.status_code, 503)
                self.assertNotIn('private-path', response.get_data(as_text=True))
            with patch('app.video_validation.probe_video', return_value={'format': {'duration': '999'}, 'streams': []}):
                response = self.client.post('/api/uploads/videos', headers=seller, data={'file': (io.BytesIO(header), 'video.mp4')})
                self.assertEqual(response.status_code, 400)
            storage.assert_not_called(); quota.assert_not_called()

    def test_video_size_and_animation_limits_precede_storage(self):
        seller, _ = self.register('media_limits')
        from PIL import Image
        animation = io.BytesIO()
        frames = [Image.new('RGB', (1, 1), (index, 0, 0)) for index in range(101)]
        frames[0].save(animation, format='GIF', save_all=True, append_images=frames[1:])
        self.app.config['VIDEO_UPLOAD_MAX_BYTES'] = 16
        with patch('app.routes.system.init_cloudinary') as storage:
            response = self.client.post('/api/uploads/videos', headers=seller,
                data={'file': (io.BytesIO(b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42'), 'large.mp4')})
            self.assertEqual(response.status_code, 400)
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(animation.getvalue()), 'animation.gif')})
            self.assertEqual(response.status_code, 400)
            storage.assert_not_called()

    def test_development_fallback_rewinds_after_cloud_failure(self):
        seller, _ = self.register('media_fallback')
        from PIL import Image
        image = io.BytesIO()
        Image.new('RGB', (2, 2)).save(image, format='PNG')
        self.app.config['LOCAL_UPLOADS_ALLOWED'] = True
        def upload(file, **kwargs):
            file.read()
            raise RuntimeError('fixture cloud failure')
        with patch('app.routes.system.init_cloudinary', return_value=True), \
                patch('app.routes.system.cloudinary.uploader.upload', side_effect=upload):
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(image.getvalue()), 'fixture.png')})
        self.assertEqual(response.status_code, 200)
        saved = Path(self.app.config['UPLOAD_FOLDER']) / response.get_json()['filename']
        self.assertEqual(saved.read_bytes(), image.getvalue())

    def test_upload_dimensions_and_multiple_files_rejected(self):
        seller, _ = self.register('media_dimensions')
        from PIL import Image
        from werkzeug.datastructures import MultiDict
        image = io.BytesIO()
        Image.new('RGB', (10001, 1)).save(image, format='PNG')
        with patch('app.routes.system.init_cloudinary') as storage:
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(image.getvalue()), 'wide.png')})
            self.assertEqual(response.status_code, 400)
            response = self.client.post('/api/uploads/images', headers=seller,
                data=MultiDict([('file', (io.BytesIO(b'a'), 'a.png')), ('file', (io.BytesIO(b'b'), 'b.png'))]))
            self.assertEqual(response.status_code, 400)
            storage.assert_not_called()

    def test_hosted_uploads_never_fall_back_to_local_disk(self):
        seller, _ = self.register('hosted_media')
        from PIL import Image
        image = io.BytesIO()
        Image.new('RGB', (2, 2)).save(image, format='PNG')
        self.app.config['LOCAL_UPLOADS_ALLOWED'] = False
        fixtures = [('images', 'png', image.getvalue()),
                    ('videos', 'mp4', b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42')]
        for configured in (False, True):
            with patch('app.routes.system.init_cloudinary', return_value=configured), \
                    patch('app.routes.system.cloudinary.uploader.upload', side_effect=RuntimeError('fixture-private')):
                for kind, extension, payload in fixtures:
                    response = self.client.post(f'/api/uploads/{kind}', headers=seller,
                        data={'file': (io.BytesIO(payload), f'fixture.{extension}')})
                    self.assertEqual(response.status_code, 503)
                    self.assertNotIn('fixture-private', response.get_data(as_text=True))
        self.assertFalse(any(Path(self.app.config['UPLOAD_FOLDER']).iterdir()))

    def test_cloud_upload_receives_validated_stream_from_start(self):
        seller, _ = self.register('cloud_media')
        from PIL import Image
        image = io.BytesIO()
        Image.new('RGB', (2, 2)).save(image, format='PNG')
        self.app.config['LOCAL_UPLOADS_ALLOWED'] = False
        def upload(file, **kwargs):
            self.assertTrue(file.read() == image.getvalue(), 'Validation must rewind upload')
            self.assertEqual(kwargs['resource_type'], 'image')
            return {'secure_url': 'https://example.test/image.png', 'public_id': 'fixture/image'}
        with patch('app.routes.system.init_cloudinary', return_value=True), \
                patch('app.routes.system.cloudinary.uploader.upload', side_effect=upload):
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(image.getvalue()), 'fixture.png')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['url'], 'https://example.test/image.png')

    def enable_asset_ledger(self):
        from app.db import get_db
        migration = Path(__file__).parent / 'migrations' / '001_media_assets.sql'
        with self.app.app_context():
            get_db().executescript(migration.read_text(encoding='utf-8'))
        self.app.config['MEDIA_ASSET_LEDGER_ENABLED'] = True

    def ledger_image(self):
        from PIL import Image
        image = io.BytesIO()
        Image.new('RGB', (2, 2)).save(image, format='PNG')
        return image.getvalue()

    def test_asset_ledger_disabled_preserves_existing_upload_contract(self):
        seller, _ = self.register('ledger_disabled')
        with patch('app.routes.system.init_cloudinary', return_value=False):
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('assetId', response.get_json())
        from app.db import get_db
        with self.app.app_context():
            self.assertIsNone(get_db().execute("SELECT name FROM sqlite_master WHERE name='media_assets'").fetchone())

    def test_asset_ledger_missing_migration_fails_before_storage(self):
        seller, _ = self.register('ledger_missing')
        self.app.config['MEDIA_ASSET_LEDGER_ENABLED'] = True
        with patch('app.routes.system.init_cloudinary') as storage:
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('url', response.get_json())
            storage.assert_not_called()
        self.assertFalse(any(Path(self.app.config['UPLOAD_FOLDER']).iterdir()))

    def test_asset_ledger_records_session_owner_not_submitted_identity(self):
        seller, owner_id = self.register('ledger_owner')
        self.enable_asset_ledger()
        image = self.ledger_image()
        with patch('app.routes.system.init_cloudinary', return_value=False):
            response = self.client.post('/api/uploads/images', headers=seller, data={
                'file': (io.BytesIO(image), 'fixture.png'), 'owner_id': '999999', 'assetId': 'forged'})
        self.assertEqual(response.status_code, 200)
        asset_id = response.get_json()['assetId']
        self.assertNotEqual(asset_id, 'forged')
        from app.db import get_db
        with self.app.app_context():
            row = get_db().execute('SELECT * FROM media_assets WHERE id = ?', (asset_id,)).fetchone()
            self.assertEqual(row['owner_id'], owner_id)
            self.assertEqual(row['source_bytes'], len(image))
            self.assertEqual(row['delivery_url'], response.get_json()['url'])
            self.assertEqual(row['provider'], 'local')

    def test_cloud_ledger_unique_identity_cannot_be_claimed_by_another_user(self):
        seller, owner_id = self.register('cloud_ledger_owner')
        outsider, _ = self.register('cloud_ledger_other')
        self.enable_asset_ledger()
        with patch.dict(os.environ, {'CLOUDINARY_CLOUD_NAME': 'isolated-fixture'}), \
                patch('app.routes.system.init_cloudinary', return_value=True), \
                patch('app.routes.system.cloudinary.uploader.upload', return_value={
                    'secure_url': 'https://example.test/image.png', 'public_id': 'fixture/image'}):
            success = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
            self.assertEqual(success.status_code, 200)
            rejected = self.client.post('/api/uploads/images', headers=outsider,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
        self.assertEqual(rejected.status_code, 503)
        self.assertNotIn('url', rejected.get_json())
        self.assertFalse(any(Path(self.app.config['UPLOAD_FOLDER']).iterdir()))
        from app.db import get_db
        with self.app.app_context():
            rows = get_db().execute('SELECT * FROM media_assets').fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['owner_id'], owner_id)

    def test_asset_ledger_video_and_database_failure(self):
        seller, _ = self.register('ledger_video')
        self.enable_asset_ledger()
        from unittest.mock import Mock
        video = b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42'
        with patch('app.routes.system.init_cloudinary', return_value=False):
            response = self.client.post('/api/uploads/videos', headers=seller,
                data={'file': (io.BytesIO(video), 'fixture.mp4')})
        self.assertEqual(response.status_code, 200)
        from app.db import get_db
        with self.app.app_context():
            row = get_db().execute('SELECT * FROM media_assets').fetchone()
            self.assertEqual(row['resource_type'], 'video')
        failing = Mock()
        failing.execute.side_effect = RuntimeError('fixture-private-details')
        with patch('app.routes.system.check_ledger_ready', return_value=True), \
                patch('app.routes.system.init_cloudinary', return_value=True), \
                patch('app.routes.system.cloudinary.uploader.upload', return_value={
                    'secure_url': 'https://example.test/image.png', 'public_id': 'fixture/image'}), \
                patch.dict(os.environ, {'CLOUDINARY_CLOUD_NAME': 'isolated-fixture'}), \
                patch('app.media_assets.get_db', return_value=failing):
            response = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('fixture-private-details', response.get_data(as_text=True))
        self.assertNotIn('url', response.get_json())
        failing.rollback.assert_called_once()
        self.assertEqual(len(list(Path(self.app.config['UPLOAD_FOLDER']).iterdir())), 1)

    def test_asset_lookup_is_private_and_rollout_gated(self):
        seller, _ = self.register('lookup_owner')
        outsider, _ = self.register('lookup_other')
        self.enable_asset_ledger()
        with patch('app.routes.system.init_cloudinary', return_value=False):
            uploaded = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')}).get_json()
        endpoint = f"/api/uploads/assets/{uploaded['assetId']}"
        self.assertEqual(self.client.get(endpoint).status_code, 401)
        response = self.client.get(endpoint, headers=seller)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.get_json()['asset']['url'], uploaded['url'])
        self.assertNotIn('owner_id', response.get_json()['asset'])
        denied = self.client.get(endpoint, headers=outsider)
        missing = self.client.get('/api/uploads/assets/' + '0' * 32, headers=outsider)
        self.assertEqual(denied.status_code, 404)
        self.assertEqual(denied.get_json(), missing.get_json())
        self.assertEqual(self.client.get('/api/uploads/assets/invalid', headers=seller).status_code, 404)
        self.app.config['MEDIA_ASSET_LEDGER_ENABLED'] = False
        self.assertEqual(self.client.get(endpoint, headers=seller).status_code, 404)

    def test_uploaded_asset_listing_create_reload_edit_remove_roundtrip(self):
        seller, _ = self.register('asset_flow')
        self.enable_asset_ledger()
        with patch('app.routes.system.init_cloudinary', return_value=False):
            uploaded = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')}).get_json()
        item = {'type': 'image', 'url': uploaded['url'], 'assetId': uploaded['assetId']}
        created = self.client.post('/api/cars', headers=seller, json={
            'make': 'Toyota', 'model': 'Camry', 'image': uploaded['url'],
            'galleryImages': [uploaded['url']], 'mediaGallery': [item]})
        self.assertEqual(created.status_code, 201)
        endpoint = f"/api/cars/{created.get_json()['id']}"
        self.assertEqual(self.client.get(endpoint).get_json()['car']['mediaGallery'], [item])
        edited = self.client.patch(endpoint, headers=seller, json={'price': 15000, 'mediaGallery': [item]})
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.get_json()['car']['mediaGallery'], [item])
        cleared = self.client.patch(endpoint, headers=seller, json={
            'image': '', 'videoUrl': '', 'galleryImages': [], 'mediaGallery': []})
        self.assertEqual(cleared.status_code, 200)
        self.assertEqual(self.client.get(endpoint).get_json()['car']['media_gallery'], [])
        self.assertEqual(self.client.get('/api/uploads/assets/' + uploaded['assetId'], headers=seller).status_code, 200)
        # Removing a reference is not permission to destroy the original object.
        self.assertTrue((Path(self.app.config['UPLOAD_FOLDER']) / uploaded['filename']).exists())

    def test_listing_asset_ownership_url_type_and_url_only_bypass_rejected(self):
        seller, _ = self.register('association_owner')
        outsider, _ = self.register('association_other')
        self.enable_asset_ledger()
        with patch('app.routes.system.init_cloudinary', return_value=False):
            uploaded = self.client.post('/api/uploads/images', headers=seller,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')}).get_json()
        base = {'make': 'Toyota', 'model': 'Camry'}
        item = {'type': 'image', 'url': uploaded['url'], 'assetId': uploaded['assetId']}
        for fields in ({'image': uploaded['url']}, {'galleryImages': [uploaded['url']]},
                       {'mediaGallery': [item]}, {'mediaGallery': [{'type': 'image', 'url': uploaded['url']}]},
                       {'image': 'https://example.test/unregistered.png'}):
            self.assertEqual(self.client.post('/api/cars', headers=outsider, json={**base, **fields}).status_code, 400)
        for modified in ({**item, 'url': 'https://example.test/spoof.png'}, {**item, 'type': 'video'},
                         {**item, 'assetId': '0' * 32}):
            self.assertEqual(self.client.post('/api/cars', headers=seller,
                json={**base, 'mediaGallery': [modified]}).status_code, 400)
        # Old clients can submit the owner's exact known URL; the server adds its ID.
        created = self.client.post('/api/cars', headers=seller, json={**base, 'image': uploaded['url']})
        self.assertEqual(created.status_code, 201)
        endpoint = f"/api/cars/{created.get_json()['id']}"
        self.assertEqual(self.client.get(endpoint).get_json()['car']['mediaGallery'], [item])
        before = self.client.get(endpoint).get_json()['car']
        self.assertEqual(self.client.patch(endpoint, headers=seller,
            json={'price': 1, 'mediaGallery': [{**item, 'assetId': '0' * 32}]}).status_code, 400)
        self.assertEqual(self.client.get(endpoint).get_json()['car'], before)

    def test_existing_url_only_listing_survives_ledger_rollout_without_transferring_ownership(self):
        seller, _ = self.register('legacy_association')
        url = 'https://example.test/legacy.png'
        created = self.client.post('/api/cars', headers=seller, json={
            'make': 'Toyota', 'model': 'Camry', 'image': url, 'galleryImages': [url]})
        endpoint = f"/api/cars/{created.get_json()['id']}"
        self.enable_asset_ledger()
        self.assertEqual(self.client.patch(endpoint, headers=seller,
            json={'price': 12000, 'image': url, 'galleryImages': [url], 'mediaGallery': [{'type': 'image', 'url': url}]}).status_code, 200)
        self.assertEqual(self.client.post('/api/cars', headers=seller,
            json={'make': 'Toyota', 'model': 'Camry', 'image': url}).status_code, 400)
        self.assertEqual(self.client.patch(endpoint, headers=seller,
            json={'galleryImages': [url, 'https://example.test/new.png']}).status_code, 400)
        self.assertEqual(self.client.patch(endpoint, headers=seller, json={'price': 13000}).status_code, 200)

    def enable_upload_quotas(self, count=100, size=1024 * 1024 * 1024):
        self.enable_asset_ledger()
        from app.db import get_db
        with self.app.app_context():
            get_db().executescript((Path(__file__).parent / 'migrations' / '002_upload_reservations.sql').read_text(encoding='utf-8'))
        self.app.config.update(UPLOAD_QUOTAS_ENABLED=True, UPLOAD_USER_MAX_ASSETS=count, UPLOAD_USER_MAX_BYTES=size)

    def test_upload_count_quota_is_per_owner_and_precedes_storage(self):
        owner, _ = self.register('quota_owner')
        other, _ = self.register('quota_other')
        self.enable_upload_quotas(count=1)
        def upload(headers):
            return self.client.post('/api/uploads/images', headers=headers,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
        with patch('app.routes.system.init_cloudinary', return_value=False):
            self.assertEqual(upload(owner).status_code, 200)
            self.assertEqual(upload(other).status_code, 200)
        with patch('app.routes.system.init_cloudinary') as storage:
            rejected = upload(owner)
            self.assertEqual(rejected.status_code, 409)
            self.assertEqual(rejected.get_json()['code'], 'upload_quota_exceeded')
            self.assertEqual(rejected.headers['Cache-Control'], 'no-store')
            storage.assert_not_called()
        from app.db import get_db
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM upload_reservations').fetchone()['n'], 0)
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM media_assets').fetchone()['n'], 2)

    def test_byte_quota_includes_ledger_usage_created_before_quota_enablement(self):
        owner, _ = self.register('quota_bytes')
        self.enable_asset_ledger()
        image = self.ledger_image()
        with patch('app.routes.system.init_cloudinary', return_value=False):
            self.assertEqual(self.client.post('/api/uploads/images', headers=owner,
                data={'file': (io.BytesIO(image), 'fixture.png')}).status_code, 200)
        self.enable_upload_quotas(size=len(image) * 2 - 1)
        with patch('app.routes.system.init_cloudinary') as storage:
            response = self.client.post('/api/uploads/images', headers=owner,
                data={'file': (io.BytesIO(image), 'fixture.png')})
            self.assertEqual(response.status_code, 409)
            storage.assert_not_called()

    def test_concurrent_uploads_cannot_overbook_one_owner(self):
        from concurrent.futures import ThreadPoolExecutor
        owner, _ = self.register('quota_parallel')
        self.enable_upload_quotas(count=3)
        image = self.ledger_image()
        def upload(_):
            with self.app.test_client() as client:
                return client.post('/api/uploads/images', headers=owner,
                    data={'file': (io.BytesIO(image), 'fixture.png')}).status_code
        with patch('app.routes.system.init_cloudinary', return_value=False):
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(upload, range(8)))
        self.assertEqual(results.count(200), 3, results)
        self.assertEqual(results.count(409), 5, results)
        from app.db import get_db
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM media_assets').fetchone()['n'], 3)
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM upload_reservations').fetchone()['n'], 0)

    def test_ambiguous_cloud_failure_keeps_reservation_and_prevents_retry_bypass(self):
        owner, _ = self.register('quota_failure')
        self.enable_upload_quotas(count=1)
        self.app.config['LOCAL_UPLOADS_ALLOWED'] = True
        with patch('app.routes.system.init_cloudinary', return_value=True), \
                patch('app.routes.system.cloudinary.uploader.upload', side_effect=RuntimeError('fixture timeout')) as cloud:
            first = self.client.post('/api/uploads/images', headers=owner,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
            second = self.client.post('/api/uploads/images', headers=owner,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
        self.assertEqual(first.status_code, 503)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(cloud.call_count, 1)
        self.assertFalse(any(Path(self.app.config['UPLOAD_FOLDER']).iterdir()))
        from app.db import get_db
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM upload_reservations').fetchone()['n'], 1)

    def test_image_and_video_uploads_share_the_account_budget(self):
        owner, _ = self.register('quota_shared_media')
        self.enable_upload_quotas(count=1)
        video = b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42'
        with patch('app.routes.system.init_cloudinary', return_value=False):
            self.assertEqual(self.client.post('/api/uploads/videos', headers=owner,
                data={'file': (io.BytesIO(video), 'fixture.mp4')}).status_code, 200)
        with patch('app.routes.system.init_cloudinary') as storage:
            self.assertEqual(self.client.post('/api/uploads/images', headers=owner,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')}).status_code, 409)
            storage.assert_not_called()

    def test_ledger_completion_without_matching_reservation_rolls_back(self):
        _, owner_id = self.register('quota_completion')
        self.enable_upload_quotas()
        from app.media_assets import finish_upload
        from app.db import get_db
        with self.app.test_request_context('/api/uploads/images'):
            response = finish_upload({'success': True, 'url': '/api/uploads/images/fixture.png'},
                owner_id=owner_id, provider='local', namespace='local', kind='image',
                provider_id='fixture.png', source_bytes=100)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM media_assets').fetchone()['n'], 0)

    def test_missing_quota_migration_fails_closed_and_invalid_files_do_not_reserve(self):
        owner, _ = self.register('quota_schema')
        self.enable_asset_ledger()
        self.app.config['UPLOAD_QUOTAS_ENABLED'] = True
        with patch('app.routes.system.init_cloudinary') as storage:
            response = self.client.post('/api/uploads/images', headers=owner,
                data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')})
            self.assertEqual(response.status_code, 503)
            storage.assert_not_called()
        self.enable_upload_quotas()
        self.assertEqual(self.client.post('/api/uploads/images', headers=owner,
            data={'file': (io.BytesIO(b'bad'), 'fixture.png')}).status_code, 400)
        self.assertEqual(self.client.post('/api/uploads/images',
            data={'file': (io.BytesIO(self.ledger_image()), 'fixture.png')}).status_code, 401)
        from app.db import get_db
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM upload_reservations').fetchone()['n'], 0)

    def enable_signed_uploads(self):
        self.enable_upload_quotas()
        from app.db import get_db
        with self.app.app_context():
            get_db().executescript((Path(__file__).parent / 'migrations' / '003_signed_upload_intents.sql').read_text(encoding='utf-8'))
        self.app.config.update(SIGNED_UPLOADS_ENABLED=True, SIGNED_UPLOAD_PRESETS_VERIFIED=True,
            SIGNED_UPLOAD_IMAGE_PRESET='fixture_images', SIGNED_UPLOAD_VIDEO_PRESET='fixture_videos')
        self.enterContext(patch('app.signed_uploads.provider_options', return_value={
            'cloud_name': 'fixture', 'api_key': 'fixture-public-key', 'api_secret': 'fixture-signing-only', 'timeout': 10}))

    def signed_fixture_metadata(self, intent_id):
        from app.db import get_db
        with self.app.app_context():
            intent = get_db().execute('SELECT * FROM signed_upload_intents WHERE id = ?', (intent_id,)).fetchone()
        return {'public_id': intent['public_id'], 'resource_type': intent['resource_type'], 'type': 'upload',
                'asset_id': 'fixture-immutable-id', 'version': 123, 'bytes': 100, 'width': 10, 'height': 10,
                'format': 'png' if intent['resource_type'] == 'image' else 'mp4', 'duration': 30,
                'secure_url': f"https://res.cloudinary.com/fixture/{intent['resource_type']}/upload/v123/{intent['public_id']}.png"}

    def test_signed_prepare_proxy_gate_and_authentication(self):
        owner, _ = self.register('signed_gate')
        self.assertEqual(self.client.post('/api/uploads/prepare', json={}).status_code, 401)
        self.assertEqual(self.client.post('/api/uploads/prepare', headers=owner, json={}).get_json(), {'mode': 'proxy'})
        self.app.config['SIGNED_UPLOADS_ENABLED'] = True
        self.assertEqual(self.client.post('/api/uploads/prepare', headers=owner, json={}).status_code, 503)

    def test_signed_prepare_is_idempotent_and_uses_only_server_parameters(self):
        owner, _ = self.register('signed_prepare')
        self.enable_signed_uploads()
        payload = {'kind': 'image', 'requestKey': 'a' * 32, 'public_id': 'attacker', 'overwrite': True, 'size': 1}
        first = self.client.post('/api/uploads/prepare', headers=owner, json=payload)
        self.assertEqual(first.status_code, 200)
        second = self.client.post('/api/uploads/prepare', headers=owner, json=payload)
        self.assertEqual(first.get_json(), second.get_json())
        data = first.get_json()
        self.assertEqual(data['parameters']['overwrite'], 'false')
        self.assertTrue(data['parameters']['public_id'].startswith('intelliwheels/development/image/'))
        self.assertNotIn('api_secret', data['parameters'])
        from app.db import get_db
        with self.app.app_context():
            rows = get_db().execute('SELECT * FROM upload_reservations').fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['source_bytes'], 15 * 1024 * 1024)
        self.assertEqual(self.client.post('/api/uploads/prepare', headers=owner,
            json={**payload, 'kind': 'video'}).status_code, 409)

    def test_signed_completion_is_verified_idempotent_and_attaches_to_listing(self):
        owner, _ = self.register('signed_flow')
        other, _ = self.register('signed_other')
        self.enable_signed_uploads()
        prepared = self.client.post('/api/uploads/prepare', headers=owner,
            json={'kind': 'image', 'requestKey': 'b' * 32}).get_json()
        intent_id = prepared['intentId']
        endpoint = f'/api/uploads/complete/{intent_id}'
        metadata = self.signed_fixture_metadata(intent_id)
        with patch('app.signed_uploads.cloudinary.api.resource', return_value=metadata) as provider:
            self.assertEqual(self.client.post(endpoint, headers=other).status_code, 404)
            provider.assert_not_called()
            first = self.client.post(endpoint, headers=owner, json={'secure_url': 'https://evil.test/forged'})
            self.assertEqual(first.status_code, 200)
            second = self.client.post(endpoint, headers=owner)
            self.assertEqual(first.get_json(), second.get_json())
            self.assertEqual(provider.call_count, 1)
        result = first.get_json()
        self.assertEqual(result['url'], metadata['secure_url'])
        created = self.client.post('/api/cars', headers=owner, json={'make': 'Toyota', 'model': 'Camry',
            'mediaGallery': [{'type': 'image', 'url': result['url'], 'assetId': result['assetId']}]})
        self.assertEqual(created.status_code, 201)
        from app.db import get_db
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM upload_reservations').fetchone()['n'], 1)
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM media_assets').fetchone()['n'], 1)

    def test_signed_completion_keeps_full_hold_and_blocks_allowance_recycling(self):
        owner, _ = self.register('signed_hold')
        self.enable_signed_uploads()
        maximum = self.app.config['IMAGE_UPLOAD_MAX_BYTES']
        self.app.config['UPLOAD_USER_MAX_BYTES'] = maximum + 1000
        payload = {'kind': 'image', 'requestKey': 'e' * 32}
        intent_id = self.client.post('/api/uploads/prepare', headers=owner, json=payload).get_json()['intentId']
        with patch('app.signed_uploads.cloudinary.api.resource', return_value=self.signed_fixture_metadata(intent_id)):
            self.assertEqual(self.client.post(f'/api/uploads/complete/{intent_id}', headers=owner).status_code, 200)
        from app.db import get_db
        with self.app.app_context():
            db = get_db()
            row = db.execute('SELECT source_bytes FROM upload_reservations WHERE id=?', (intent_id,)).fetchone()
            self.assertEqual(row['source_bytes'], maximum)
            db.execute('UPDATE signed_upload_intents SET issued_at=1')
            db.commit()
        self.assertEqual(self.client.post('/api/uploads/prepare', headers=owner,
            json={**payload, 'requestKey': 'f' * 32}).status_code, 409)
        recovery = self.client.get('/api/uploads/recovery', headers=owner).get_json()['uploads'][0]
        self.assertEqual(recovery['state'], 'completed')
        self.assertTrue(recovery['signatureExpired'])
        self.assertTrue(recovery['quotaHeld'])

    def test_signed_recovery_is_private_paginated_and_does_not_contact_provider(self):
        owner, _ = self.register('recovery_owner')
        other, _ = self.register('recovery_other')
        self.assertEqual(self.client.get('/api/uploads/recovery').status_code, 401)
        self.assertEqual(self.client.get('/api/uploads/recovery', headers=owner).status_code, 404)
        self.enable_signed_uploads()
        ids = set()
        for index in range(21):
            response = self.client.post('/api/uploads/prepare', headers=owner,
                json={'kind': 'image', 'requestKey': f'{index:032x}'})
            self.assertEqual(response.status_code, 200)
            ids.add(response.get_json()['intentId'])
        with patch('app.signed_uploads.cloudinary.api.resource') as provider:
            self.assertEqual(self.client.get('/api/uploads/recovery', headers=other).get_json()['uploads'], [])
            self.assertEqual(self.client.get('/api/uploads/recovery?after=invalid', headers=owner).status_code, 400)
            first = self.client.get('/api/uploads/recovery', headers=owner)
            self.assertEqual(first.headers['Cache-Control'], 'no-store')
            data = first.get_json()
            self.assertEqual(len(data['uploads']), 20)
            last = self.client.get('/api/uploads/recovery?after=' + data['nextCursor'], headers=owner).get_json()
            self.assertEqual(len(last['uploads']), 1)
            self.assertIsNone(last['nextCursor'])
            self.assertEqual({row['intentId'] for row in data['uploads'] + last['uploads']}, ids)
            self.assertEqual(set(data['uploads'][0]), {'intentId', 'kind', 'state', 'signatureExpired', 'quotaHeld', 'assetId'})
            provider.assert_not_called()

    def test_signed_completion_without_full_hold_cannot_write_ledger(self):
        owner, _ = self.register('signed_missing_hold')
        self.enable_signed_uploads()
        intent_id = self.client.post('/api/uploads/prepare', headers=owner,
            json={'kind': 'image', 'requestKey': '9' * 32}).get_json()['intentId']
        from app.db import get_db
        with self.app.app_context():
            db = get_db()
            db.execute('DELETE FROM upload_reservations')
            db.commit()
        with patch('app.signed_uploads.cloudinary.api.resource', return_value=self.signed_fixture_metadata(intent_id)):
            self.assertEqual(self.client.post(f'/api/uploads/complete/{intent_id}', headers=owner).status_code, 503)
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM media_assets').fetchone()['n'], 0)

    def test_signed_metadata_failures_retain_reservation(self):
        owner, _ = self.register('signed_bad')
        self.enable_signed_uploads()
        intent_id = self.client.post('/api/uploads/prepare', headers=owner,
            json={'kind': 'video', 'requestKey': 'c' * 32}).get_json()['intentId']
        original = self.signed_fixture_metadata(intent_id)
        for change in ({'bytes': 101 * 1024 * 1024}, {'duration': 121}, {'duration': float('nan')},
                       {'width': 0}, {'height': 10001}, {'public_id': 'other'}, {'resource_type': 'image'},
                       {'secure_url': 'https://evil.test/video.mp4'}, {'asset_id': ''}):
            with patch('app.signed_uploads.cloudinary.api.resource', return_value={**original, **change}):
                self.assertEqual(self.client.post(f'/api/uploads/complete/{intent_id}', headers=owner).status_code, 503)
        from app.db import get_db
        with self.app.app_context():
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM upload_reservations').fetchone()['n'], 1)
            self.assertEqual(get_db().execute('SELECT COUNT(*) AS n FROM media_assets').fetchone()['n'], 0)

    def test_signed_expiry_does_not_refund_or_generate_a_fresh_signature(self):
        owner, _ = self.register('signed_expiry')
        self.enable_signed_uploads()
        payload = {'kind': 'image', 'requestKey': 'd' * 32}
        self.client.post('/api/uploads/prepare', headers=owner, json=payload)
        from app.db import get_db
        with self.app.app_context():
            db = get_db()
            db.execute('UPDATE signed_upload_intents SET issued_at = 1')
            db.commit()
        self.assertEqual(self.client.post('/api/uploads/prepare', headers=owner, json=payload).status_code, 410)

    def test_asset_migration_readonly_backup_and_reapplication(self):
        import sqlite3
        from migrate_media_assets import migrate
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        database = root / 'fixture.db'
        backup = root / 'backup.db'
        with contextlib.closing(sqlite3.connect(database)) as db:
            db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY)')
            db.execute('INSERT INTO users VALUES (1)')
            db.commit()
        self.assertEqual(migrate(database), 'Media ledger migration pending')
        self.assertFalse(backup.exists())
        migrate(database, backup)
        with contextlib.closing(sqlite3.connect(backup)) as db:
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='media_assets'").fetchone())
            self.assertEqual(db.execute('SELECT COUNT(*) FROM users').fetchone()[0], 1)
        with self.assertRaises(FileExistsError):
            migrate(database, backup)
        migrate(database, root / 'second-backup.db')
        self.assertEqual(migrate(database), 'Media ledger table present')
        with self.assertRaises(FileNotFoundError):
            migrate(root / 'missing.db', root / 'unused.db')
        self.assertFalse((root / 'missing.db').exists())
        self.assertEqual(migrate(database, migration='quotas'), 'Upload quota migration pending')
        migrate(database, root / 'quota-backup.db', 'quotas')
        self.assertEqual(migrate(database, migration='quotas'), 'Upload quota table present')
        migrate(database, root / 'signed-backup.db', 'signed')
        self.assertEqual(migrate(database, migration='signed'), 'Signed upload table present')

    def test_listing_media_limits_count_aliases_once_and_preserve_urls(self):
        seller, _ = self.register('media_listing')
        images = [f'https://example.test/{index}.png?a=1&b=2' for index in range(12)]
        videos = ['/one.mp4', '/two.mp4']
        payload = {'make': 'Toyota', 'model': 'Camry', 'image': images[0], 'galleryImages': images,
                   'videoUrl': videos[0], 'mediaGallery': [{'type': 'image', 'url': url} for url in images] +
                   [{'type': 'video', 'url': url} for url in videos]}
        created = self.client.post('/api/cars', headers=seller, json=payload)
        self.assertEqual(created.status_code, 201)
        car = self.client.get(f"/api/cars/{created.get_json()['id']}").get_json()['car']
        self.assertEqual(car['image'], images[0])
        self.assertEqual(car['galleryImages'], images)
        self.assertEqual(car['mediaGallery'], payload['mediaGallery'])

    def test_invalid_listing_media_rejected_without_creating_records(self):
        seller, _ = self.register('bad_media_listing')
        invalid = [
            {'galleryImages': ['/image.png'] * 13},
            {'mediaGallery': [{'type': 'video', 'url': f'/{i}.mp4'} for i in range(3)]},
            {'galleryImages': 'not an array'}, {'galleryImages': [None]},
            {'mediaGallery': [{'type': 'audio', 'url': '/sound.mp3'}]},
            {'mediaGallery': [{'type': 'image', 'url': '/image.png', 'unexpected': True}]},
            {'mediaGallery': [{'type': 'image', 'url': '/image.png', 'thumbnail': 'javascript:alert(1)'}]},
            {'image': '/same', 'videoUrl': '/same'}, {'image': {'url': '/image.png'}},
        ]
        invalid += [{'image': url} for url in ('javascript:alert(1)', 'data:image/png;base64,AA',
                    '//example.test/image', 'https://user:pass@example.test/image', '/bad\\image',
                    '/bad\nimage', 'https://', 'https://[invalid', 'https://example.test:bad/x', '/' + 'a' * 500)]
        for fields in invalid:
            with self.subTest(fields=fields):
                response = self.client.post('/api/cars', headers=seller, json={'make': 'Toyota', 'model': 'Camry', **fields})
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get('/api/cars').get_json()['total'], 0)
        self.assertEqual(self.client.post('/api/cars', headers=seller, json=['invalid']).status_code, 400)

    def test_partial_media_updates_cannot_bypass_combined_limits(self):
        seller, _ = self.register('partial_media')
        images = [f'/{index}.png' for index in range(12)]
        response = self.client.post('/api/cars', headers=seller, json={
            'make': 'Toyota', 'model': 'Camry', 'galleryImages': images,
            'mediaGallery': [{'type': 'video', 'url': '/one.mp4'}, {'type': 'video', 'url': '/two.mp4'}]})
        endpoint = f"/api/cars/{response.get_json()['id']}"
        for method in ('patch', 'put'):
            for changes in ({'image': '/extra.png'}, {'videoUrl': '/three.mp4'}, {'mediaGallery': [] , 'galleryImages': images + ['/extra.png']}):
                rejected = getattr(self.client, method)(endpoint, headers=seller, json={**changes, 'price': 1})
                self.assertEqual(rejected.status_code, 400)
        car = self.client.get(endpoint).get_json()['car']
        self.assertIsNone(car['price'])
        self.assertEqual(car['galleryImages'], images)
        self.assertEqual(self.client.patch(endpoint, headers=seller, json={'image': images[0]}).status_code, 200)
        self.assertEqual(self.client.patch(endpoint, headers=seller, json=['invalid']).status_code, 400)

    def test_media_clear_and_optional_metadata_roundtrip(self):
        seller, _ = self.register('clear_media')
        media = [{'type': 'video', 'url': '/one.mp4', 'label': 'Walkaround', 'thumbnail': '/thumb.png'}]
        response = self.client.post('/api/cars', headers=seller, json={
            'make': 'Toyota', 'model': 'Camry', 'image': '/image.png', 'videoUrl': '/one.mp4',
            'galleryImages': ['/image.png'], 'mediaGallery': media})
        endpoint = f"/api/cars/{response.get_json()['id']}"
        self.assertEqual(self.client.get(endpoint).get_json()['car']['mediaGallery'], media)
        response = self.client.patch(endpoint, headers=seller,
            json={'image': '', 'videoUrl': '', 'galleryImages': [], 'mediaGallery': []})
        self.assertEqual(response.status_code, 200)
        car = self.client.get(endpoint).get_json()['car']
        self.assertFalse(car['image_url'])
        self.assertFalse(car['video_url'])
        self.assertEqual(car['gallery_images'], [])
        self.assertEqual(car['media_gallery'], [])

    def test_legacy_media_does_not_block_unrelated_edits_and_can_be_replaced(self):
        seller, _ = self.register('legacy_media')
        response = self.client.post('/api/cars', headers=seller, json={'make': 'Toyota', 'model': 'Camry'})
        car_id = response.get_json()['id']
        from app.db import get_db
        with self.app.app_context():
            db = get_db()
            db.execute('UPDATE cars SET media_gallery = ? WHERE id = ?', ('bad historical json', car_id))
            db.commit()
        endpoint = f'/api/cars/{car_id}'
        self.assertEqual(self.client.patch(endpoint, headers=seller, json={'price': 2500}).status_code, 200)
        self.assertEqual(self.client.patch(endpoint, headers=seller, json={'image': '/new.png'}).status_code, 400)
        self.assertEqual(self.client.patch(endpoint, headers=seller, json={'image': '/new.png', 'mediaGallery': []}).status_code, 200)

    def test_media_updates_remain_owner_only(self):
        seller, _ = self.register('media_owner')
        outsider, _ = self.register('media_outsider')
        response = self.client.post('/api/cars', headers=seller, json={'make': 'Toyota', 'model': 'Camry'})
        endpoint = f"/api/cars/{response.get_json()['id']}"
        self.assertEqual(self.client.patch(endpoint, headers=outsider, json={'image': '/other.png'}).status_code, 403)
        self.assertEqual(self.client.patch(endpoint, json={'image': '/other.png'}).status_code, 401)

    def test_seller_buyer_listing_favorite_message_and_logout(self):
        seller, seller_id = self.register('journey_seller')
        buyer, _ = self.register('journey_buyer')
        outsider, _ = self.register('journey_outsider')
        created = self.client.post('/api/cars', headers=seller, json={
            'make': 'Toyota', 'model': 'Camry', 'year': 2021,
            'price': 15000, 'currency': 'JOD', 'description': 'Disposable test listing',
            'owner_id': -1,
        })
        self.assertEqual(created.status_code, 201)
        car_id = created.get_json()['id']
        self.assertEqual(self.client.get(f'/api/cars/{car_id}').status_code, 200)
        from app.db import get_db
        with self.app.app_context():
            owner = get_db().execute('SELECT owner_id FROM cars WHERE id = ?', (car_id,)).fetchone()
            self.assertEqual(owner['owner_id'], seller_id)
        search = self.client.get('/api/cars?make=Toyota').get_json()
        self.assertEqual(search['total'], 1)
        self.assertEqual(self.client.patch(f'/api/cars/{car_id}', headers=buyer, json={'price': 1}).status_code, 403)
        self.assertEqual(self.client.patch(f'/api/cars/{car_id}', headers=seller, json={'price': 14500}).status_code, 200)
        self.assertEqual(self.client.post('/api/favorites', headers=buyer, json={'car_id': car_id}).status_code, 200)
        favorites = self.client.get('/api/favorites', headers=buyer).get_json()
        self.assertEqual([car['id'] for car in favorites['cars']], [car_id])
        sent = self.client.post('/api/messages/send', headers=buyer, json={
            'recipient_id': seller_id, 'listing_id': car_id, 'content': 'Is this test vehicle available?',
        })
        self.assertIn(sent.status_code, (200, 201))
        conversations = self.client.get('/api/messages/conversations', headers=seller).get_json()
        self.assertEqual(len(conversations['conversations']), 1)
        conversation_id = conversations['conversations'][0]['id']
        thread = self.client.get(f'/api/messages/conversations/{conversation_id}', headers=seller)
        self.assertEqual(thread.status_code, 200)
        self.assertEqual(len(thread.get_json()['messages']), 1)
        self.assertIn(self.client.get(f'/api/messages/conversations/{conversation_id}', headers=outsider).status_code, (403, 404))
        self.assertEqual(self.client.delete(f'/api/favorites/{car_id}', headers=buyer).status_code, 200)
        self.assertEqual(self.client.delete(f'/api/cars/{car_id}', headers=buyer).status_code, 403)
        self.assertEqual(self.client.delete(f'/api/cars/{car_id}', headers=seller).status_code, 200)
        self.assertEqual(self.client.get(f'/api/cars/{car_id}').status_code, 404)
        self.assertEqual(self.client.post('/api/auth/logout', headers=buyer).status_code, 200)
        self.assertEqual(self.client.get('/api/favorites', headers=buyer).status_code, 401)


if __name__ == '__main__':
    unittest.main()
