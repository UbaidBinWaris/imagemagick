"""
Modular ImageMagick Web Application
"""
import os
import subprocess
import logging
import uuid
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

from config import config, Config
from utils import (
    allowed_file, 
    check_imagemagick, 
    build_imagemagick_command, 
    cleanup_files,
    validate_processing_params
)

def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Enable CORS
    CORS(app)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Register routes
    register_routes(app)
    register_error_handlers(app)
    
    return app

def register_routes(app):
    """Register application routes"""
    
    @app.route('/')
    def index():
        """Serve the main HTML page"""
        return render_template('index.html')

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            imagemagick_installed, magick_cmd = check_imagemagick()
            return jsonify({
                'status': 'healthy',
                'imagemagick_installed': imagemagick_installed,
                'magick_command': magick_cmd,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            app.logger.error(f"Health check error: {e}")
            return jsonify({
                'status': 'error',
                'imagemagick_installed': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    @app.route('/process', methods=['POST'])
    def process_image():
        """Process uploaded image with selected action"""
        input_path = None
        
        try:
            # Check ImageMagick installation
            imagemagick_installed, magick_cmd = check_imagemagick()
            if not imagemagick_installed:
                return jsonify({
                    'error': 'ImageMagick is not installed or not in PATH. Please install ImageMagick first.'
                }), 500

            # Validate file upload
            validation_error = validate_file_upload(request)
            if validation_error:
                return validation_error

            file = request.files['image']
            
            # Get and validate processing parameters
            action, params = extract_processing_params(request)
            validate_processing_params(action, params)

            # Process the image
            input_path, output_path = save_and_process_image(
                file, action, params, magick_cmd, app.config
            )

            # Return processed image
            return send_file(output_path, mimetype=f'image/{get_file_extension(file.filename)}', as_attachment=False)

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except subprocess.CalledProcessError as e:
            app.logger.error(f"ImageMagick command failed: {e.stderr}")
            return jsonify({'error': f'Image processing failed: {e.stderr}'}), 500
        except subprocess.TimeoutExpired:
            app.logger.error("ImageMagick command timed out")
            return jsonify({'error': 'Image processing timed out. Please try with a smaller image.'}), 500
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500
        finally:
            # Clean up temporary files
            cleanup_files(input_path)

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(413)
    def too_large(e):
        """Handle file too large error"""
        return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

    @app.errorhandler(500)
    def internal_error(e):
        """Handle internal server errors"""
        app.logger.error(f"Internal server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(404)
    def not_found(e):
        """Handle not found errors"""
        return jsonify({'error': 'Endpoint not found'}), 404

def validate_file_upload(request):
    """Validate file upload"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': f'File type not allowed. Allowed types: {", ".join(Config.ALLOWED_EXTENSIONS)}'
        }), 400
    
    return None

def extract_processing_params(request):
    """Extract processing parameters from request"""
    action = request.form.get('action', '').lower()
    if not action:
        raise ValueError('No action specified')

    params = {}
    for key, default in Config.DEFAULT_PARAMS.items():
        params[key] = request.form.get(key, default)
    
    # Special handling for text parameter
    params['text'] = request.form.get('text', '')
    
    return action, params

def save_and_process_image(file, action, params, magick_cmd, config):
    """Save uploaded file and process it"""
    # Generate unique filenames
    unique_id = str(uuid.uuid4())
    original_ext = get_file_extension(file.filename)
    
    input_filename = f"{unique_id}.{original_ext}"
    input_path = os.path.join(config['UPLOAD_FOLDER'], input_filename)
    
    output_filename = f"output_{unique_id}.{original_ext}"
    output_path = os.path.join(config['OUTPUT_FOLDER'], output_filename)

    # Save uploaded file
    file.save(input_path)
    logging.getLogger(__name__).info(f"File saved: {input_path}")

    # Build and execute ImageMagick command
    cmd = build_imagemagick_command(magick_cmd, input_path, output_path, action, params)
    logging.getLogger(__name__).info(f"Executing command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=Config.IMAGEMAGICK_TIMEOUT)
    
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)

    # Check if output file was created
    if not os.path.exists(output_path):
        raise RuntimeError('Image processing failed: No output file generated')

    return input_path, output_path

def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower()

def print_startup_info(port):
    """Print startup information"""
    print("=" * 60)
    print("🎨 ImageMagick Web Image Processor (Modular)")
    print("=" * 60)
    
    imagemagick_installed, magick_cmd = check_imagemagick()
    if imagemagick_installed:
        print(f"✅ ImageMagick found: {magick_cmd}")
    else:
        print("❌ ImageMagick not found!")
        print("📋 Please install ImageMagick:")
        print("   1. Download from: https://imagemagick.org/script/download.php#windows")
        print("   2. Or use Chocolatey: choco install imagemagick (as admin)")
        print("   3. Restart your terminal after installation")
    
    print(f"🚀 Starting server on http://localhost:{port}")
    print("=" * 60)

# Create the application instance
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    print_startup_info(port)
    
    app.run(host="0.0.0.0", port=port, debug=app.config['DEBUG'])
