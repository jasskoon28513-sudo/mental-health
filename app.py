import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google.generativeai.errors import APIError

# --- Configuration and Initialization ---

# Azure App Service will securely provide the API key via Application Settings.
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Hardcoded model name as requested
MODEL_TO_USE = 'gemini-2.5-flash' 

if not API_KEY:
    # Print a warning for the Azure logs if the key is missing
    print("FATAL: GOOGLE_API_KEY environment variable not found. The application cannot start.")

try:
    # Configure and initialize the model only if the API key is present
    if API_KEY:
        genai.configure(api_key=API_KEY)
        # The GenerativeModel instance explicitly uses gemini-2.5-flash
        model = genai.GenerativeModel(MODEL_TO_USE)
    else:
        # Placeholder if configuration failed
        model = None 
except Exception as e:
    # Log configuration errors
    print(f"ERROR: Failed to configure Google Generative AI: {e}")
    model = None

# Initialize Flask app
# The name must be 'app' for Azure/Gunicorn to easily find it.
app = Flask(__name__)

# Configure CORS (use specific origins in production)
CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})

# --- Core LLM Logic ---

def execute_mental_health(query: str):
    """
    Skill: Mental Health Advice - Provides general guidance using the Gemini API and Google Search.
    NOTE: Includes a strong system instruction to ensure responsible, non-clinical advice.
    """
    if not model:
        raise Exception("AI model failed to initialize due to missing or invalid API key.")

    # CRITICAL: Define a strong, safety-focused system prompt for mental health context.
    system_prompt = (
        "You are a supportive, non-clinical mental health guide. You are strictly forbidden from "
        "providing medical diagnoses, treatment plans, or emergency advice. Your task is to "
        "offer empathetic, general guidance, stress reduction techniques, and referrals to "
        "reputable resources based on the user's query. Always end with a disclaimer about "
        "seeking professional help from a qualified healthcare provider."
    )

    # Use Google Search grounding tool for general self-care techniques/resource links
    response = model.generate_content(
        query, 
        system_instruction=system_prompt, 
        tools=[{"google_search": {}}]
    )
    return response.text

# --- Health Check Route ---

@app.route('/check', methods=['GET'])
def check():
    """
    Simple health check route used to confirm the backend server is running and accessible.
    """
    status_code = 200
    if not model:
        # Return 503 if the core dependency (AI model) failed to initialize
        status_code = 503
        message = "backend is running, but AI model failed to initialize."
    else:
        message = "backend is running"

    return jsonify({
        'status': 'ok' if status_code == 200 else 'error', 
        'message': message, 
        'model': MODEL_TO_USE
    }), status_code

# --- Main API Route ---

@app.route('/api/execute', methods=['POST'])
def execute():
    # 1. Input Validation
    if not model:
        return jsonify({'error': 'AI service not initialized. Check API key configuration.'}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid or missing JSON payload.'}), 400

    query = data.get('query')
    # Validate that query is a non-empty string
    if not query or not isinstance(query, str) or not query.strip():
        return jsonify({'error': 'Missing or empty "query" field in the request.'}), 400
    
    # 2. Execution and Specific Error Handling
    try:
        result = execute_mental_health(query)
        
        return jsonify({'success': True, 'result': result})
        
    except APIError as e:
        # Handle specific Gemini API errors
        print(f"Gemini API Error: {e}")
        return jsonify({'error': f'AI Service Unavailable or request error: {e}'}), 503
        
    except Exception as e:
        # Catch all other unexpected errors
        print(f"Internal Server Error: {e}")
        return jsonify({'error': 'An unexpected internal server error occurred.'}), 500
