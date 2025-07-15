import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

# --- API Keys (Only GEMINI_API_KEY is needed now) ---
# Set this as an environment variable for security!
# Example for Windows: set GEMINI_API_KEY=YOUR_GEMINI_KEY_HERE
# Example for Linux/macOS: export GEMINI_API_KEY="YOUR_GEMINI_KEY_HERE"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes, allowing your HTML to fetch from it

# --- Configure Gemini API ---
if GEMINI_API_KEY:
    genai.configure(api_key='AIzaSyCFE6PvN3cfmo9cQAwI1-bRdJsr9c4r4_E')
    GEMINI_MODEL = genai.GenerativeModel('gemini-pro')
    print("Gemini API configured successfully.")
else:
    print("WARNING: GEMINI_API_KEY environment variable not set. Gemini API will not work.")
    GEMINI_MODEL = None

# --- Helper function for Gemini query ---
def query_gemini(prompt):
    if not GEMINI_MODEL:
        return "Gemini API not configured.", False
    try:
        response = GEMINI_MODEL.generate_content(prompt)
        # Check if response.candidates is empty or if response.text is not present
        if not response.candidates or not response.text:
            print(f"Gemini returned no text content for prompt: {prompt}")
            return "I'm sorry, Gemini didn't provide a clear response for that.", False
        return response.text, True
    except Exception as e:
        print(f"Error querying Gemini: {e}")
        # More specific error handling for common Gemini errors (e.g., safety, rate limit)
        if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
             feedback = e.response.prompt_feedback
             if feedback.block_reason:
                 return f"My response was blocked due to: {feedback.block_reason}. Please try rephrasing.", False
        return f"I'm sorry, I couldn't get a response from Gemini at this moment due to an error.", False

# --- API Routes ---

@app.route('/api/gemini', methods=['POST'])
def gemini_endpoint():
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    print(f"Received Gemini prompt: '{prompt}'")
    gemini_response, success = query_gemini(prompt)

    if success:
        return jsonify({"response": gemini_response})
    else:
        # For a failed Gemini query, return a 500 Internal Server Error
        # or a 400 Bad Request if the prompt was the issue
        return jsonify({"error": gemini_response}), 500

# Wikipedia lookup can stay if you still want to use the Python 'wikipedia' library
# It does not require an external API key like News or Weather
@app.route('/api/wikipedia', methods=['POST'])
def wikipedia_endpoint():
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        import wikipedia # Ensure wikipedia library is installed (pip install wikipedia)
        results = wikipedia.summary(query, sentences=2)
        return jsonify({"answer": f"According to Wikipedia, {results}"})
    except wikipedia.exceptions.PageError:
        return jsonify({"error": f"Sorry, I couldn't find anything on Wikipedia for '{query}'."}), 404
    except wikipedia.exceptions.DisambiguationError as e:
        # Give some options if there's ambiguity
        options_text = ", ".join(e.options[:5])
        return jsonify({"error": f"Multiple results for '{query}'. Please be more specific. Options include: {options_text}."}), 400
    except Exception as e:
        print(f"Wikipedia lookup error: {e}")
        return jsonify({"error": "An error occurred while searching Wikipedia."}), 500


# Removed /api/news and /api/weather routes from here


# --- Run the Flask App ---
if __name__ == '__main__':
    # You might need to install Flask-CORS and google-generativeai, wikipedia
    # pip install Flask Flask-Cors google-generativeai wikipedia
    app.run(debug=True) # debug=True allows hot-reloading and shows errors