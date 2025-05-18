#!/usr/bin/env python3
"""
Starter script for the Python Flask backend with LangChain
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

# Import the Flask app
from app import app

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Set Flask environment
    os.environ["FLASK_ENV"] = os.environ.get("NODE_ENV", "development")
    
    # Run the application
    app.run(
        host="0.0.0.0",
        port=port, 
        debug=os.environ.get("FLASK_ENV") == "development"
    )