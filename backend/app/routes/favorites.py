from flask import Blueprint, request, jsonify
import os
from ..db import get_db, is_postgres
from .auth import get_user_from_token
from ..cookie_auth import request_session_token
from .cars import car_row_to_dict

bp = Blueprint('favorites', __name__, url_prefix='/api/favorites')


def ensure_favorites_table():
    """Create favorites table if it doesn't exist."""
    db = get_db()
    try:
        if is_postgres():
            db.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    car_id INTEGER NOT NULL REFERENCES cars(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, car_id)
                )
            ''')
        else:
            db.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER NOT NULL,
                    car_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, car_id),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (car_id) REFERENCES cars (id) ON DELETE CASCADE
                )
            ''')
        db.commit()
    except Exception as e:
        print('[Favorites] Table initialization failed')
        try:
            db.rollback()
        except:
            pass


@bp.route('', methods=['GET'])
def get_favorites():
    token = request_session_token()
    user = get_user_from_token(token)
    
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    db = get_db()
    ensure_favorites_table()
    
    try:
        if is_postgres():
            cursor = db.execute('''
                SELECT c.* 
                FROM cars c
                JOIN favorites f ON c.id = f.car_id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
            ''', (user['id'],))
        else:
            cursor = db.execute('''
                SELECT c.* 
                FROM cars c
                JOIN favorites f ON c.id = f.car_id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
            ''', (user['id'],))
        
        cars = [car_row_to_dict(row) for row in cursor.fetchall()]
        return jsonify({'success': True, 'cars': cars})
    except Exception as e:
        print('[Favorites] Fetch failed')
        return jsonify({'success': True, 'cars': []})  # Return empty list on error

@bp.route('', methods=['POST'])
def add_favorite():
    token = request_session_token()
    user = get_user_from_token(token)
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.json
    car_id = data.get('car_id')
    
    if not car_id:
        return jsonify({'success': False, 'error': 'car_id required'}), 400

    db = get_db()
    ensure_favorites_table()

    try:
        if is_postgres():
            db.execute(
                'INSERT INTO favorites (user_id, car_id) VALUES (%s, %s) ON CONFLICT (user_id, car_id) DO NOTHING',
                (user['id'], car_id)
            )
        else:
            db.execute('INSERT OR IGNORE INTO favorites (user_id, car_id) VALUES (?, ?)', (user['id'], car_id))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        print('[Favorites] Add failed')
        return jsonify({'success': False, 'error': 'Failed to add favorite'}), 500

@bp.route('/<int:car_id>', methods=['DELETE'])
def remove_favorite(car_id):
    token = request_session_token()
    user = get_user_from_token(token)
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    db = get_db()
    ensure_favorites_table()
    
    try:
        if is_postgres():
            db.execute('DELETE FROM favorites WHERE user_id = %s AND car_id = %s', (user['id'], car_id))
        else:
            db.execute('DELETE FROM favorites WHERE user_id = ? AND car_id = ?', (user['id'], car_id))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        print('[Favorites] Remove failed')
        return jsonify({'success': False, 'error': 'Failed to remove favorite'}), 500
