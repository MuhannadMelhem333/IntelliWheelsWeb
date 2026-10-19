from flask import Blueprint, jsonify, request, g
from ..db import get_db, is_postgres
from ..security import token_required, rate_limit
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

bp = Blueprint('dealers', __name__, url_prefix='/api/dealers')

# Email configuration (set these in environment variables for production)
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@intelliwheels.co')

def send_email(to_email, subject, body):
    """Send an email notification. Returns True if sent, False otherwise."""
    if not SMTP_HOST or not SMTP_USER:
        # Do not log request content or personal data.
        # Do not log request content or personal data.
        return False  # Email not configured
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print('[dealers] Operation failed')
        return False

@bp.route('', methods=['GET'])
def get_dealers():
    db = get_db()
    cursor = db.execute('SELECT * FROM dealers ORDER BY rating DESC')
    dealers = [dict(row) for row in cursor.fetchall()]
    return jsonify({'success': True, 'dealers': dealers})

@bp.route('/<int:id>', methods=['GET'])
def get_dealer(id):
    db = get_db()
    
    dealer_row = db.execute('SELECT * FROM dealers WHERE id = ?', (id,)).fetchone()
    if not dealer_row:
        return jsonify({'success': False, 'error': 'Dealer not found'}), 404
    
    dealer = dict(dealer_row)
    dealer['inventory'] = [] 
    dealer['reviews'] = []
    
    return jsonify({'success': True, 'dealer': dealer})

# ============ DEALER APPLICATIONS ============

@bp.route('/applications', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60)
def submit_application():
    """Submit a new dealer application"""
    data = request.get_json()
    
    required_fields = ['name', 'email', 'phone', 'city']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    db = get_db()
    
    try:
        # Check if email already has a pending application
        if is_postgres():
            existing = db.execute(
                'SELECT id FROM dealer_applications WHERE email = %s AND status = %s',
                (data['email'], 'pending')
            ).fetchone()
        else:
            existing = db.execute(
                'SELECT id FROM dealer_applications WHERE email = ? AND status = ?',
                (data['email'], 'pending')
            ).fetchone()
        
        if existing:
            return jsonify({
                'success': False, 
                'error': 'You already have a pending application'
            }), 400
        
        if is_postgres():
            cursor = db.execute('''
                INSERT INTO dealer_applications (name, email, phone, city, address, website, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (
                data['name'],
                data['email'],
                data['phone'],
                data['city'],
                data.get('address', ''),
                data.get('website', ''),
                data.get('description', '')
            ))
            app_id = cursor.fetchone()['id']
        else:
            cursor = db.execute('''
                INSERT INTO dealer_applications (name, email, phone, city, address, website, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['email'],
                data['phone'],
                data['city'],
                data.get('address', ''),
                data.get('website', ''),
                data.get('description', '')
            ))
            app_id = cursor.lastrowid
        db.commit()
        
        # Send notification to admin
        send_email(
            ADMIN_EMAIL,
            '🚗 New Dealer Application - IntelliWheels',
            f'''
            <h2>New Dealer Application Received</h2>
            <p><strong>Dealership Name:</strong> {data['name']}</p>
            <p><strong>Contact Email:</strong> {data['email']}</p>
            <p><strong>Phone:</strong> {data['phone']}</p>
            <p><strong>City:</strong> {data['city']}</p>
            <p><strong>Address:</strong> {data.get('address', 'Not provided')}</p>
            <p><strong>Website:</strong> {data.get('website', 'Not provided')}</p>
            <p><strong>Description:</strong> {data.get('description', 'Not provided')}</p>
            <hr>
            <p>Log in to the admin panel to review this application.</p>
            '''
        )
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully. We will review it within 48 hours.',
            'application_id': app_id
        })
    except Exception as e:
        print('[dealers] Operation failed')
        try:
            db.rollback()
        except:
            pass
        return jsonify({'success': False, 'error': 'Failed to submit application'}), 500

@bp.route('/applications', methods=['GET'])
@rate_limit(max_requests=60, window_seconds=60)
@token_required
def get_applications():
    """Get all dealer applications (admin only)"""
    current_user = g.current_user
    if not current_user.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    status_filter = request.args.get('status', None)
    db = get_db()
    
    try:
        if is_postgres():
            if status_filter:
                cursor = db.execute(
                    'SELECT * FROM dealer_applications WHERE status = %s ORDER BY created_at DESC',
                    (status_filter,)
                )
            else:
                cursor = db.execute('SELECT * FROM dealer_applications ORDER BY created_at DESC')
        else:
            if status_filter:
                cursor = db.execute(
                    'SELECT * FROM dealer_applications WHERE status = ? ORDER BY created_at DESC',
                    (status_filter,)
                )
            else:
                cursor = db.execute('SELECT * FROM dealer_applications ORDER BY created_at DESC')
        
        applications = [dict(row) for row in cursor.fetchall()]
        return jsonify({'success': True, 'applications': applications})
    except Exception as e:
        print('[dealers] Operation failed')
        try:
            db.rollback()
        except:
            pass
        return jsonify({'success': False, 'error': 'Failed to fetch applications'}), 500

