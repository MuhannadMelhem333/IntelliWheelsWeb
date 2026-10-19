import os
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from .db import init_app as init_db
from .security import add_security_headers
from .cookie_auth import install_cookie_auth
from .frontend_origin import resolve_reset_origin
from .rate_limits import build_rate_limiter
from .trusted_proxy import configure_trusted_proxy

# Load environment variables from .env file
load_dotenv()

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Validate required environment variables
    secret_key = os.environ.get('SECRET_KEY', '')
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    # Check if secret key is valid (not empty, not 'dev', and at least 32 chars)
    is_valid_key = secret_key and secret_key != 'dev' and len(secret_key) >= 32
    
    if not is_valid_key:
        if is_production:
            raise ValueError("SECRET_KEY must be set to a secure value (32+ chars) in production!")
        print("⚠️  WARNING: Using insecure SECRET_KEY. Set a proper one for production!")
        secret_key = 'dev-only-insecure-key-for-local-testing'
    
    # Get allowed origins from environment
    frontend_origin = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:3000')
    allowed_origins = [origin.strip() for origin in frontend_origin.split(',')]
    
    # Determine database path
    db_path = os.environ.get('DATABASE_PATH', os.path.join(app.root_path, '..', 'intelliwheels.db'))
    print(f"[App Init] Database path: {db_path}")
    print(f"[App Init] Database exists: {os.path.exists(db_path)}")
    
    # Configuration
    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=db_path,
        UPLOAD_FOLDER=os.path.join(app.root_path, '..', 'uploads'),
        MAX_CONTENT_LENGTH=101 * 1024 * 1024,  # 100MB video plus multipart overhead
        IMAGE_UPLOAD_MAX_BYTES=15 * 1024 * 1024,
        VIDEO_UPLOAD_MAX_BYTES=100 * 1024 * 1024,
        VIDEO_UPLOAD_MAX_SECONDS=120,
        FFPROBE_PATH=os.environ.get('FFPROBE_PATH', 'ffprobe'),
        LOCAL_UPLOADS_ALLOWED=os.environ.get('FLASK_ENV', 'development') == 'development',
        # Enable only after explicit migration and staging acceptance.
        MEDIA_ASSET_LEDGER_ENABLED=False,
        UPLOAD_QUOTAS_ENABLED=False,
        SIGNED_UPLOADS_ENABLED=False,
        SIGNED_UPLOAD_PRESETS_VERIFIED=False,
        SIGNED_UPLOAD_IMAGE_PRESET='',
        SIGNED_UPLOAD_VIDEO_PRESET='',
        SIGNED_UPLOAD_ENVIRONMENT='development',
        UPLOAD_USER_MAX_ASSETS=100,
        UPLOAD_USER_MAX_BYTES=1024 * 1024 * 1024,
        # Security settings
        SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        # Keep disabled until frontend and CSRF callers migrate together.
        COOKIE_AUTH_ENABLED=False,
        COOKIE_AUTH_ORIGINS=allowed_origins,
        PASSWORD_RESET_ORIGIN=os.environ.get('PASSWORD_RESET_ORIGIN'),
        RATE_LIMIT_REDIS_URL=os.environ.get('RATE_LIMIT_REDIS_URL'),
        RATE_LIMIT_NAMESPACE=os.environ.get('RATE_LIMIT_NAMESPACE'),
        TRUSTED_PROXY_CIDRS=os.environ.get('TRUSTED_PROXY_CIDRS', ''),
        TRUSTED_PROXY_X_FOR=os.environ.get('TRUSTED_PROXY_X_FOR', '0'),
        TRUSTED_PROXY_X_PROTO=os.environ.get('TRUSTED_PROXY_X_PROTO', '0'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.extensions['rate_limiter'] = build_rate_limiter(app.config)
    configure_trusted_proxy(app)

    app.config['PASSWORD_RESET_ORIGIN'] = resolve_reset_origin(
        app.config['PASSWORD_RESET_ORIGIN'], allowed_origins,
        development=os.environ.get('FLASK_ENV', 'development') == 'development',
    )

    if app.config['COOKIE_AUTH_ENABLED']:
        # Hosted staging must not inherit the old development cookie policy.
        if os.environ.get('FLASK_ENV') != 'development':
            if not is_valid_key:
                raise ValueError('Cookie authentication requires a secure SECRET_KEY')
            app.config['SESSION_COOKIE_SECURE'] = True
        if not app.config['COOKIE_AUTH_ORIGINS'] or '*' in app.config['COOKIE_AUTH_ORIGINS']:
            raise ValueError('Cookie authentication requires explicit trusted origins')

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Ensure uploads folder exists
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError:
        pass

    # Initialize CORS with proper origin restrictions
    CORS(app, 
         resources={r"/api/*": {
             "origins": app.config['COOKIE_AUTH_ORIGINS'] if app.config['COOKIE_AUTH_ENABLED'] else (allowed_origins if is_production else "*"),
             "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "X-CSRF-Token", "X-Session-Version"],
             "supports_credentials": app.config['COOKIE_AUTH_ENABLED']
         }})
    
    # Add security headers to all responses
    app.after_request(add_security_headers)
    install_cookie_auth(app)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Preserve status codes and headers for intentional HTTP errors.
        if isinstance(error, HTTPException):
            return error
        # Never attach exception messages/tracebacks, headers or request data.
        app.logger.error('request.unexpected_error')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    init_db(app)

    # Register Blueprints
    from .routes import cars, ai, system, auth, dealers, favorites, listings, reviews, messages
    from .signed_uploads import bp as signed_uploads_bp
    app.register_blueprint(signed_uploads_bp)
    app.register_blueprint(cars.bp)
    app.register_blueprint(ai.bp)
    app.register_blueprint(system.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dealers.bp)
    app.register_blueprint(favorites.bp)
    app.register_blueprint(listings.bp)
    app.register_blueprint(reviews.bp)
    app.register_blueprint(messages.bp)
    
    # Setup Swagger UI
    SWAGGER_URL = '/api/docs'
    API_URL = '/api/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "IntelliWheels API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    # Serve swagger.json from static folder
    @app.route('/api/swagger.json')
    def swagger_spec():
        return app.send_static_file('swagger.json')

    return app

# Expose app instance for 'gunicorn app:app' or 'gunicorn run:app'
def get_app():
    return create_app()

app = get_app()
