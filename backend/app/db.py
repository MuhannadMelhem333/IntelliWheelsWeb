import sqlite3
import os
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from flask import g, current_app

# PostgreSQL support
try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

# Global connection pool (shared across requests for huge performance gain)
_connection_pool = None


def _create_postgres_connection(connect_timeout=10):
    """Create a direct PostgreSQL connection using normalized DATABASE_URL."""
    database_url = _get_database_url()
    # Certificate failures must not weaken the caller's TLS policy.
    return psycopg2.connect(database_url, connect_timeout=connect_timeout)


def _is_connection_alive(connection):
    """Lightweight ping to detect stale pooled connections."""
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        return True
    except Exception:
        return False

def is_postgres():
    """Select the configured database without silently changing storage."""
    configured = bool(os.environ.get('DATABASE_URL'))
    if configured and not HAS_POSTGRES:
        raise RuntimeError('PostgreSQL driver is required when DATABASE_URL is configured')
    return configured

class PostgresRowWrapper:
    """Wrapper to make psycopg2 rows behave like sqlite3.Row."""
    def __init__(self, cursor, row):
        self._data = dict(zip([desc[0] for desc in cursor.description], row))
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self._data.values())[key]
        return self._data[key]
    
    def keys(self):
        return self._data.keys()
    
    def __iter__(self):
        return iter(self._data.values())

class PostgresCursorWrapper:
    """Wrapper to make psycopg2 cursor behave like sqlite3 cursor."""
    def __init__(self, cursor, connection):
        self._cursor = cursor
        self._connection = connection
        self.lastrowid = None
    
    def execute(self, sql, params=None):
        original_sql = sql
        # Skip conversion if already using PostgreSQL placeholders (%s)
        if '%s' not in sql:
            # Convert SQLite-style ? placeholders to PostgreSQL %s
            sql = sql.replace('?', '%s')
        # Handle AUTOINCREMENT -> SERIAL (already handled in CREATE)
        # Handle json_extract -> PostgreSQL JSON operators
        sql = self._convert_json_extract(sql)
        # Handle CURRENT_TIMESTAMP -> NOW() ONLY for non-CREATE TABLE statements
        # PostgreSQL supports CURRENT_TIMESTAMP as a default in CREATE TABLE,
        # but NOW() as a default causes errors
        if 'CREATE TABLE' not in sql.upper():
            sql = sql.replace('CURRENT_TIMESTAMP', 'NOW()')
        # Convert INSERT OR IGNORE to PostgreSQL ON CONFLICT (for any remaining cases)
        if 'INSERT OR IGNORE' in sql.upper():
            sql = sql.replace('INSERT OR IGNORE', 'INSERT')
            sql = sql.replace('insert or ignore', 'INSERT')
            # Add ON CONFLICT DO NOTHING if not already present
            if 'ON CONFLICT' not in sql.upper():
                sql = sql.rstrip(';').rstrip() + ' ON CONFLICT DO NOTHING'
        
        # For INSERT statements to tables with SERIAL id, add RETURNING id to get the lastrowid.
        # Exclude tables that don't have SERIAL id:
        # - user_sessions: uses TEXT PRIMARY KEY (token)
        # - favorites: uses composite PRIMARY KEY (user_id, car_id)
        sql_lower = sql.lower()
        tables_without_serial_id = ['user_sessions', 'favorites']
        has_serial_id = not any(table in sql_lower for table in tables_without_serial_id)
        
        needs_returning = (
            sql.strip().upper().startswith('INSERT') and 
            'RETURNING' not in sql.upper() and 
            'ON CONFLICT' not in sql.upper() and
            has_serial_id
        )
        if needs_returning:
            sql = sql.rstrip(';').rstrip() + ' RETURNING id'
        
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        
        # Get lastrowid from RETURNING clause if we added it
        if needs_returning:
            try:
                result = self._cursor.fetchone()
                if result:
                    self.lastrowid = result[0]
            except Exception:
                pass  # No result to fetch
        
        return self
    
    def _convert_json_extract(self, sql):
        """Convert SQLite json_extract to PostgreSQL JSON operators."""
        import re
        # Pattern: json_extract(column, '$.key') -> column->>'key'
        pattern = r"json_extract\s*\(\s*(\w+)\s*,\s*'\$\.(\w+)'\s*\)"
        sql = re.sub(pattern, r"\1->>'\2'", sql)
        return sql
    
    def fetchone(self):
        row = self._cursor.fetchone()
        if row and self._cursor.description:
            return PostgresRowWrapper(self._cursor, row)
        return row
    
    def fetchall(self):
        rows = self._cursor.fetchall()
        if rows and self._cursor.description:
            return [PostgresRowWrapper(self._cursor, row) for row in rows]
        return rows

