import os
import subprocess
import logging
import uuid
import base64
import hashlib
import hmac
import secrets
import time
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from io import BytesIO
from functools import wraps
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Flask and Application Configuration ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Security Configuration from environment variables
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
API_KEY = os.getenv('API_KEY', 'ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M')
JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_hex(32))
app.config['SECRET_KEY'] = SECRET_KEY

# Rate limiting
try:
    # Try to use Redis for rate limiting if available
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour", "10 per minute"],
        storage_uri=redis_url
    )
except ImportError:
    # Fall back to in-memory rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour", "10 per minute"]
    )

# File and Upload Configuration
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_imagemagick():
    """Check if ImageMagick is installed"""
    try:
        # Try multiple possible commands for ImageMagick
        commands_to_try = ['magick', 'convert', 'C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe']
        
        for cmd in commands_to_try:
            try:
                result = subprocess.run([cmd, '-version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"ImageMagick found using command: {cmd}")
                    return True, cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return False, None
    except Exception as e:
        logger.error(f"Error checking ImageMagick: {e}")
        return False, None

# --- Security Helper Functions ---
def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
        
        # Check for API key in query parameters (less secure, but useful for some integrations)
        if not api_key:
            api_key = request.args.get('api_key')
        
        # Remove 'Bearer ' prefix if present
        if api_key and api_key.startswith('Bearer '):
            api_key = api_key[7:]
        
        if not api_key or api_key != API_KEY:
            logger.warning(f"Unauthorized access attempt from {get_remote_address()}")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Valid API key required',
                'code': 'INVALID_API_KEY'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_input(required_fields=None, optional_fields=None):
    """Decorator to validate input data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if required_fields:
                for field in required_fields:
                    if field not in request.form and field not in request.files:
                        return jsonify({
                            'error': 'Bad Request',
                            'message': f'Required field missing: {field}',
                            'code': 'MISSING_FIELD'
                        }), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_filename(filename):
    """Sanitize filename for security"""
    if not filename:
        return None
    
    # Use werkzeug's secure_filename and add additional checks
    filename = secure_filename(filename)
    
    # Remove any remaining dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    return filename

def generate_jwt_token(payload, expires_in_hours=24):
    """Generate JWT token for session management"""
    payload['exp'] = datetime.utcnow() + timedelta(hours=expires_in_hours)
    payload['iat'] = datetime.utcnow()
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# --- Flask Routes ---
@app.route('/')
def index():
    """Serve the HTML frontend from templates."""
    return render_template('index.html', api_key=API_KEY)

@app.route('/api/health', methods=['GET'])
@limiter.limit("30 per minute")
def health_check():
    """Health check endpoint - no authentication required"""
    imagemagick_installed, magick_cmd = check_imagemagick()
    return jsonify({
        'status': 'healthy',
        'service': 'imagemagick-api',
        'version': '1.0.0',
        'imagemagick_installed': imagemagick_installed,
        'magick_command': magick_cmd,
        'timestamp': datetime.now().isoformat(),
        'rate_limits': {
            'per_day': 200,
            'per_hour': 50,
            'per_minute': 10
        }
    })

@app.route('/api/auth/token', methods=['POST'])
@limiter.limit("5 per minute")
def generate_token():
    """Generate JWT token for session-based authentication (optional)"""
    try:
        data = request.get_json()
        
        # For demo purposes, we'll use a simple username/password
        # In production, integrate with your actual auth system
        username = data.get('username')
        password = data.get('password')
        
        # Simple check - replace with your actual authentication logic
        if username == 'admin' and password == os.getenv('ADMIN_PASSWORD', 'admin123'):
            token = generate_jwt_token({'username': username, 'role': 'admin'})
            return jsonify({
                'success': True,
                'token': token,
                'expires_in': 24 * 3600  # 24 hours in seconds
            })
        else:
            return jsonify({
                'error': 'Invalid credentials',
                'code': 'INVALID_CREDENTIALS'
            }), 401
            
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500

@app.route('/api/process', methods=['POST'])
@limiter.limit("20 per minute")
@require_api_key
@validate_input(required_fields=['image', 'action'])
def process_image_api():
    """Secure API endpoint for image processing - designed for n8n integration"""
    start_time = time.time()
    input_path = None
    output_path = None
    
    try:
        # Check if ImageMagick is installed
        imagemagick_installed, magick_cmd = check_imagemagick()
        if not imagemagick_installed:
            return jsonify({
                'error': 'Service unavailable',
                'message': 'ImageMagick is not installed or not in PATH',
                'code': 'IMAGEMAGICK_NOT_FOUND'
            }), 503

        # Validate file upload
        if 'image' not in request.files:
            return jsonify({
                'error': 'Bad request',
                'message': 'No image file uploaded',
                'code': 'NO_FILE'
            }), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'error': 'Bad request',
                'message': 'No file selected',
                'code': 'EMPTY_FILENAME'
            }), 400

        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        if not safe_filename or not allowed_file(safe_filename):
            return jsonify({
                'error': 'Bad request',
                'message': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}',
                'code': 'INVALID_FILE_TYPE'
            }), 400

        # Get and validate action
        action = request.form.get('action', '').lower().strip()
        valid_actions = ['resize', 'grayscale', 'rotate', 'text', 'blur', 'sharpen', 
                        'sepia', 'negative', 'flip', 'flop']
        
        if action not in valid_actions:
            return jsonify({
                'error': 'Bad request',
                'message': f'Invalid action. Valid actions: {", ".join(valid_actions)}',
                'code': 'INVALID_ACTION'
            }), 400

        # Get and validate parameters with defaults and ranges
        try:
            params = {
                'text': request.form.get('text', '').strip(),
                'resize_percentage': max(1, min(500, int(request.form.get('resize_percentage', '50')))),
                'rotation_angle': max(-360, min(360, int(request.form.get('rotation_angle', '90')))),
                'text_size': max(8, min(500, int(request.form.get('text_size', '120')))),
                'text_color': request.form.get('text_color', 'black').strip(),
                'text_font': request.form.get('text_font', 'Arial').strip(),
                'text_position': request.form.get('text_position', 'Center').strip(),
                'blur_radius': request.form.get('blur_radius', '0x1').strip()
            }
        except ValueError as e:
            return jsonify({
                'error': 'Bad request',
                'message': 'Invalid parameter value',
                'code': 'INVALID_PARAMETER'
            }), 400

        # Validate text for text action
        if action == 'text' and not params['text']:
            return jsonify({
                'error': 'Bad request',
                'message': 'Text parameter is required for text action',
                'code': 'MISSING_TEXT'
            }), 400

        # Generate unique filenames
        unique_id = str(uuid.uuid4())
        original_ext = safe_filename.rsplit('.', 1)[1].lower()
        input_filename = f"{unique_id}_input.{original_ext}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        
        output_filename = f"{unique_id}_output.{original_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Save uploaded file
        file.save(input_path)
        logger.info(f"File saved: {input_path} for action: {action}")

        # Build ImageMagick command
        cmd = [magick_cmd, input_path]
        
        # Add action-specific parameters
        if action == "resize":
            cmd.extend(["-resize", f"{params['resize_percentage']}%"])
        elif action == "grayscale":
            cmd.extend(["-colorspace", "Gray"])
        elif action == "rotate":
            cmd.extend(["-rotate", str(params['rotation_angle'])])
        elif action == "text":
            cmd.extend([
                "-gravity", params['text_position'],
                "-font", params['text_font'],
                "-pointsize", str(params['text_size']),
                "-fill", params['text_color'],
                "-annotate", "+0+10", params['text']
            ])
        elif action == "blur":
            cmd.extend(["-blur", params['blur_radius']])
        elif action == "sharpen":
            cmd.extend(["-sharpen", "0x1"])
        elif action == "sepia":
            cmd.extend(["-sepia-tone", "80%"])
        elif action == "negative":
            cmd.extend(["-negate"])
        elif action == "flip":
            cmd.extend(["-flip"])
        elif action == "flop":
            cmd.extend(["-flop"])

        cmd.append(output_path)

        # Execute ImageMagick command with timeout
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        
        if result.returncode != 0:
            logger.error(f"ImageMagick error: {result.stderr}")
            return jsonify({
                'error': 'Processing failed',
                'message': 'Image processing failed',
                'code': 'PROCESSING_ERROR'
            }), 500

        # Check if output file was created and get file info
        if not os.path.exists(output_path):
            return jsonify({
                'error': 'Processing failed',
                'message': 'Output file was not created',
                'code': 'NO_OUTPUT'
            }), 500

        # Get file size and processing time
        output_size = os.path.getsize(output_path)
        processing_time = round(time.time() - start_time, 3)

        # Read and encode the image as base64 for API response
        with open(output_path, 'rb') as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')

        # Return successful response with metadata
        response_data = {
            'success': True,
            'message': 'Image processed successfully',
            'data': {
                'image': img_base64,
                'format': original_ext,
                'size_bytes': output_size,
                'processing_time_seconds': processing_time,
                'action': action,
                'parameters': params,
                'timestamp': datetime.now().isoformat()
            },
            'metadata': {
                'request_id': unique_id,
                'content_type': f'image/{original_ext}',
                'filename': f"processed_{unique_id}.{original_ext}"
            }
        }

        logger.info(f"Image processed successfully: {unique_id}, action: {action}, time: {processing_time}s")
        return jsonify(response_data)

    except subprocess.CalledProcessError as e:
        logger.error(f"ImageMagick command failed: {e.stderr}")
        return jsonify({
            'error': 'Processing failed',
            'message': 'ImageMagick command execution failed',
            'code': 'COMMAND_FAILED'
        }), 500
        
    except subprocess.TimeoutExpired:
        logger.error("ImageMagick command timed out")
        return jsonify({
            'error': 'Processing timeout',
            'message': 'Image processing timed out. Try with a smaller image.',
            'code': 'TIMEOUT'
        }), 408
        
    except Exception as e:
        logger.error(f"Unexpected error in process_image_api: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'code': 'SERVER_ERROR'
        }), 500
        
    finally:
        # Clean up files
        for file_path in [input_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Cleaned up: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not remove {file_path}: {e}")

# Legacy endpoint for backward compatibility
@app.route('/process', methods=['POST'])
@limiter.limit("10 per minute")
def process_image():
    """Legacy process endpoint (less secure, for backward compatibility)"""
    return process_image_api()

@app.route('/api/status', methods=['GET'])
@require_api_key
def api_status():
    """Get API status and usage information"""
    imagemagick_installed, magick_cmd = check_imagemagick()
    
    return jsonify({
        'service': 'ImageMagick API',
        'version': '1.0.0',
        'status': 'operational' if imagemagick_installed else 'degraded',
        'imagemagick': {
            'installed': imagemagick_installed,
            'command': magick_cmd
        },
        'supported_actions': ['resize', 'grayscale', 'rotate', 'text', 'blur', 'sharpen', 'sepia', 'negative', 'flip', 'flop'],
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'limits': {
            'max_file_size_mb': MAX_CONTENT_LENGTH // (1024 * 1024),
            'rate_limit_per_minute': 20,
            'processing_timeout_seconds': 60
        },
        'timestamp': datetime.now().isoformat()
    })

# --- Error Handlers ---
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({
        'error': 'File too large',
        'message': f'Maximum file size is {MAX_CONTENT_LENGTH // (1024 * 1024)}MB',
        'code': 'FILE_TOO_LARGE'
    }), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist',
        'code': 'NOT_FOUND'
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The requested method is not allowed for this endpoint',
        'code': 'METHOD_NOT_ALLOWED'
    }), 405

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'code': 'RATE_LIMIT_EXCEEDED'
    }), 429

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'code': 'INTERNAL_ERROR'
    }), 500

# --- Documentation Endpoint ---
@app.route('/api/docs', methods=['GET'])
def api_documentation():
    """API documentation endpoint"""
    docs = {
        'title': 'ImageMagick Processing API',
        'version': '1.0.0',
        'description': 'Secure API for image processing using ImageMagick, designed for n8n integration',
        'base_url': request.url_root + 'api/',
        'authentication': {
            'type': 'API Key',
            'header': 'X-API-Key',
            'description': 'Include your API key in the X-API-Key header'
        },
        'endpoints': {
            'POST /api/process': {
                'description': 'Process an image with specified action',
                'authentication': 'required',
                'rate_limit': '20 per minute',
                'parameters': {
                    'image': {'type': 'file', 'required': True, 'description': 'Image file to process'},
                    'action': {'type': 'string', 'required': True, 'options': ['resize', 'grayscale', 'rotate', 'text', 'blur', 'sharpen', 'sepia', 'negative', 'flip', 'flop']},
                    'text': {'type': 'string', 'required': False, 'description': 'Text to add (required for text action)'},
                    'resize_percentage': {'type': 'integer', 'default': 50, 'range': '1-500'},
                    'rotation_angle': {'type': 'integer', 'default': 90, 'range': '-360 to 360'},
                    'text_size': {'type': 'integer', 'default': 120, 'range': '8-500'},
                    'text_color': {'type': 'string', 'default': 'black'},
                    'text_font': {'type': 'string', 'default': 'Arial'},
                    'text_position': {'type': 'string', 'default': 'Center'},
                    'blur_radius': {'type': 'string', 'default': '0x1'}
                },
                'response': {
                    'success': 'Returns base64 encoded processed image with metadata',
                    'error': 'Returns error object with code and message'
                }
            },
            'GET /api/health': {
                'description': 'Health check endpoint',
                'authentication': 'not required',
                'rate_limit': '30 per minute'
            },
            'GET /api/status': {
                'description': 'Get API status and configuration',
                'authentication': 'required',
                'rate_limit': 'default'
            }
        },
        'error_codes': {
            'INVALID_API_KEY': 'API key is missing or invalid',
            'MISSING_FIELD': 'Required field is missing',
            'INVALID_FILE_TYPE': 'File type not supported',
            'INVALID_ACTION': 'Action not supported',
            'PROCESSING_ERROR': 'Image processing failed',
            'TIMEOUT': 'Processing timed out',
            'FILE_TOO_LARGE': 'File exceeds size limit',
            'RATE_LIMIT_EXCEEDED': 'Too many requests'
        }
    }
    return jsonify(docs)

if __name__ == "__main__":
    is_production = os.getenv('FLASK_ENV') == 'production'
    port = int(os.getenv('PORT', 5000))
    
    # Print startup information
    print("=" * 80)
    print("🎨 Secure ImageMagick Processing API")
    print("=" * 80)
    
    # Security warnings
    if API_KEY == 'ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M':
        print("✅ Using generated secure API key")
    else:
        print("⚠️  Using custom API key")
    
    if not is_production:
        print("🔧 Running in development mode")
    else:
        print("🚀 Running in production mode")
    
    imagemagick_installed, magick_cmd = check_imagemagick()
    if imagemagick_installed:
        print(f"✅ ImageMagick found: {magick_cmd}")
    else:
        print("❌ ImageMagick not found!")
        print("📋 Please install ImageMagick:")
        print("   1. Download from: https://imagemagick.org/script/download.php#windows")
        print("   2. Or use Chocolatey: choco install imagemagick (as admin)")
        print("   3. Restart your terminal after installation")
    
    print(f"\n📡 API Endpoints:")
    print(f"   Health Check:    http://localhost:{port}/api/health")
    print(f"   Process Images:  http://localhost:{port}/api/process")
    print(f"   API Status:      http://localhost:{port}/api/status")
    print(f"   Documentation:   http://localhost:{port}/api/docs")
    print(f"   Web Interface:   http://localhost:{port}/")
    
    print(f"\n🔐 Security:")
    print(f"   API Key Header:  X-API-Key")
    print(f"   API Key Value:   {API_KEY}")
    print(f"   Rate Limiting:   Enabled")
    print(f"   Input Validation: Enabled")
    
    print(f"\n🔧 n8n Integration:")
    print(f"   Use HTTP Request node")
    print(f"   Method: POST")
    print(f"   URL: http://localhost:{port}/api/process")
    print(f"   Headers: X-API-Key: {API_KEY}")
    print(f"   Body: Form Data with 'image' file and 'action' parameter")
    
    print("=" * 80)
    
    app.run(host="0.0.0.0", port=port, debug=not is_production)
