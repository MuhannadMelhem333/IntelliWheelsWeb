"""Validate the configured destination of sensitive account emails."""
from urllib.parse import urlsplit, urlencode


def resolve_reset_origin(explicit, allowed_origins, development=False):
    # Compatibility default is one configured origin, never request Host/Origin.
    value = explicit if explicit is not None else next((v for v in allowed_origins if v), '')
    if not isinstance(value, str):
        raise ValueError('PASSWORD_RESET_ORIGIN must be one valid frontend origin')
    value = value.strip()
    try:
        parsed = urlsplit(value)
        port = parsed.port
        valid = (
            bool(parsed.hostname) and parsed.scheme in ('http', 'https')
            and parsed.username is None and parsed.password is None
            and parsed.path in ('', '/') and not parsed.query and not parsed.fragment
            and not any(c.isspace() or c in ',\\<>\"\'%' for c in value)
            and '*' not in value and (port is None or 0 < port <= 65535)
        )
        if parsed.scheme == 'http':
            valid = valid and development and parsed.hostname in ('localhost', '127.0.0.1', '::1')
        if not valid:
            raise ValueError()
    except ValueError:
        # Never echo configured values: malformed URLs can contain credentials.
        raise ValueError('PASSWORD_RESET_ORIGIN must be one valid HTTPS frontend origin (HTTP loopback is development-only)') from None
    return value.rstrip('/')


def password_reset_url(origin, token):
    return f'{origin}/account?{urlencode({"reset_token": token})}'
