import unittest
from check_release_config import check, public_https


class ReleaseConfigTest(unittest.TestCase):
    def fixture(self):
        return dict(FLASK_ENV='staging', SECRET_KEY='fixture-only-long-secret-not-for-deployment',
                    DATABASE_URL='postgresql://fixture:private@db.example.com/market',
                    FRONTEND_ORIGIN='https://www.example.com', BACKEND_URL='https://api.example.com',
                    CLOUDINARY_CLOUD_NAME='fixture', CLOUDINARY_API_KEY='private-key', CLOUDINARY_API_SECRET='private-secret',
                    SMTP_HOST='mail.example.com', SMTP_USER='fixture', SMTP_PASS='private-password',
                    RATE_LIMIT_REDIS_URL='rediss://fixture:private@redis.example.com:6379', RATE_LIMIT_NAMESPACE='staging',
                    NEXT_PUBLIC_API_URL='https://api.example.com/api')

    def test_configured_is_not_launch_approval_and_values_are_never_reported(self):
        report = check(self.fixture())
        self.assertTrue(report['configuration_passed'])
        self.assertFalse(report['launch_approved']); self.assertFalse(report['services_contacted'])
        for private in ('private-key', 'private-secret', 'private-password', 'db.example.com'):
            self.assertNotIn(private, str(report))

    def test_missing_services_and_local_urls_block_hosted_configuration(self):
        report = check({})
        self.assertFalse(report['configuration_passed'])
        for code in ('frontend.public_api_missing', 'backend.durable_image_storage_missing', 'backend.password_reset_email_missing', 'backend.shared_limiter_missing'):
            self.assertIn(code, report['blockers'])
        for value in ('http://api.example.com', 'https://localhost', 'https://127.0.0.1', 'https://10.0.0.1', 'https://user:pass@api.example.com', 'https://api.example.com?secret=x'):
            self.assertFalse(public_https(value))

    def test_resend_configuration_needs_key_and_sender_not_smtp(self):
        env = self.fixture()
        for key in ('SMTP_HOST', 'SMTP_USER', 'SMTP_PASS'):
            env.pop(key)
        env.update(AUTH_EMAIL_PROVIDER='resend', RESEND_API_KEY='private-resend-key',
                   AUTH_EMAIL_FROM='IntelliWheels <reset@example.test>', SMTP_PORT='unused')
        self.assertTrue(check(env)['configuration_passed'])
        self.assertNotIn('private-resend-key', str(check(env)))
        for key in ('RESEND_API_KEY', 'AUTH_EMAIL_FROM'):
            missing = {**env, key: ''}
            self.assertIn('backend.password_reset_email_missing', check(missing)['blockers'])
        env['AUTH_EMAIL_PROVIDER'] = 'unknown'
        self.assertIn('backend.email_provider_invalid', check(env)['blockers'])

    def test_alias_conflicts_and_component_separation(self):
        env = self.fixture(); env['NEXT_PUBLIC_API_BASE_URL'] = 'https://different.example.com'
        self.assertIn('frontend.conflicting_public_api_settings', check(env, 'frontend')['blockers'])
        env['NEXT_PUBLIC_API_BASE_URL'] = 'https://api.example.com/'
        self.assertTrue(check(env, 'frontend')['configuration_passed'])
        self.assertTrue(check({'NEXT_PUBLIC_API_URL': 'https://api.example.com'}, 'frontend')['configuration_passed'])

    def test_invalid_secret_origins_database_and_smtp_port_fail_safely(self):
        for key, value, code in [('SECRET_KEY', 'x' * 64, 'backend.secret_missing_or_obviously_weak'),
                                 ('FRONTEND_ORIGIN', '*', 'backend.frontend_origins_invalid'),
                                 ('DATABASE_URL', 'sqlite:///local.db', 'backend.postgres_configuration_missing'),
                                 ('SMTP_PORT', 'invalid', 'backend.smtp_port_invalid')]:
            env = self.fixture(); env[key] = value
            self.assertIn(code, check(env)['blockers'])


if __name__ == '__main__':
    unittest.main()
