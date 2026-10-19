"""Opt-in forwarded IP/scheme handling for a verified immediate proxy peer."""
from ipaddress import ip_address, ip_network
from werkzeug.middleware.proxy_fix import ProxyFix


def configure_trusted_proxy(app):
    try:
        counts = []
        for name in ('TRUSTED_PROXY_X_FOR', 'TRUSTED_PROXY_X_PROTO'):
            value = str(app.config.get(name, '0'))
            if value not in ('0', '1', '2', '3', '4', '5'):
                raise ValueError()
            counts.append(int(value))
        networks = [ip_network(value.strip()) for value in app.config.get('TRUSTED_PROXY_CIDRS', '').split(',') if value.strip()]
        if any(network.prefixlen == 0 for network in networks) or (any(counts) and not networks):
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Invalid trusted-proxy configuration') from None
    original = app.wsgi_app
    fixed = ProxyFix(original, x_for=counts[0], x_proto=counts[1], x_host=0, x_port=0, x_prefix=0)

    def dispatch(environ, start_response):
        try:
            peer = ip_address(environ.get('REMOTE_ADDR', ''))
            trusted = any(peer in network for network in networks)
        except ValueError:
            trusted = False
        return (fixed if trusted else original)(environ, start_response)

    app.wsgi_app = dispatch
