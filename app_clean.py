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
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
DEFAULT_IMAGES_FOLDER = "src/default-image"
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

def get_default_images():
    """Get list of available default images"""
    try:
        if not os.path.exists(DEFAULT_IMAGES_FOLDER):
            return []
        
        images = []
        for filename in os.listdir(DEFAULT_IMAGES_FOLDER):
            if allowed_file(filename):
                images.append(filename)
        return sorted(images)
    except Exception as e:
        logger.error(f"Error getting default images: {e}")
        return []

# --- Flask Routes ---
@app.route('/')
def index():
    """Serve the HTML frontend from template."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    imagemagick_installed, magick_cmd = check_imagemagick()
    return jsonify({
        'status': 'healthy',
        'imagemagick_installed': imagemagick_installed,
        'magick_command': magick_cmd,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/default-images', methods=['GET'])
def get_default_images_list():
    """Get list of available default images."""
    try:
        images = get_default_images()
        return jsonify({
            'success': True,
            'images': images,
            'count': len(images)
        })
    except Exception as e:
        logger.error(f"Error getting default images list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/default-images/<filename>', methods=['GET'])
def serve_default_image(filename):
    """Serve a default image file."""
    try:
        if not allowed_file(filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        image_path = os.path.join(DEFAULT_IMAGES_FOLDER, filename)
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image not found'}), 404
        
        return send_file(image_path, mimetype=f'image/{filename.rsplit(".", 1)[1].lower()}')
    except Exception as e:
        logger.error(f"Error serving default image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_image():
    """Process uploaded image with selected action."""
    try:
        # Check if ImageMagick is installed
        imagemagick_installed, magick_cmd = check_imagemagick()
        if not imagemagick_installed:
            return jsonify({'error': 'ImageMagick is not installed or not in PATH. Please install ImageMagick first.'}), 500

        # Validate file upload
        if 'image' not in request.files:
            return jsonify({'error': 'No image file uploaded'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Get parameters
        action = request.form.get('action', '').lower()
        text = request.form.get('text', '')
        
        # Get custom parameters
        resize_percentage = request.form.get('resize_percentage', '50')
        rotation_angle = request.form.get('rotation_angle', '90')
        text_size = request.form.get('text_size', '120')
        text_color = request.form.get('text_color', 'black')
        text_font = request.form.get('text_font', 'Arial')
        text_position = request.form.get('text_position', 'Center')
        blur_radius = request.form.get('blur_radius', '0x1')

        # Generate unique filename for temporary storage
        unique_id = str(uuid.uuid4())
        original_ext = file.filename.rsplit('.', 1)[1].lower()
        input_filename = f"{unique_id}.{original_ext}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        
        # Output filename will have the same extension
        output_filename = f"output_{unique_id}.{original_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Save uploaded file
        file.save(input_path)
        logger.info(f"File saved: {input_path}")

        # Build ImageMagick command based on action
        cmd = [magick_cmd, input_path]
        
        if action == "resize":
            cmd.extend(["-resize", f"{resize_percentage}%"])
        elif action == "grayscale":
            cmd.extend(["-colorspace", "Gray"])
        elif action == "rotate":
            cmd.extend(["-rotate", rotation_angle])
        elif action == "text":
            if not text:
                return jsonify({'error': 'Text parameter is required for text action'}), 400
            cmd.extend([
                "-gravity", text_position,
                "-font", text_font,
                "-pointsize", text_size,
                "-fill", text_color,
                "-annotate", "+0+10", text
            ])
        elif action == "blur":
            cmd.extend(["-blur", blur_radius])
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
            return jsonify({'error': f'Invalid action: {action}'}), 400

        cmd.append(output_path)

        # Execute ImageMagick command
        logger.info(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"ImageMagick error: {result.stderr}")
            return jsonify({'error': f'ImageMagick processing failed: {result.stderr}'}), 500

        # Return processed image
        return send_file(output_path, mimetype=f'image/{original_ext}', as_attachment=False)

    except subprocess.CalledProcessError as e:
        logger.error(f"ImageMagick command failed: {e.stderr}")
        return jsonify({'error': f'Image processing failed: {e.stderr}'}), 500
    except subprocess.TimeoutExpired:
        logger.error("ImageMagick command timed out")
        return jsonify({'error': 'Image processing timed out. Please try with a smaller image.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    finally:
        # Clean up files, but check if they exist first
        if 'input_path' in locals() and os.path.exists(input_path):
            try:
                os.remove(input_path)
                logger.info(f"Cleaned up input file: {input_path}")
            except Exception as e:
                logger.warning(f"Could not remove input file {input_path}: {e}")

@app.route('/process-default', methods=['POST'])
def process_default_image():
    """Process a default image with text overlay."""
    try:
        # Check if ImageMagick is installed
        imagemagick_installed, magick_cmd = check_imagemagick()
        if not imagemagick_installed:
            return jsonify({'error': 'ImageMagick is not installed or not in PATH. Please install ImageMagick first.'}), 500

        # Get parameters from JSON request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        default_image = data.get('default_image', '')
        text = data.get('text', '')
        
        # Validate inputs
        if not default_image:
            return jsonify({'error': 'default_image parameter is required'}), 400
        
        if not text:
            return jsonify({'error': 'text parameter is required'}), 400

        # Check if default image exists
        input_path = os.path.join(DEFAULT_IMAGES_FOLDER, default_image)
        if not os.path.exists(input_path):
            return jsonify({'error': f'Default image "{default_image}" not found'}), 404

        if not allowed_file(default_image):
            return jsonify({'error': f'Invalid file type for default image'}), 400

        # Get text customization parameters
        text_size = data.get('text_size', '120')
        text_color = data.get('text_color', 'white')
        text_font = data.get('text_font', 'Arial')
        text_position = data.get('text_position', 'Center')
        
        # Generate unique output filename
        unique_id = str(uuid.uuid4())
        original_ext = default_image.rsplit('.', 1)[1].lower()
        output_filename = f"default_output_{unique_id}.{original_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Build ImageMagick command for text overlay
        cmd = [
            magick_cmd, 
            input_path,
            "-gravity", text_position,
            "-font", text_font,
            "-pointsize", text_size,
            "-fill", text_color,
            "-stroke", "black",
            "-strokewidth", "2",
            "-annotate", "+0+10", text,
            output_path
        ]

        # Execute ImageMagick command
        logger.info(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"ImageMagick error: {result.stderr}")
            return jsonify({'error': f'ImageMagick processing failed: {result.stderr}'}), 500

        # Return processed image
        return send_file(output_path, mimetype=f'image/{original_ext}', as_attachment=False)

    except subprocess.CalledProcessError as e:
        logger.error(f"ImageMagick command failed: {e.stderr}")
        return jsonify({'error': f'Image processing failed: {e.stderr}'}), 500
    except subprocess.TimeoutExpired:
        logger.error("ImageMagick command timed out")
        return jsonify({'error': 'Image processing timed out. Please try with a smaller image.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

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
