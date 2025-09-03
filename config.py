"""
Configuration settings for the ImageMagick Web Application
"""
import os

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Application directories
    UPLOAD_FOLDER = "uploads"
    OUTPUT_FOLDER = "outputs"
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
    
    # ImageMagick commands to try (in order of preference)
    IMAGEMAGICK_COMMANDS = [
        'magick',
        'convert',
        'C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe'
    ]
    
    # Processing timeouts
    IMAGEMAGICK_TIMEOUT = 30  # seconds
    
    # Default processing parameters
    DEFAULT_PARAMS = {
        'resize_percentage': '50',
        'rotation_angle': '90',
        'text_size': '120',
        'text_color': 'black',
        'text_font': 'Arial',
        'text_position': 'Center',
        'blur_radius': '0x1'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
