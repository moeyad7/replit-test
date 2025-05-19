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
        # Return the mock response
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