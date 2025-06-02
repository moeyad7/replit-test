from flask import Flask, request, jsonify

app = Flask(__name__)

# Counter to track number of requests
request_count = 0

@app.route('/query', methods=['GET'])
def handle_query():
    """
    Handle query requests and return mock data based on the question
    """
    global request_count
    request_count += 1
    
    # Get both SQL query and question from request parameters
    sql_query = request.args.get('sql_query', '')
    question = request.args.get('query', '').lower()
        
    if not sql_query or not question:
        return jsonify({
            'error': 'Both SQL query and question must be provided'
        }), 400
    
    try:
        # Handle different questions
        if "how many points did my customers earn last week" in question:
            return jsonify({
                'total_earned_points': 170618272,
                'status': 'success',
                'sql_query': sql_query
            })
        elif "where did this points come from" in question:
            return jsonify({
                'total_payment_reward_points': 166163746,
                'total_achievement_reward_points': 11208450,
                'total_refunded_points': 0,
                'total_migrated_points': 0,
                'total_manual_accumulated_points': 179350,
                'total_manual_rewarded_points': 6933274,
                'status': 'success',
                'sql_query': sql_query
            })
        else:
            return jsonify({
                'error': 'Question not recognized',
                'query': question,
                'sql_query': sql_query,
                'status': 'error'
            }), 400
            
    except Exception as e:
        return jsonify({
            'error': str(e),
            'query': question,
            'sql_query': sql_query,
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True) 