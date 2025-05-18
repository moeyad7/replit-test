import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import time

# Import our custom modules
from loyalty_agent import LoyaltyAgent

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],  # Vite dev server
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize our LoyaltyAgent
loyalty_agent = LoyaltyAgent()

@app.route('/api/chat/session', methods=['POST'])
def create_chat_session():
    """Create a new chat session"""
    try:
        session_id = loyalty_agent.create_chat_session()
        return jsonify({'session_id': session_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        history = loyalty_agent.get_chat_history(session_id)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history/<session_id>', methods=['DELETE'])
def clear_chat_history(session_id):
    """Clear chat history for a session"""
    try:
        loyalty_agent.clear_chat_history(session_id)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    """
    Process a natural language query about loyalty program data
    """
    data = request.json
    
    if not data or 'question' not in data:
        return jsonify({'error': 'Question is required'}), 400
    
    query = data['question']
    session_id = data.get('session_id')  # Optional session ID
    
    print(f"Processing question: {query}")
    if session_id:
        print(f"Using chat session: {session_id}")
    
    try:
        # Start timing
        start_time = time.time()
        
        # Process the query using our LangChain agent
        result = loyalty_agent.process_question(query, session_id)
        
        # End timing
        elapsed_time = time.time() - start_time
        print(f"Query processed in {elapsed_time:.2f} seconds")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return jsonify({
            'error': f'Error processing query: {str(e)}',
            'queryUnderstanding': "There was an error understanding your question.",
            'sqlQuery': "",
            'databaseResults': {
                'count': 0,
                'time': 0
            },
            'title': "Error Processing Query",
            'data': [],
            'insights': [
                {
                    'id': 1,
                    'text': f"Error: {str(e)}"
                }
            ],
            'recommendations': [
                {
                    'id': 1,
                    'title': "Try Again",
                    'description': "Please try rephrasing your question or ask something else.",
                    'type': "other"
                }
            ]
        }), 500

@app.route('/api/schema', methods=['GET'])
def get_schema():
    """
    Get the database schema information
    """
    try:
        schema = loyalty_agent.get_schema()
        return jsonify({'schema': schema})
    
    except Exception as e:
        print(f"Error fetching schema: {str(e)}")
        return jsonify({
            'error': f'Error fetching schema: {str(e)}'
        }), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

# Serve the frontend from the Flask app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # Serve static files if we're in production
    if os.environ.get('FLASK_ENV') == 'production':
        if path and Path(f"../client/dist/{path}").exists():
            return app.send_static_file(path)
        return app.send_static_file('index.html')
    
    # In development, we'll proxy to the Vite server from the JavaScript layer
    return jsonify({
        'error': 'Not found. In development, frontend is served by Vite.'
    }), 404

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Print configuration info
    print(f"API URL configured: {os.environ.get('DATABASE_API_URL', 'Not configured')}")
    if os.environ.get('DATABASE_API_KEY'):
        print("API Key configured: Yes (key provided)")
    else:
        print("API Key not configured")
    print(f"SQL dialect configured: {os.environ.get('SQL_DIALECT', 'redshift')}")
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')