class PostgresConnectionWrapper:
    """Wrapper to make psycopg2 connection behave like sqlite3 connection."""
    def __init__(self, connection):
        self._connection = connection
        self._cursor = None
    
    def execute(self, sql, params=None):
        cursor = self._connection.cursor()
        wrapper = PostgresCursorWrapper(cursor, self._connection)
        wrapper.execute(sql, params)
        return wrapper
    
    def commit(self):
        try:
            self._connection.commit()
            print("[DB] PostgreSQL commit successful")
        except Exception as e:
            print('[DB] PostgreSQL commit failed')
            raise
    
    def rollback(self):
        self._connection.rollback()
    
    def close(self):
        self._connection.close()
    
    @property
    def row_factory(self):
        return None
    
    @row_factory.setter
    def row_factory(self, value):
        pass  # PostgreSQL handles this differently

def _get_database_url():
    """Normalize the DATABASE_URL for psycopg2."""
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    elif database_url.startswith('cockroachdb://'):
        database_url = database_url.replace('cockroachdb://', 'postgresql://', 1)

    # Normalize query params so cloud Postgres/Cockroach works across environments.
    try:
        parsed = urlparse(database_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        host = (parsed.hostname or '').lower()
        is_cloud_db = any(
            domain in host for domain in [
                'cockroachlabs.cloud', 'neon.tech', 'render.com', 'supabase.co'
            ]
        )

        # If no sslmode is provided for a cloud DB, default to require.
        if is_cloud_db and 'sslmode' not in query:
            query['sslmode'] = 'require'

        # Cockroach commonly uses verify-full; on Render/libpq this needs explicit system roots.
        # Otherwise libpq tries /opt/render/.postgresql/root.crt and fails startup.
        sslmode = query.get('sslmode', '').lower()
        if is_cloud_db and sslmode in ('verify-ca', 'verify-full') and 'sslrootcert' not in query:
            query['sslrootcert'] = 'system'

        database_url = urlunparse(parsed._replace(query=urlencode(query)))
    except Exception as e:
        print('[DB] DATABASE_URL normalization failed')

    return database_url

def _get_pool():
    """Get or create the global connection pool (lazy init, thread-safe)."""
    global _connection_pool
    if _connection_pool is None and is_postgres() and HAS_POSTGRES:
        database_url = _get_database_url()
        try:
            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=database_url,
                connect_timeout=10,
            )
            print("[DB] Connection pool created (1-10 connections)")
        except Exception as e:
            print('[DB] Failed to create connection pool')
            _connection_pool = None
    return _connection_pool

def get_db():
    if 'db' not in g:
        if is_postgres() and HAS_POSTGRES:
            try:
                pool = _get_pool()
                conn = None
                from_pool = False

                if pool:
                    conn = pool.getconn()
                    from_pool = True

                    # Render/Cockroach connections can go stale. Replace dead pooled connections.
                    if not _is_connection_alive(conn):
                        print("[DB] Detected stale pooled connection; replacing")
                        try:
                            pool.putconn(conn, close=True)
                        except Exception:
                            pass
                        conn = _create_postgres_connection(connect_timeout=10)
                        from_pool = False

                if conn is None:
                    # Fallback: direct connection if pool failed or unavailable
                    conn = _create_postgres_connection(connect_timeout=10)
                    from_pool = False
                    print("[DB] Connected to PostgreSQL/CockroachDB (no pool)")

                conn.autocommit = False
                g.db = PostgresConnectionWrapper(conn)
                g._db_from_pool = from_pool
            except Exception as e:
                # Bubble up a clear error for logs and error handlers.
                print('[DB] PostgreSQL connection failed')
                raise RuntimeError("Database connection unavailable") from e
        else:
            db_path = current_app.config['DATABASE']
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
            g._db_from_pool = False
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    from_pool = g.pop('_db_from_pool', False)
    if db is not None:
        if from_pool and _connection_pool:
            # Return connection to pool (don't close it!)
            try:
                db._connection.rollback()  # Clear any uncommitted transaction
            except Exception:
                pass
            _connection_pool.putconn(db._connection)
        else:
            db.close()

def init_db(app):
    with app.app_context():
        db = get_db()
        
        if is_postgres() and HAS_POSTGRES:
            _init_postgres_tables(db)
        else:
            _init_sqlite_tables(db)

