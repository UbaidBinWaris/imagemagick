import os
import subprocess
import logging
import uuid
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Flask and Application Configuration ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# File and Upload Configuration
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

# --- Flask Routes ---
@app.route('/')
def index():
    """Serve the HTML frontend from templates."""
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

if __name__ == "__main__":
    print("✅ App syntax test passed!")
    print("🚀 Basic Flask app is working!")
