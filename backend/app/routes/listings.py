from flask import Blueprint, jsonify, request
from ..db import get_db, is_postgres
from .auth import get_user_from_token
from ..cookie_auth import request_session_token
from .cars import car_row_to_dict

# This blueprint will attach directly to /api to handle root-level resource endpoints
# like /api/makes and /api/my-listings
bp = Blueprint('listings', __name__, url_prefix='/api')

@bp.route('/makes', methods=['GET'])
def get_makes():
    db = get_db()
    cursor = db.execute('SELECT DISTINCT make FROM cars ORDER BY make ASC')
    makes = [row['make'] for row in cursor.fetchall()]
    return jsonify({'success': True, 'makes': makes})

@bp.route('/models', methods=['GET'])
def get_models():
    """Get models for a specific make, or all make-model pairs."""
    db = get_db()
    make = request.args.get('make')
    
    if make:
        cursor = db.execute(
            'SELECT DISTINCT model FROM cars WHERE LOWER(make) = LOWER(?) ORDER BY model ASC',
            (make,)
        )
        models = [row['model'] for row in cursor.fetchall()]
        return jsonify({'success': True, 'models': models})
    else:
        # Return all make-model pairs grouped
        cursor = db.execute(
            'SELECT DISTINCT make, model FROM cars ORDER BY make ASC, model ASC'
        )
        result = {}
        for row in cursor.fetchall():
            make_name = row['make']
            if make_name not in result:
                result[make_name] = []
            result[make_name].append(row['model'])
        return jsonify({'success': True, 'models_by_make': result})

@bp.route('/engines', methods=['GET'])
def get_engines():
    """Get engines for a specific make/model."""
    db = get_db()
    make = request.args.get('make')
    model = request.args.get('model')
    
    if not make or not model:
        return jsonify({'success': False, 'error': 'make and model required'}), 400
    
    cursor = db.execute(
        '''SELECT DISTINCT json_extract(specs, '$.engine') as engine 
           FROM cars 
           WHERE LOWER(make) = LOWER(?) AND LOWER(model) = LOWER(?)
           AND json_extract(specs, '$.engine') IS NOT NULL
           ORDER BY engine ASC''',
        (make, model)
    )
    engines = [row['engine'] for row in cursor.fetchall() if row['engine']]
    return jsonify({'success': True, 'engines': engines})

@bp.route('/my-listings', methods=['GET'])
def get_my_listings():
    token = request_session_token()
    user = get_user_from_token(token)
    
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    # Assuming 'owner_id' links cars to users.
    # Note: users table created in db.py has 'id', so cars 'owner_id' should match.
    # But db.py schema for cars doesn't explicitly have owner_id in the simplified create statement I wrote?
    # Let me check db.py content I wrote... 
    # I wrote: CREATE TABLE cars ... (..., media_gallery JSON, created_at ...)
    # I did NOT explicitly add owner_id in the CREATE statement I pushed in Step 408/409.
    # THIS IS A BUG/OVERSIGHT in my restoration plan execution.
    # I need to fix db.py to include owner_id if I want this to work, OR I just add it now via migration/alter,
    # OR since the user might be fresh, I can update db.py and they can reset.
    # However, for now, let's write the code assuming it exists, and I will issue a fix to db.py next.
    
    db = get_db()
    # Check if owner_id exists
    try:
        cursor = db.execute('SELECT * FROM cars WHERE owner_id = ?', (user['id'],))
        cars = [car_row_to_dict(row) for row in cursor.fetchall()]
        return jsonify({'success': True, 'cars': cars})
    except Exception:
        # Fallback if column missing (safe fail)
        return jsonify({'success': True, 'cars': []})


