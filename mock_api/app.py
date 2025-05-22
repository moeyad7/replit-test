from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/query', methods=['GET'])
def handle_query():
    """
    Handle query requests and return mock data
    """
    # Get the query from request parameters
    query = request.args.get('query', '')
        
    if not query:
        return jsonify({
            'error': 'No query provided'
        }), 400
    
    try:
        # Check if this is the points query
        if 'SUM(payment_reward_points)' in query and 'gameball_analytics.daily_client_transactions' in query:
            return jsonify({
                'total_earned_points': 177551546,
                'total_payment_reward_points': 166163746,
                'total_achievement_reward_points': 11208450,
                'total_manual_accumulated_points': 179350,
                'total_migrated_points': 0,
                'total_refunded_points': 0,
                'total_partially_refunded_points': 524372,
                'total_burned_points': 56454535,
                'total_cancelled_points': 0,
                'total_redeemed_discount_points': 110473800,
                'status': 'success'
            })
        
        # Default response for other queries
        return jsonify({
            'total_earned_points': 170618272,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'query': query,
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True) 