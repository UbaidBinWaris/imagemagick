import os
import subprocess
import logging
import uuid
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

# --- Flask and Application Configuration ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
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

def build_imagemagick_command(magick_cmd, input_path, output_path, action, params):
    """Build ImageMagick command based on action and parameters"""
    cmd = [magick_cmd, input_path]
    
    if action == "resize":
        cmd.extend(["-resize", f"{params.get('resize_percentage', '50')}%"])
    elif action == "grayscale":
        cmd.extend(["-colorspace", "Gray"])
    elif action == "rotate":
        cmd.extend(["-rotate", params.get('rotation_angle', '90')])
    elif action == "text":
        text = params.get('text', '')
        if not text:
            raise ValueError('Text parameter is required for text action')
        cmd.extend([
            "-gravity", params.get('text_position', 'Center'),
            "-font", params.get('text_font', 'Arial'),
            "-pointsize", params.get('text_size', '120'),
            "-fill", params.get('text_color', 'black'),
            "-annotate", "+0+10", text
        ])
    elif action == "blur":
        cmd.extend(["-blur", params.get('blur_radius', '0x1')])
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
    else:
        raise ValueError(f'Invalid action: {action}')

    cmd.append(output_path)
    return cmd

def cleanup_files(*file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove file {file_path}: {e}")

# --- API Routes ---
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
        logger.error(f"Health check error: {e}")
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
    output_path = None
    
    try:
        # Check if ImageMagick is installed
        imagemagick_installed, magick_cmd = check_imagemagick()
        if not imagemagick_installed:
            return jsonify({
                'error': 'ImageMagick is not installed or not in PATH. Please install ImageMagick first.'
            }), 500

        # Validate file upload
        if 'image' not in request.files:
            return jsonify({'error': 'No image file uploaded'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Get processing parameters
        action = request.form.get('action', '').lower()
        if not action:
            return jsonify({'error': 'No action specified'}), 400

        params = {
            'text': request.form.get('text', ''),
            'resize_percentage': request.form.get('resize_percentage', '50'),
            'rotation_angle': request.form.get('rotation_angle', '90'),
            'text_size': request.form.get('text_size', '120'),
            'text_color': request.form.get('text_color', 'black'),
            'text_font': request.form.get('text_font', 'Arial'),
            'text_position': request.form.get('text_position', 'Center'),
            'blur_radius': request.form.get('blur_radius', '0x1')
        }

        # Generate unique filenames
        unique_id = str(uuid.uuid4())
        original_ext = file.filename.rsplit('.', 1)[1].lower()
        input_filename = f"{unique_id}.{original_ext}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        
        output_filename = f"output_{unique_id}.{original_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Save uploaded file
        file.save(input_path)
        logger.info(f"File saved: {input_path}")

        # Build and execute ImageMagick command
        try:
            cmd = build_imagemagick_command(magick_cmd, input_path, output_path, action, params)
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"ImageMagick error: {result.stderr}")
                return jsonify({'error': f'ImageMagick processing failed: {result.stderr}'}), 500

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except subprocess.CalledProcessError as e:
            logger.error(f"ImageMagick command failed: {e.stderr}")
            return jsonify({'error': f'Image processing failed: {e.stderr}'}), 500
        except subprocess.TimeoutExpired:
            logger.error("ImageMagick command timed out")
            return jsonify({'error': 'Image processing timed out. Please try with a smaller image.'}), 500

        # Check if output file was created
        if not os.path.exists(output_path):
            return jsonify({'error': 'Image processing failed: No output file generated'}), 500

        # Return processed image
        return send_file(output_path, mimetype=f'image/{original_ext}', as_attachment=False)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    
    finally:
        # Clean up temporary files
        cleanup_files(input_path)

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle not found errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

if __name__ == "__main__":
    is_production = os.getenv('FLASK_ENV') == 'production'
    port = int(os.getenv('PORT', 5000))
    
    # Print startup information
    print("=" * 60)
    print("🎨 ImageMagick Web Image Processor")
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
    
    app.run(host="0.0.0.0", port=port, debug=not is_production)