def _init_postgres_tables(db):
    """Initialize PostgreSQL / CockroachDB tables.
    
    Uses INT GENERATED BY DEFAULT AS IDENTITY instead of SERIAL to ensure
    sequential IDs that fit within JavaScript's Number.MAX_SAFE_INTEGER.
    (CockroachDB's SERIAL uses unique_rowid() which produces 64-bit IDs
    that exceed JS safe integer range and get corrupted in JSON.)
    """
    cursor = db._connection.cursor()
    
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT8 GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    # Create Sessions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            token TEXT PRIMARY KEY,
            user_id INT8 NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP
        )
    ''')
    
    # Create Cars Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INT8 GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            owner_id INT8,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER,
            price REAL,
            currency TEXT DEFAULT 'JOD',
            odometer_km INTEGER,
            image_url TEXT,
            image_urls JSONB,
            gallery_images JSONB,
            media_gallery JSONB,
            video_url TEXT,
            rating REAL,
            reviews INTEGER DEFAULT 0,
            description TEXT,
            specs JSONB,
            engines JSONB,
            statistics JSONB,
            source_sheets JSONB,
            category TEXT DEFAULT 'car',
            condition TEXT DEFAULT 'used',
            exterior_color TEXT,
            interior_color TEXT,
            transmission TEXT,
            fuel_type TEXT,
            regional_spec TEXT,
            payment_type TEXT DEFAULT 'cash',
            city TEXT,
            neighborhood TEXT,
            trim TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    # Create Dealers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dealers (
            id INT8 GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            rating REAL DEFAULT 0,
            reviews_count INTEGER DEFAULT 0,
            image_url TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Create Dealer Applications Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dealer_applications (
            id INT8 GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT,
            website TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            admin_notes TEXT,
            reviewed_by INT8 REFERENCES users(id),
            reviewed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Create Callbacks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS callbacks (
            id INT8 GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            car_id INT8,
            user_id INT8,
            name TEXT,
            phone TEXT,
            message TEXT,
            preferred_time TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    # Create Favorites Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INT8 NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            car_id INT8 NOT NULL REFERENCES cars(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (user_id, car_id)
        )
    ''')
    
    # Create Reviews Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INT8 GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            car_id INT8 NOT NULL REFERENCES cars(id) ON DELETE CASCADE,
            user_id INT8 NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(car_id, user_id)
        )
    ''')
    
    # Migrations: Add new columns if they don't exist
    migrations = [
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS odometer_km INTEGER",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'car'",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS condition TEXT DEFAULT 'used'",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS exterior_color TEXT",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS interior_color TEXT",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS transmission TEXT",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS fuel_type TEXT",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS regional_spec TEXT",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS payment_type TEXT DEFAULT 'cash'",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS city TEXT",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS neighborhood TEXT",
        "ALTER TABLE cars ADD COLUMN IF NOT EXISTS trim TEXT",
        # User columns
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT",
    ]
    for migration in migrations:
        try:
            cursor.execute(migration)
        except Exception as e:
            print('[DB] Optional migration failed')
    
    # Create Password Resets Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INT8 GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            token TEXT UNIQUE NOT NULL,
            user_id INT8 NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    db._connection.commit()
    print("[DB] PostgreSQL/CockroachDB tables initialized")

def _init_sqlite_tables(db):
    """Initialize SQLite tables."""
    cursor = db.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Sessions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create Cars Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER,
            price REAL,
            currency TEXT DEFAULT 'JOD',
            odometer_km INTEGER,
            image_url TEXT,
            image_urls JSON,
            gallery_images JSON,
            media_gallery JSON,
            video_url TEXT,
            rating REAL,
            reviews INTEGER DEFAULT 0,
            description TEXT,
            specs JSON,
            engines JSON,
            statistics JSON,
            source_sheets JSON,
            category TEXT DEFAULT 'car',
            condition TEXT DEFAULT 'used',
            exterior_color TEXT,
            interior_color TEXT,
            transmission TEXT,
            fuel_type TEXT,
            regional_spec TEXT,
            payment_type TEXT DEFAULT 'cash',
            city TEXT,
            neighborhood TEXT,
            trim TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Dealers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dealers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            rating REAL DEFAULT 0,
            reviews_count INTEGER DEFAULT 0,
            image_url TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Dealer Applications Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dealer_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT,
            website TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            admin_notes TEXT,
            reviewed_by INTEGER REFERENCES users(id),
            reviewed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Callbacks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS callbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            message TEXT,
            preferred_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Favorites Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, car_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (car_id) REFERENCES cars (id) ON DELETE CASCADE
        )
    ''')
    
    # Create Reviews Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (car_id) REFERENCES cars (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(car_id, user_id)
        )
    ''')
    
    # Create Password Resets Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Migrations for SQLite (doesn't support IF NOT EXISTS for ALTER)
    sqlite_migrations = [
        "ALTER TABLE cars ADD COLUMN odometer_km INTEGER",
        "ALTER TABLE users ADD COLUMN google_id TEXT",
        "ALTER TABLE users ADD COLUMN avatar_url TEXT",
    ]
    for migration in sqlite_migrations:
        try:
            cursor.execute(migration)
        except Exception:
            pass  # Column likely already exists
    
    db.commit()
    print("[DB] SQLite tables initialized")

def init_app(app):
    app.teardown_appcontext(close_db)
    init_db(app)
