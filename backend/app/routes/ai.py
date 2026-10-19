from flask import Blueprint, request, jsonify
from ..services.ai_service import ai_service
from ..security import sanitize_string, validate_text_field, require_auth, rate_limit

bp = Blueprint('ai', __name__, url_prefix='/api')


@bp.route('/chatbot', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def chatbot():
    # Optional auth check - chatbot can work for guests too
    user = require_auth()
    
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400
    
    query = sanitize_string(data.get('query') or data.get('message') or '')
    image_base64 = data.get('image_base64')
    
    # Require either a message or an image
    if not query and not image_base64:
        return jsonify({'success': False, 'error': 'Please provide a message or image'}), 400
    
    # Validate query length if provided
    if query:
        valid, error = validate_text_field(query, 'Message', required=False, max_length=4000)
        if not valid:
            return jsonify({'success': False, 'error': error}), 400
    
    history = data.get('history', [])
    # Limit history to prevent abuse
    if isinstance(history, list):
        history = history[-20:]  # Keep only last 20 messages
    else:
        history = []
    
    # Basic validation for base64 image
    if image_base64 and len(image_base64) > 10 * 1024 * 1024:  # 10MB limit
        return jsonify({'success': False, 'error': 'Image too large'}), 400
    
    result = ai_service.chat(query, history, image_base64)
    
    if isinstance(result, dict):
        return jsonify({
            'success': True, 
            'response': result.get('text', ''),
            'listing_data': result.get('listing_data'),
            'action_type': 'create_listing' if result.get('listing_data') else None
        })
    
    return jsonify({'success': True, 'response': result})

@bp.route('/price-estimate', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def price_estimate():
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400
    
    make = sanitize_string(data.get('make', ''))[:50]
    model = sanitize_string(data.get('model', ''))[:100]
    year = data.get('year')
    specs = data.get('specs', {})
    currency = sanitize_string(data.get('currency', 'JOD'))[:10]
    
    if not make or not model:
        return jsonify({'success': False, 'error': 'Make and model are required'}), 400
    
    result = ai_service.estimate_price(make, model, year, specs, currency)
    return jsonify({
        'success': True,
        'estimate': result['value'],
        'currency': result['currency'],
        'range': {
            'low': result['low'],
            'high': result['high']
        }
    })

@bp.route('/semantic-search', methods=['GET'])
@rate_limit(max_requests=30, window_seconds=60)
def semantic_search():
    query = sanitize_string(request.args.get('q', ''))[:500]
    if not query:
        return jsonify({'success': False, 'error': 'Query is required'}), 400
    
    try:
        limit = min(int(request.args.get('limit', 6)), 20)  # Max 20 results
    except ValueError:
        limit = 6
    
    results = ai_service.semantic_search(query, limit)
    return jsonify({'success': True, 'results': results})

@bp.route('/vision-helper', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60)
def vision_helper():
    user = require_auth()
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json(silent=True)
    image_base64 = data.get('image_base64')
    
    if not image_base64:
        return jsonify({'success': False, 'error': 'Image is required'}), 400
    
    if len(image_base64) > 10 * 1024 * 1024:  # 10MB limit
        return jsonify({'success': False, 'error': 'Image too large'}), 400
    
    attributes = ai_service.analyze_image(image_base64)
    
    # Add helpful highlights with price info
    highlights = []
    if attributes.get('make') and attributes.get('model'):
        highlights.append(f"Detected: {attributes['make']} {attributes['model']}")
    if attributes.get('year'):
        highlights.append(f"Year: {attributes['year']}")
    if attributes.get('bodyStyle'):
        highlights.append(f"Body: {attributes['bodyStyle']}")
    if attributes.get('estimatedPrice'):
        currency = attributes.get('currency', 'JOD')
        price = attributes['estimatedPrice']
        highlights.append(f"Est. price: {price:,.0f} {currency}")
    if attributes.get('conditionDescription'):
        highlights.append(f"Condition: {attributes['conditionDescription'][:100]}")
    
    attributes['highlights'] = highlights
    
    return jsonify({'success': True, 'attributes': attributes})

@bp.route('/listing-assistant', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def listing_assistant():
    user = require_auth()
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json(silent=True)
    query = sanitize_string(data.get('query', ''))
    
    valid, error = validate_text_field(query, 'Query', required=True, max_length=2000)
    if not valid:
        return jsonify({'success': False, 'error': error}), 400
    
    history = data.get('history', [])
    if isinstance(history, list):
        history = history[-20:]
    else:
        history = []
    
    response = ai_service.listing_assistant(query, history)
    return jsonify(response)

@bp.route('/analytics/insights', methods=['GET'])
@rate_limit(max_requests=10, window_seconds=60)
def analytics_insights():
    # Return mock/aggregated insights for now
    insights = {
        'summary': {
            'currency': 'JOD',
            'average_price': 25000,
            'min_price': 5000,
            'max_price': 150000,
            'total_listings': 42,
            'favorites_count': 12
        },
        'market_top_makes': [
            {'make': 'Toyota', 'avg_price': 22000, 'listings': 15},
            {'make': 'BMW', 'avg_price': 45000, 'listings': 8},
            {'make': 'Mercedes', 'avg_price': 52000, 'listings': 6}
        ],
        'price_distribution': [
            {'bucket': '< 10k', 'count': 5},
            {'bucket': '10k-30k', 'count': 20},
            {'bucket': '30k-60k', 'count': 10},
            {'bucket': '> 60k', 'count': 7}
        ],
        'growth_trends': [
            {'label': 'Jan', 'value': 10},
            {'label': 'Feb', 'value': 15},
            {'label': 'Mar', 'value': 25},
            {'label': 'Apr', 'value': 42}
        ],
        'watchlist': []
    }
    return jsonify({'success': True, 'insights': insights})
