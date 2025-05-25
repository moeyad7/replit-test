import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import time

# Import our custom modules
from loyalty_agent.agent import LoyaltyAgent

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],  # Vite dev server
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize our LoyaltyAgent
print("\n=== Initializing LoyaltyAgent with LangGraph ===")
loyalty_agent = LoyaltyAgent()
print("=== LoyaltyAgent initialized successfully ===\n")

# Default client_id
DEFAULT_CLIENT_ID = 5252

@app.route('/api/chat/session', methods=['POST'])
async def create_chat_session():
    """Create a new chat session"""
    try:
        print("\n--- Creating New Chat Session ---")
        session_id = await loyalty_agent.create_chat_session()
        print(f"✓ Created chat session: {session_id}")
        return jsonify({'session_id': session_id})
    except Exception as e:
        print(f"✗ Error creating chat session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history/<session_id>', methods=['GET'])
async def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        client_id = request.args.get('client_id', DEFAULT_CLIENT_ID)
        print(f"\n--- Getting Chat History ---")
        print(f"Session ID: {session_id}")
        print(f"Client ID: {client_id}")
        history = await loyalty_agent.get_chat_history(session_id, client_id=client_id)
        print(f"✓ Retrieved {len(history)} messages")
        return jsonify({'history': history})
    except Exception as e:
        print(f"✗ Error getting chat history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history/<session_id>', methods=['DELETE'])
async def clear_chat_history(session_id):
    """Clear chat history for a session"""
    try:
        print(f"\n--- Clearing Chat History ---")
        print(f"Session ID: {session_id}")
        await loyalty_agent.clear_chat_history(session_id)
        print("✓ Chat history cleared")
        return jsonify({'status': 'success'})
    except ValueError as e:
        print(f"✗ Session not found: {str(e)}")
        return jsonify({'error': 'Session not found', 'details': str(e)}), 404
    except Exception as e:
        print(f"✗ Error clearing chat history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
async def process_query():
    """
    Process a natural language query about loyalty program data
    """
    data = request.json
    
    if not data or 'question' not in data:
        return jsonify({'error': 'Question is required'}), 400
    
    query = data['question']
    session_id = data.get('session_id')  # Optional session ID
    client_id = data.get('client_id', DEFAULT_CLIENT_ID)
    
    print(f"\n=== Processing Query ===")
    print(f"Question: {query}")
    if session_id:
        print(f"Session ID: {session_id}")
    print(f"Client ID: {client_id}")
    
    try:
        # Start timing
        start_time = time.time()
        
        # Process the query using our LangGraph agent
        print("\nStarting query processing with LangGraph workflow...")
        result = await loyalty_agent.process_question(query, session_id, client_id=client_id)
        
        # End timing
        elapsed_time = time.time() - start_time
        print(f"\n✓ Query processed in {elapsed_time:.2f} seconds")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"\n✗ Error processing query: {str(e)}")
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
async def get_schema():
    """
    Get the database schema information
    """
    try:
        client_id = request.args.get('client_id', DEFAULT_CLIENT_ID)
        print(f"\n--- Getting Schema ---")
        print(f"Client ID: {client_id}")
        schema = await loyalty_agent.get_schema(client_id=client_id)
        print("✓ Schema retrieved successfully")
        return jsonify({'schema': schema})
    
    except Exception as e:
        print(f"✗ Error fetching schema: {str(e)}")
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