@bp.route('/applications/<int:id>', methods=['GET'])
@rate_limit(max_requests=60, window_seconds=60)
@token_required
def get_application(id):
    """Get a specific application (admin only)"""
    current_user = g.current_user
    if not current_user.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    db = get_db()
    try:
        if is_postgres():
            app_row = db.execute('SELECT * FROM dealer_applications WHERE id = %s', (id,)).fetchone()
        else:
            app_row = db.execute('SELECT * FROM dealer_applications WHERE id = ?', (id,)).fetchone()
        
        if not app_row:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        
        return jsonify({'success': True, 'application': dict(app_row)})
    except Exception as e:
        print('[dealers] Operation failed')
        try:
            db.rollback()
        except:
            pass
        return jsonify({'success': False, 'error': 'Failed to fetch application'}), 500

@bp.route('/applications/<int:id>/approve', methods=['PUT'])
@rate_limit(max_requests=20, window_seconds=60)
@token_required
def approve_application(id):
    """Approve a dealer application (admin only)"""
    current_user = g.current_user
    if not current_user.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    data = request.get_json() or {}
    admin_notes = data.get('notes', '')
    
    db = get_db()
    try:
        if is_postgres():
            app_row = db.execute('SELECT * FROM dealer_applications WHERE id = %s', (id,)).fetchone()
        else:
            app_row = db.execute('SELECT * FROM dealer_applications WHERE id = ?', (id,)).fetchone()
        
        if not app_row:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        
        app_data = dict(app_row)
        
        if app_data['status'] != 'pending':
            return jsonify({'success': False, 'error': 'Application already processed'}), 400
        
        # Update application status
        if is_postgres():
            db.execute('''
                UPDATE dealer_applications 
                SET status = %s, admin_notes = %s, reviewed_by = %s, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', ('approved', admin_notes, current_user['id'], id))
            
            # Create dealer record
            db.execute('''
                INSERT INTO dealers (name, location, contact_email, contact_phone)
                VALUES (%s, %s, %s, %s)
            ''', (app_data['name'], app_data['city'], app_data['email'], app_data['phone']))
        else:
            db.execute('''
                UPDATE dealer_applications 
                SET status = ?, admin_notes = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', ('approved', admin_notes, current_user['id'], id))
            
            # Create dealer record
            db.execute('''
                INSERT INTO dealers (name, location, contact_email, contact_phone)
                VALUES (?, ?, ?, ?)
            ''', (app_data['name'], app_data['city'], app_data['email'], app_data['phone']))
        
        db.commit()
        
        # Send approval email
        send_email(
            app_data['email'],
            '🎉 Your Dealer Application is Approved! - IntelliWheels',
            f'''
            <h2>Congratulations, {app_data['name']}!</h2>
            <p>Your dealer application has been <strong style="color: green;">approved</strong>!</p>
            <p>You can now log in to IntelliWheels and start listing your vehicles.</p>
            {f'<p><strong>Admin Notes:</strong> {admin_notes}</p>' if admin_notes else ''}
            <hr>
            <p>Welcome to IntelliWheels!</p>
            '''
        )
        
        return jsonify({'success': True, 'message': 'Application approved successfully'})
    except Exception as e:
        print('[dealers] Operation failed')
        try:
            db.rollback()
        except:
            pass
        return jsonify({'success': False, 'error': 'Failed to approve application'}), 500

@bp.route('/applications/<int:id>/reject', methods=['PUT'])
@rate_limit(max_requests=20, window_seconds=60)
@token_required
def reject_application(id):
    """Reject a dealer application (admin only)"""
    current_user = g.current_user
    if not current_user.get('is_admin'):
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    data = request.get_json() or {}
    admin_notes = data.get('notes', '')
    reason = data.get('reason', 'Your application did not meet our requirements at this time.')
    
    db = get_db()
    try:
        if is_postgres():
            app_row = db.execute('SELECT * FROM dealer_applications WHERE id = %s', (id,)).fetchone()
        else:
            app_row = db.execute('SELECT * FROM dealer_applications WHERE id = ?', (id,)).fetchone()
        
        if not app_row:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        
        app_data = dict(app_row)
        
        if app_data['status'] != 'pending':
            return jsonify({'success': False, 'error': 'Application already processed'}), 400
        
        # Update application status
        if is_postgres():
            db.execute('''
                UPDATE dealer_applications 
                SET status = %s, admin_notes = %s, reviewed_by = %s, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', ('rejected', admin_notes, current_user['id'], id))
        else:
            db.execute('''
                UPDATE dealer_applications 
                SET status = ?, admin_notes = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', ('rejected', admin_notes, current_user['id'], id))
        
        db.commit()
        
        # Send rejection email
        send_email(
            app_data['email'],
            'Dealer Application Update - IntelliWheels',
            f'''
            <h2>Dear {app_data['name']},</h2>
            <p>Thank you for your interest in becoming a dealer on IntelliWheels.</p>
            <p>After careful review, we regret to inform you that your application has not been approved at this time.</p>
            <p><strong>Reason:</strong> {reason}</p>
            <p>You are welcome to reapply after addressing the concerns mentioned above.</p>
            <hr>
            <p>Best regards,<br>The IntelliWheels Team</p>
            '''
        )
        
        return jsonify({'success': True, 'message': 'Application rejected'})
    except Exception as e:
        print('[dealers] Operation failed')
        try:
            db.rollback()
        except:
            pass
        return jsonify({'success': False, 'error': 'Failed to reject application'}), 500