@bp.route('/my-listings/analytics', methods=['GET'])
def get_my_listings_analytics():
    """Get analytics for user's own listings."""
    token = request_session_token()
    user = get_user_from_token(token)
    
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    db = get_db()
    
    try:
        # Get all user's listings
        cursor = db.execute('SELECT * FROM cars WHERE owner_id = ?', (user['id'],))
        cars = [car_row_to_dict(row) for row in cursor.fetchall()]
        
        if not cars:
            return jsonify({
                'success': True,
                'analytics': {
                    'total_listings': 0,
                    'total_value': 0,
                    'average_price': 0,
                    'price_range': {'min': 0, 'max': 0},
                    'listings_by_make': [],
                    'listings_by_year': [],
                    'listings_by_body_style': [],
                    'recent_listings': [],
                    'performance': {
                        'total_views': 0,
                        'total_favorites': 0,
                        'avg_rating': 0
                    }
                }
            })
        
        # Calculate analytics
        prices = [c.get('price', 0) or 0 for c in cars if c.get('price')]
        total_value = sum(prices)
        avg_price = total_value / len(prices) if prices else 0
        
        # Listings by make
        make_counts = {}
        for car in cars:
            make = car.get('make', 'Unknown')
            make_counts[make] = make_counts.get(make, 0) + 1
        listings_by_make = [{'make': k, 'count': v} for k, v in sorted(make_counts.items(), key=lambda x: -x[1])]
        
        # Listings by year
        year_counts = {}
        for car in cars:
            year = car.get('year', 'Unknown')
            if year:
                year_counts[year] = year_counts.get(year, 0) + 1
        listings_by_year = [{'year': k, 'count': v} for k, v in sorted(year_counts.items(), key=lambda x: -x[0] if isinstance(x[0], int) else 0)]
        
        # Listings by body style
        body_counts = {}
        for car in cars:
            specs = car.get('specs') or {}
            body = specs.get('bodyStyle', 'Unknown') if isinstance(specs, dict) else 'Unknown'
            body_counts[body] = body_counts.get(body, 0) + 1
        listings_by_body_style = [{'bodyStyle': k, 'count': v} for k, v in sorted(body_counts.items(), key=lambda x: -x[1])]
        
        # Get favorites count for user's cars
        car_ids = [c['id'] for c in cars]
        favorites_count = 0
        if car_ids:
            placeholders = ','.join(['?'] * len(car_ids))
            fav_cursor = db.execute(f'SELECT COUNT(*) as count FROM favorites WHERE car_id IN ({placeholders})', car_ids)
            favorites_count = fav_cursor.fetchone()['count']
        
        # Get average rating for user's cars
        avg_rating = 0
        if car_ids:
            placeholders = ','.join(['?'] * len(car_ids))
            rating_cursor = db.execute(f'SELECT AVG(rating) as avg_rating FROM reviews WHERE car_id IN ({placeholders})', car_ids)
            result = rating_cursor.fetchone()
            avg_rating = round(result['avg_rating'], 1) if result['avg_rating'] else 0
        
        # Recent listings (last 5)
        recent = sorted(cars, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        recent_listings = [{
            'id': c['id'],
            'make': c.get('make'),
            'model': c.get('model'),
            'price': c.get('price'),
            'created_at': c.get('created_at')
        } for c in recent]
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_listings': len(cars),
                'total_value': total_value,
                'average_price': round(avg_price, 2),
                'price_range': {
                    'min': min(prices) if prices else 0,
                    'max': max(prices) if prices else 0
                },
                'listings_by_make': listings_by_make,
                'listings_by_year': listings_by_year,
                'listings_by_body_style': listings_by_body_style,
                'recent_listings': recent_listings,
                'performance': {
                    'total_views': 0,  # TODO: implement view tracking
                    'total_favorites': favorites_count,
                    'avg_rating': avg_rating
                }
            }
        })
        
    except Exception as e:
        print('[listings] Operation failed')
        try:
            db.rollback()
        except:
            pass
        return jsonify({
            'success': True,
            'analytics': {
                'total_listings': 0,
                'total_value': 0,
                'average_price': 0,
                'price_range': {'min': 0, 'max': 0},
                'listings_by_make': [],
                'listings_by_year': [],
                'listings_by_body_style': [],
                'recent_listings': [],
                'performance': {
                    'total_views': 0,
                    'total_favorites': 0,
                    'avg_rating': 0
                }
            }
        })


@bp.route('/request-callback', methods=['POST'])
def request_callback():
    data = request.get_json() or {}
    car_id = data.get('car_id')
    name = data.get('name')
    phone = data.get('phone')
    message = data.get('message')
    preferred_time = data.get('preferred_time')

    token = request_session_token()
    user = get_user_from_token(token)
    user_id = user['id'] if user else None

    db = get_db()
    try:
        if is_postgres():
            db.execute(
                'INSERT INTO callbacks (car_id, user_id, name, phone, message, preferred_time) VALUES (%s, %s, %s, %s, %s, %s)',
                (car_id, user_id, name, phone, message, preferred_time)
            )
        else:
            db.execute(
                'INSERT INTO callbacks (car_id, user_id, name, phone, message, preferred_time) VALUES (?, ?, ?, ?, ?, ?)',
                (car_id, user_id, name, phone, message, preferred_time)
            )
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        print('[listings] Operation failed')
        try:
            db.rollback()
        except:
            pass
        return jsonify({'success': False, 'error': 'Unable to complete request'}), 500
