from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from chatbot import PlacementChatbot
import logging
from pathlib import Path
import os
from werkzeug.utils import secure_filename
import base64
from dotenv import load_dotenv
import tempfile

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload directory
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

# Initialize Gemini
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("✓ Gemini API configured")
    else:
        logger.warning("⚠️ GEMINI_API_KEY not set")
except ImportError:
    logger.warning("⚠️ google-generativeai not installed")
except Exception as e:
    logger.warning(f"⚠️ Gemini initialization failed: {e}")

# Global chatbot instance
chatbot = None

def initialize_chatbot():
    """Initialize chatbot with error handling"""
    global chatbot
    try:
        logger.info("🚀 Initializing Placement Chatbot...")
        chatbot = PlacementChatbot()
        logger.info("✓ Chatbot initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize chatbot: {e}")
        return False

# Initialize chatbot on startup
with app.app_context():
    chatbot_ready = initialize_chatbot()

# ==================== UTILITY FUNCTIONS ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    """Determine file type"""
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
        return 'image'
    elif ext == 'pdf':
        return 'pdf'
    elif ext == 'txt':
        return 'text'
    return 'unknown'

# ==================== GEMINI FILE ANALYSIS ====================

def analyze_image_with_gemini(filepath, question):
    """Analyze image with Gemini Vision API"""
    if not GEMINI_AVAILABLE:
        return "Gemini API not configured. Install: pip install google-generativeai"
    
    try:
        with open(filepath, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')
        
        prompt = f"""You are an expert interview prep assistant for placement interviews.

User's question/request: {question if question else "Explain what you see in this image and how it relates to interviews"}

Please provide:
1. **Summary**: What's in the image
2. **Key Concepts**: Important points
3. **Interview Relevance**: How this relates to placement interviews
4. **Practice Questions**: 3 questions based on this
5. **Study Tips**: How to master these concepts

Be clear, concise, and practical for interview prep."""
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content([
            {
                "type": "image",
                "data": image_data,
            },
            {
                "type": "text",
                "text": prompt
            }
        ])
        
        logger.info("✓ Image analysis completed with Gemini")
        return response.text
    
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        return f"Analysis failed: {str(e)}"

def analyze_pdf_with_gemini(filepath, question):
    """Extract and analyze PDF with Gemini"""
    if not GEMINI_AVAILABLE:
        return "Gemini API not configured. Install: pip install google-generativeai"
    
    try:
        try:
            import PyPDF2
        except ImportError:
            return "PyPDF2 not installed. Install with: pip install PyPDF2"
        
        # Extract text from PDF
        text = ""
        with open(filepath, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = min(len(pdf_reader.pages), 10)  # First 10 pages
            for i in range(num_pages):
                text += pdf_reader.pages[i].extract_text()
        
        if not text.strip():
            return "Could not extract text from PDF. Try converting to text first."
        
        # Analyze with Gemini
        return analyze_text_with_gemini(text, question)
    
    except Exception as e:
        logger.error(f"PDF analysis failed: {e}")
        return f"PDF analysis failed: {str(e)}"

def analyze_text_with_gemini(text, question):
    """Analyze text content with Gemini"""
    if not GEMINI_AVAILABLE:
        return "Gemini API not configured. Install: pip install google-generativeai"
    
    try:
        # Limit text size
        text = text[:8000]
        
        prompt = f"""You are an expert interview prep assistant for placement interviews.

Study material provided:
---
{text}
---

User's question/request: {question if question else "Summarize this material and create practice questions"}

Please provide:
1. **Summary**: Key points (2-3 lines)
2. **Main Concepts**: Top 5 topics
3. **Interview Relevance**: How this helps with placements
4. **Practice Questions**: 5 questions with brief answers
5. **Study Focus**: What to prioritize
6. **Next Steps**: What to practice

Be clear, practical, and focused on interview preparation."""
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        logger.info("✓ Text analysis completed with Gemini")
        return response.text
    
    except Exception as e:
        logger.error(f"Text analysis failed: {e}")
        return f"Analysis failed: {str(e)}"

def analyze_file_with_gemini(filepath, content_type, question):
    """Route to appropriate analysis function"""
    try:
        if content_type.startswith('image/'):
            return analyze_image_with_gemini(filepath, question)
        elif content_type == 'application/pdf':
            return analyze_pdf_with_gemini(filepath, question)
        elif content_type == 'text/plain':
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            return analyze_text_with_gemini(text, question)
        else:
            return "File type not supported for analysis"
    except Exception as e:
        return f"Analysis error: {str(e)}"

# ==================== STATIC FILE ROUTES ====================

@app.route('/')
def index():
    """Serve the main UI"""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return serve_fallback_ui()

def serve_fallback_ui():
    """Fallback UI if index.html is not found"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JIMS Placement Chatbot</title>
        <style>
            body { font-family: Arial; background: #667eea; margin: 0; }
            .container { background: white; border-radius: 10px; max-width: 600px; margin: 20px auto; padding: 20px; }
            h1 { color: #667eea; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>JIMS Placement Chatbot</h1>
            <p>Chatbot is running! Use the API endpoints to interact.</p>
            <p>API URL: <code>http://localhost:5000/query</code></p>
        </div>
    </body>
    </html>
    """
    return html

# ==================== API ROUTES ====================

@app.route('/api/health', methods=['GET'])
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok" if chatbot_ready else "error",
        "chatbot": "initialized" if chatbot and chatbot_ready else "not_initialized",
        "gemini_available": GEMINI_AVAILABLE,
        "message": "Placement Chatbot API is running"
    }), 200 if chatbot_ready else 503

