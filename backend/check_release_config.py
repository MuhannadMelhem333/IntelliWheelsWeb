"""Read-only configuration preflight, not deployment or service acceptance.

Reads only process environment. Does not load .env, connect to services, import
Flask, or print configuration values. Exit 1 means required configuration fails.
"""
import argparse
import ipaddress
import json
import os
from urllib.parse import urlsplit

PUBLIC_API_KEYS = ('NEXT_PUBLIC_API_BASE_URL', 'NEXT_PUBLIC_API_URL',
                   'NEXT_PUBLIC_API_BASE', 'NEXT_PUBLIC_BACKEND_URL')


def public_https(value, origin=False):
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if (parsed.scheme != 'https' or not host or parsed.username or parsed.password or
                parsed.query or parsed.fragment or any(char.isspace() for char in value) or
                host == 'localhost' or host.endswith(('.localhost', '.local')) or
                (origin and parsed.path not in ('', '/'))):
            return False
        _ = parsed.port  # Reject malformed port syntax without reporting the value.
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return '.' in host
    except (ValueError, TypeError):
        return False


def check(env, component='all'):
    failures = []
    def require(condition, code):
        if not condition:
            failures.append(code)
    if component in ('frontend', 'all'):
        values = [env.get(key, '') for key in PUBLIC_API_KEYS if env.get(key)]
        require(bool(values), 'frontend.public_api_missing')
        if values:
            require(all(public_https(value) for value in values), 'frontend.public_api_not_public_https')
            normalized = {value.rstrip('/') if value.rstrip('/').endswith('/api') else value.rstrip('/') + '/api' for value in values}
            require(len(normalized) == 1, 'frontend.conflicting_public_api_settings')
    if component in ('backend', 'all'):
        require(env.get('FLASK_ENV') in ('production', 'staging'), 'backend.environment_not_hosted')
        secret = env.get('SECRET_KEY', '')
        require(len(secret) >= 32 and secret not in ('dev-only-insecure-key-for-local-testing',) and len(set(secret)) >= 8,
                'backend.secret_missing_or_obviously_weak')
        try:
            database = urlsplit(env.get('DATABASE_URL', ''))
            require(database.scheme in ('postgres', 'postgresql') and bool(database.hostname) and bool(database.path.strip('/')),
                    'backend.postgres_configuration_missing')
        except ValueError:
            failures.append('backend.postgres_configuration_missing')
        origins = [part.strip() for part in env.get('FRONTEND_ORIGIN', '').split(',') if part.strip()]
        require(bool(origins) and all(public_https(origin, origin=True) for origin in origins), 'backend.frontend_origins_invalid')
        require(public_https(env.get('BACKEND_URL', ''), origin=True), 'backend.public_origin_invalid')
        reset = env.get('PASSWORD_RESET_ORIGIN') or (origins[0] if origins else '')
        require(public_https(reset, origin=True), 'backend.reset_origin_invalid')
        require(all(env.get(key) for key in ('CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET')),
                'backend.durable_image_storage_missing')
        email_provider = env.get('AUTH_EMAIL_PROVIDER', 'smtp')
        require(email_provider in ('smtp', 'resend'), 'backend.email_provider_invalid')
        if email_provider == 'resend':
            require(all(env.get(key) for key in ('RESEND_API_KEY', 'AUTH_EMAIL_FROM')),
                    'backend.password_reset_email_missing')
        elif email_provider == 'smtp':
            require(all(env.get(key) for key in ('SMTP_HOST', 'SMTP_USER', 'SMTP_PASS')), 'backend.password_reset_email_missing')
            try:
                require(1 <= int(env.get('SMTP_PORT', '587')) <= 65535, 'backend.smtp_port_invalid')
            except ValueError:
                failures.append('backend.smtp_port_invalid')
        try:
            limiter = urlsplit(env.get('RATE_LIMIT_REDIS_URL', ''))
            require(limiter.scheme in ('redis', 'rediss') and bool(limiter.hostname) and bool(env.get('RATE_LIMIT_NAMESPACE')),
                    'backend.shared_limiter_missing')
        except ValueError:
            failures.append('backend.shared_limiter_missing')
    return {'configuration_passed': not failures, 'component': component, 'blockers': failures,
            'services_contacted': False, 'launch_approved': False,
            'manual_gates': ['database_migration_and_restore', 'durable_upload_and_reload',
                             'login_logout_reset_delivery', 'browser_mobile_rtl',
                             'hosted_rate_limits_and_proxy', 'release_security_and_session_review',
                             'runtime_video_tools_if_videos_enabled', 'approved_deployment_and_rollback']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', choices=['frontend', 'backend', 'all'], default='all')
    args = parser.parse_args()
    report = check(os.environ, args.component)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['configuration_passed'] else 1)
