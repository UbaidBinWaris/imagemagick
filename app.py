import os
import subprocess
import logging
import uuid
import base64
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
from io import BytesIO

# --- Flask and Application Configuration ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
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

# --- HTML Content (All in one place) ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ImageMagick Web Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { background: white; padding: 30px; border-radius: 15px; max-width: 900px; margin: auto; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); position: relative; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #333; margin-bottom: 10px; font-size: 2.5em; font-weight: 300; }
        .header p { color: #666; font-size: 1.1em; }
        .upload-section { background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 25px; border: 2px dashed #dee2e6; text-align: center; transition: all 0.3s ease; }
        .upload-section:hover { border-color: #007bff; background: #f0f7ff; }
        .file-input-wrapper { position: relative; display: inline-block; }
        .file-input { opacity: 0; position: absolute; z-index: -1; }
        .file-input-button { display: inline-block; padding: 12px 24px; background: #007bff; color: white; border-radius: 25px; cursor: pointer; transition: all 0.3s ease; font-weight: 500; }
        .file-input-button:hover { background: #0056b3; transform: translateY(-2px); }
        .controls-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px; }
        .control-group { background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #007bff; }
        .control-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        .control-group select, .control-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; transition: border-color 0.3s ease; }
        .control-group select:focus, .control-group input:focus { outline: none; border-color: #007bff; box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1); }
        .advanced-options { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 10px; padding: 20px; margin-bottom: 25px; }
        .advanced-options h3 { color: #856404; margin-bottom: 15px; display: flex; align-items: center; cursor: pointer; }
        .advanced-options-content { display: none; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .advanced-options.expanded .advanced-options-content { display: grid; }
        .toggle-icon { margin-left: 10px; transition: transform 0.3s ease; }
        .advanced-options.expanded .toggle-icon { transform: rotate(90deg); }
        .button-group { text-align: center; margin-bottom: 30px; }
        .btn { padding: 12px 30px; margin: 5px; border: none; border-radius: 25px; font-size: 16px; font-weight: 500; cursor: pointer; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 1px; }
        .btn-primary { background: linear-gradient(45deg, #007bff, #0056b3); color: white; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 123, 255, 0.4); }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-secondary:hover { background: #545b62; transform: translateY(-2px); }
        .results-section { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .image-container { text-align: center; background: #f8f9fa; border-radius: 10px; padding: 20px; min-height: 200px; }
        .image-container h3 { color: #333; margin-bottom: 15px; font-size: 1.2em; }
        .image-container img { max-width: 100%; max-height: 300px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); transition: transform 0.3s ease; }
        .image-container img:hover { transform: scale(1.05); }
        .status-message { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 12px; border-radius: 6px; margin-bottom: 20px; display: none; }
        .error-message { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 12px; border-radius: 6px; margin-bottom: 20px; display: none; }
        .loading { text-align: center; padding: 20px; }
        .spinner { display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .health-status { position: absolute; top: 20px; right: 20px; padding: 8px 15px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .health-status.healthy { background: #d4edda; color: #155724; }
        .health-status.unhealthy { background: #f8d7da; color: #721c24; }
        .health-status.warning { background: #fff3cd; color: #856404; }
        .install-instructions { background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 10px; padding: 20px; margin-bottom: 25px; display: none; }
        .install-instructions h3 { color: #1565c0; margin-bottom: 15px; }
        .install-instructions ol { margin-left: 20px; }
        .install-instructions li { margin-bottom: 10px; color: #333; }
        .install-instructions code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        @media (max-width: 768px) { .controls-grid, .results-section { grid-template-columns: 1fr; } .container { padding: 20px; margin: 10px; } .header h1 { font-size: 2em; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="health-status" id="healthStatus">Checking...</div>
        <div class="header">
            <h1>🎨 Image Processor</h1>
            <p>Transform your images with powerful ImageMagick processing</p>
        </div>
        <div class="status-message" id="statusMessage"></div>
        <div class="error-message" id="errorMessage"></div>
        
        <div class="install-instructions" id="installInstructions">
            <h3>📋 ImageMagick Installation Required</h3>
            <p>To use this image processor, you need to install ImageMagick first:</p>
            <ol>
                <li>Download ImageMagick from <a href="https://imagemagick.org/script/download.php#windows" target="_blank">https://imagemagick.org/script/download.php#windows</a></li>
                <li>Choose the Windows binary release (e.g., ImageMagick-7.1.1-Q16-HDRI-x64-dll.exe)</li>
                <li>Run the installer with administrator privileges</li>
                <li>Make sure to check "Install development headers and libraries for C and C++" during installation</li>
                <li>Restart your command prompt/PowerShell</li>
                <li>Refresh this page to check if ImageMagick is detected</li>
            </ol>
            <p><strong>Alternative:</strong> If you have Chocolatey installed, run: <code>choco install imagemagick</code> (as administrator)</p>
        </div>
        
        <div class="upload-section">
            <div class="file-input-wrapper">
                <input type="file" id="imageInput" class="file-input" accept="image/*" />
                <label for="imageInput" class="file-input-button">
                    📁 Choose Image File
                </label>
            </div>
            <p style="margin-top: 10px; color: #666;">Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF, WebP (Max: 16MB)</p>
        </div>
        <div class="controls-grid">
            <div class="control-group">
                <label for="action">🔧 Processing Action:</label>
                <select id="action" onchange="toggleAdvancedOptions()">
                    <option value="resize">Resize Image</option>
                    <option value="grayscale">Convert to Grayscale</option>
                    <option value="rotate">Rotate Image</option>
                    <option value="text" selected>Add Text Overlay</option>
                    <option value="blur">Apply Blur Effect</option>
                    <option value="sharpen">Sharpen Image</option>
                    <option value="sepia">Sepia Tone</option>
                    <option value="negative">Negative Effect</option>
                    <option value="flip">Flip Vertically</option>
                    <option value="flop">Flip Horizontally</option>
                </select>
            </div>
            <div class="control-group" id="textGroup" style="display: block;">
                <label for="textInput">✏️ Text to Add:</label>
                <input type="text" id="textInput" placeholder="Enter your text here..." />
            </div>
        </div>
        <div class="advanced-options" id="advancedOptions">
            <h3 onclick="toggleAdvanced()">
                ⚙️ Advanced Options 
                <span class="toggle-icon">▶</span>
            </h3>
            <div class="advanced-options-content">
                <div class="control-group">
                    <label for="resizePercentage">Resize %:</label>
                    <input type="number" id="resizePercentage" value="50" min="1" max="200" />
                </div>
                <div class="control-group">
                    <label for="rotationAngle">Rotation Angle:</label>
                    <input type="number" id="rotationAngle" value="90" min="-360" max="360" />
                </div>
                <div class="control-group">
                    <label for="textSize">Text Size:</label>
                    <input type="number" id="textSize" value="120" min="8" max="200" />
                </div>
                <div class="control-group">
                    <label for="textColor">Text Color:</label>
                    <select id="textColor">
                        <option value="white">White</option>
                        <option value="black" selected>Black</option>
                        <option value="red">Red</option>
                        <option value="blue">Blue</option>
                        <option value="green">Green</option>
                        <option value="yellow">Yellow</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="textFont">Font Family:</label>
                    <select id="textFont">
                        <option value="Arial" selected>Arial</option>
                        <option value="Times-New-Roman">Times New Roman</option>
                        <option value="Helvetica">Helvetica</option>
                        <option value="Georgia">Georgia</option>
                        <option value="Verdana">Verdana</option>
                        <option value="Courier-New">Courier New</option>
                        <option value="Comic-Sans-MS">Comic Sans MS</option>
                        <option value="Impact">Impact</option>
                        <option value="Trebuchet-MS">Trebuchet MS</option>
                        <option value="Palatino">Palatino</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="textPosition">Text Position:</label>
                    <select id="textPosition">
                        <option value="South">Bottom</option>
                        <option value="North">Top</option>
                        <option value="Center" selected>Center</option>
                        <option value="West">Center Left</option>
                        <option value="East">Center Right</option>
                        <option value="SouthEast">Bottom Right</option>
                        <option value="SouthWest">Bottom Left</option>
                        <option value="NorthEast">Top Right</option>
                        <option value="NorthWest">Top Left</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="blurRadius">Blur Radius:</label>
                    <input type="text" id="blurRadius" value="0x1" placeholder="e.g., 0x1, 2x2" />
                </div>
            </div>
        </div>
        <div class="button-group">
            <button class="btn btn-primary" onclick="processImage()" id="processBtn">
                🚀 Process Image
            </button>
            <button class="btn btn-secondary" onclick="resetAll()">
                🔄 Reset All
            </button>
        </div>
        <div id="loadingIndicator" class="loading" style="display: none;">
            <div class="spinner"></div>
            <p>Processing your image...</p>
        </div>
        <div class="results-section">
            <div class="image-container">
                <h3>📷 Original Image</h3>
                <img id="originalImage" src="" alt="Original Image" style="display: none;" />
                <p id="originalPlaceholder" style="color: #999; margin-top: 50px;">Upload an image to get started</p>
            </div>
            <div class="image-container">
                <h3>✨ Processed Image</h3>
                <img id="outputImage" src="" alt="Processed Image" style="display: none;" />
                <p id="processedPlaceholder" style="color: #999; margin-top: 50px;">Processed image will appear here</p>
            </div>
        </div>
    </div>
    <script>
        const BACKEND_URL = window.location.protocol + '//' + window.location.host;

        document.addEventListener('DOMContentLoaded', function() {
            checkHealth();
            setupEventListeners();
        });

        function setupEventListeners() {
            document.getElementById('imageInput').addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    displayOriginalImage(e.target.files[0]);
                }
            });
        }

        function checkHealth() {
            fetch(`${BACKEND_URL}/health`)
                .then(response => response.json())
                .then(data => {
                    const healthStatus = document.getElementById('healthStatus');
                    const installInstructions = document.getElementById('installInstructions');
                    const processBtn = document.getElementById('processBtn');
                    
                    if (data.status === 'healthy' && data.imagemagick_installed) {
                        healthStatus.textContent = '✅ Ready';
                        healthStatus.className = 'health-status healthy';
                        installInstructions.style.display = 'none';
                        processBtn.disabled = false;
                    } else if (data.status === 'healthy' && !data.imagemagick_installed) {
                        healthStatus.textContent = '⚠️ ImageMagick Missing';
                        healthStatus.className = 'health-status warning';
                        installInstructions.style.display = 'block';
                        processBtn.disabled = true;
                        showError('ImageMagick is not installed. Please see installation instructions above.');
                    } else {
                        healthStatus.textContent = '❌ Backend Issues';
                        healthStatus.className = 'health-status unhealthy';
                        installInstructions.style.display = 'none';
                        processBtn.disabled = true;
                        showError('Backend server is not running.');
                    }
                })
                .catch(error => {
                    const healthStatus = document.getElementById('healthStatus');
                    const processBtn = document.getElementById('processBtn');
                    healthStatus.textContent = '🔌 Disconnected';
                    healthStatus.className = 'health-status unhealthy';
                    processBtn.disabled = true;
                    showError('Cannot connect to backend. Please start the Flask server.');
                });
        }

        function displayOriginalImage(file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const originalImage = document.getElementById('originalImage');
                const originalPlaceholder = document.getElementById('originalPlaceholder');
                originalImage.src = e.target.result;
                originalImage.style.display = 'block';
                originalPlaceholder.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }

        function toggleAdvancedOptions() {
            const action = document.getElementById('action').value;
            const textGroup = document.getElementById('textGroup');
            if (action === 'text') {
                textGroup.style.display = 'block';
            } else {
                textGroup.style.display = 'none';
            }
        }

        function toggleAdvanced() {
            const advancedOptions = document.getElementById('advancedOptions');
            advancedOptions.classList.toggle('expanded');
        }

        function showStatus(message) {
            const statusEl = document.getElementById('statusMessage');
            const errorEl = document.getElementById('errorMessage');
            errorEl.style.display = 'none';
            statusEl.textContent = message;
            statusEl.style.display = 'block';
            setTimeout(() => { statusEl.style.display = 'none'; }, 3000);
        }

        function showError(message) {
            const statusEl = document.getElementById('statusMessage');
            const errorEl = document.getElementById('errorMessage');
            statusEl.style.display = 'none';
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }

        function hideMessages() {
            document.getElementById('statusMessage').style.display = 'none';
            document.getElementById('errorMessage').style.display = 'none';
        }

        function processImage() {
            const fileInput = document.getElementById('imageInput');
            const action = document.getElementById('action').value;
            const text = document.getElementById('textInput').value;
            if (!fileInput.files.length) {
                showError('Please upload an image first.');
                return;
            }
            if (action === 'text' && !text.trim()) {
                showError('Please enter text to add to the image.');
                return;
            }
            document.getElementById('loadingIndicator').style.display = 'block';
            hideMessages();
            const formData = new FormData();
            formData.append('image', fileInput.files[0]);
            formData.append('action', action);
            formData.append('text', text);
            formData.append('resize_percentage', document.getElementById('resizePercentage').value);
            formData.append('rotation_angle', document.getElementById('rotationAngle').value);
            formData.append('text_size', document.getElementById('textSize').value);
            formData.append('text_color', document.getElementById('textColor').value);
            formData.append('text_font', document.getElementById('textFont').value);
            formData.append('text_position', document.getElementById('textPosition').value);
            formData.append('blur_radius', document.getElementById('blurRadius').value);

            fetch(`${BACKEND_URL}/process`, {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => Promise.reject(err));
                }
                return response.blob();
            })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const outputImage = document.getElementById('outputImage');
                const processedPlaceholder = document.getElementById('processedPlaceholder');
                outputImage.src = url;
                outputImage.style.display = 'block';
                processedPlaceholder.style.display = 'none';
                showStatus('✅ Image processed successfully!');
            })
            .catch(error => {
                console.error('Error:', error);
                showError(error.error || 'Failed to process image. Please try again.');
            })
            .finally(() => {
                document.getElementById('loadingIndicator').style.display = 'none';
            });
        }

        function resetAll() {
            document.getElementById('imageInput').value = '';
            document.getElementById('action').selectedIndex = 3; // Add Text Overlay option
            document.getElementById('textInput').value = '';
            document.getElementById('resizePercentage').value = '50';
            document.getElementById('rotationAngle').value = '90';
            document.getElementById('textSize').value = '120';
            document.getElementById('textColor').selectedIndex = 1; // Black option
            document.getElementById('textFont').selectedIndex = 0; // Arial option
            document.getElementById('textPosition').selectedIndex = 2; // Center option
            document.getElementById('blurRadius').value = '0x1';
            document.getElementById('originalImage').style.display = 'none';
            document.getElementById('outputImage').style.display = 'none';
            document.getElementById('originalPlaceholder').style.display = 'block';
            document.getElementById('processedPlaceholder').style.display = 'block';
            document.getElementById('textGroup').style.display = 'block'; // Show text group for default action
            hideMessages();
            showStatus('🔄 All settings reset');
        }

        toggleAdvancedOptions();
    </script>
</body>
</html>
"""

# --- Flask Routes ---
@app.route('/')
def index():
    """Serve the HTML frontend directly from the Python file."""
    return HTML_CONTENT

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