@app.route('/api/status', methods=['GET'])
def status():
    """Get API status and capabilities"""
    return jsonify({
        "status": "online",
        "api_version": "2.0",
        "features": {
            "placement_queries": True,
            "file_upload": True,
            "gemini_analysis": GEMINI_AVAILABLE,
            "batch_queries": True
        },
        "endpoints": {
            "GET /": "Web UI",
            "POST /query": "Query chatbot",
            "POST /batch": "Batch queries",
            "POST /upload-file": "Upload and analyze file",
            "POST /interview-prep": "Get interview prep from files",
            "GET /health": "Health check",
            "GET /api/status": "Status info"
        },
        "chatbot_ready": chatbot_ready
    }), 200

@app.route('/api/query', methods=['POST'])
@app.route('/query', methods=['POST'])
def query():
    """
    Query the chatbot
    
    Request JSON:
    {
        "question": "What is TCS CGPA requirement?"
    }
    """
    
    if not chatbot_ready or not chatbot:
        return jsonify({
            "error": "Chatbot not initialized",
            "message": "Run: python knowledge_base_builder.py --default",
            "success": False
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON", "success": False}), 400
        
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "Question cannot be empty", "success": False}), 400
        
        logger.info(f"📝 Query: {question}")
        result = chatbot.query(question)
        result['success'] = True
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/batch', methods=['POST'])
@app.route('/batch', methods=['POST'])
def batch_query():
    """Process multiple queries at once"""
    
    if not chatbot_ready or not chatbot:
        return jsonify({
            "error": "Chatbot not initialized",
            "success": False
        }), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON", "success": False}), 400
        
        questions = data.get('questions', [])
        
        if not questions or not isinstance(questions, list):
            return jsonify({
                "error": "Questions must be a list",
                "success": False
            }), 400
        
        results = []
        for question in questions:
            logger.info(f"📝 Batch Query: {question}")
            result = chatbot.query(question)
            result['success'] = True
            results.append(result)
        
        return jsonify({
            "results": results,
            "count": len(results),
            "success": True
        }), 200
    
    except Exception as e:
        logger.error(f"Error in batch processing: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/upload-file', methods=['POST'])
@app.route('/upload-file', methods=['POST'])
def upload_file():
    """
    Upload and analyze file with Gemini API
    
    Request: multipart/form-data
    - file: uploaded file
    - question: (optional) what to analyze
    """
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided", "success": False}), 400
    
    file = request.files['file']
    question = request.form.get('question', '')
    
    if file.filename == '':
        return jsonify({"error": "No file selected", "success": False}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            "success": False
        }), 400
    
    try:
        # Use temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = secure_filename(file.filename)
            filepath = os.path.join(tmpdir, filename)
            file.save(filepath)
            
            logger.info(f"📤 File uploaded: {filename}")
            
            # Analyze with Gemini
            analysis = analyze_file_with_gemini(filepath, file.content_type, question)
            
            return jsonify({
                "success": True,
                "filename": filename,
                "file_type": get_file_type(filename),
                "analysis": analysis,
                "source": "Gemini 2.0 Flash API"
            }), 200
    
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/interview-prep', methods=['POST'])
def interview_prep():
    """
    Generate comprehensive interview prep using uploaded files
    
    Request: multipart/form-data
    - files: multiple files
    - prep_type: 'technical', 'hr', 'full'
    """
    
    if 'files' not in request.files or len(request.files.getlist('files')) == 0:
        return jsonify({"error": "No files provided", "success": False}), 400
    
    if not GEMINI_AVAILABLE:
        return jsonify({
            "error": "Gemini API not configured",
            "success": False
        }), 503
    
    try:
        files = request.files.getlist('files')
        prep_type = request.form.get('type', 'full')
        
        combined_analysis = ""
        
        # Analyze all files
        with tempfile.TemporaryDirectory() as tmpdir:
            for file in files:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(tmpdir, filename)
                    file.save(filepath)
                    
                    analysis = analyze_file_with_gemini(filepath, file.content_type, "")
                    combined_analysis += f"\n\n--- {filename} ---\n{analysis}"
            
            # Generate comprehensive prep plan
            prep_prompt = f"""Based on these study materials, create a comprehensive {prep_type} interview preparation plan.

Materials analyzed:
{combined_analysis[:5000]}

Provide (in markdown format):
1. **Key Topics to Master** - Top 5-7 topics
2. **Common Questions** - 10 likely interview questions
3. **Study Schedule** - 4-week preparation timeline
4. **Daily Practice Tasks** - What to practice each day
5. **Mock Interview Tips** - How to prepare
6. **Common Mistakes** - What to avoid
7. **Resources** - Where to practice (LeetCode, HackerRank, etc)
8. **Success Probability** - Estimated chances

Be specific and actionable. Focus on {prep_type} interview preparation."""
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prep_prompt)
            
            logger.info("✓ Interview prep plan generated")
            
            return jsonify({
                "success": True,
                "prep_type": prep_type,
                "files_analyzed": len(files),
                "prep_plan": response.text,
                "source": "Gemini 2.0 Flash API"
            }), 200
    
    except Exception as e:
        logger.error(f"Interview prep error: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/test-queries', methods=['GET'])
def test_queries():
    """Get sample test queries"""
    return jsonify({
        "sample_queries": [
            "What is TCS CGPA requirement?",
            "Which companies visit JIMS?",
            "What is the average CTC?",
            "Tell me about Infosys placement",
            "How many rounds in selection process?",
            "What is the stipend for internship?",
            "What are the placement statistics?"
        ],
        "success": True
    }), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "path": request.path,
        "success": False
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "success": False
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "success": False
    }), 405

