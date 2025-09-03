"""
Utility functions for the ImageMagick Web Application
"""
import os
import subprocess
import logging
from .config import Config

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def check_imagemagick():
    """Check if ImageMagick is installed and return the command to use"""
    try:
        for cmd in Config.IMAGEMAGICK_COMMANDS:
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
    
    action_handlers = {
        "resize": lambda: cmd.extend(["-resize", f"{params.get('resize_percentage', '50')}%"]),
        "grayscale": lambda: cmd.extend(["-colorspace", "Gray"]),
        "rotate": lambda: cmd.extend(["-rotate", params.get('rotation_angle', '90')]),
        "text": lambda: _add_text_command(cmd, params),
        "blur": lambda: cmd.extend(["-blur", params.get('blur_radius', '0x1')]),
        "sharpen": lambda: cmd.extend(["-sharpen", "0x1"]),
        "sepia": lambda: cmd.extend(["-sepia-tone", "80%"]),
        "negative": lambda: cmd.extend(["-negate"]),
        "flip": lambda: cmd.extend(["-flip"]),
        "flop": lambda: cmd.extend(["-flop"])
    }
    
    if action not in action_handlers:
        raise ValueError(f'Invalid action: {action}')
    
    action_handlers[action]()
    cmd.append(output_path)
    return cmd

def _add_text_command(cmd, params):
    """Add text overlay command parameters"""
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

def cleanup_files(*file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not remove file {file_path}: {e}")

def validate_processing_params(action, params):
    """Validate processing parameters"""
    if action == 'text' and not params.get('text', '').strip():
        raise ValueError('Text parameter is required for text action')
    
    # Add more validation as needed
    return True