# ==================== STARTUP MESSAGE ====================

def print_startup_info():
    """Print startup information"""
    print("\n" + "="*70)
    print("🚀 PLACEMENT CHATBOT API - STARTUP (v2.0 with File Upload)")
    print("="*70)
    print("\n📍 Server Status:")
    print(f"   Status: {'✅ READY' if chatbot_ready else '❌ NOT READY'}")
    print(f"   Chatbot: {'✅ Initialized' if chatbot else '❌ Not Initialized'}")
    print(f"   Gemini API: {'✅ Available' if GEMINI_AVAILABLE else '⚠️  Not Configured'}")
    print("\n🌐 Access Points:")
    print("   Web UI:        http://localhost:5000/")
    print("   API Base:      http://localhost:5000/api")
    print("   Health Check:  http://localhost:5000/health")
    print("\n📚 Main Endpoints:")
    print("   POST /query         - Chat about placements")
    print("   POST /batch         - Multiple queries")
    print("   POST /upload-file   - Analyze files with Gemini")
    print("   POST /interview-prep - Generate prep plans")
    print("\n💡 File Upload Features:")
    print("   ✓ Images (PNG, JPG, GIF)")
    print("   ✓ PDFs")
    print("   ✓ Text files")
    print("   ✓ Gemini Vision API integration")
    print("\n📤 File Upload Examples:")
    print("   curl -X POST http://localhost:5000/upload-file \\")
    print("     -F 'file=@notes.txt' \\")
    print("     -F 'question=Summarize this'")
    print("\n⚠️  If features not working:")
    print("   Run: python knowledge_base_builder.py --default")
    print("   Set: GEMINI_API_KEY in .env file")
    print("="*70 + "\n")

if __name__ == '__main__':
    print_startup_info()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
