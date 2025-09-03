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
    
    # Security settings
    API_KEY_REQUIRED = os.environ.get('API_KEY_REQUIRED', 'false').lower() == 'true'
    DISABLE_API_AUTH = os.environ.get('DISABLE_API_AUTH', 'false').lower() == 'true'
    API_KEYS_FILE = os.environ.get('API_KEYS_FILE', 'api_keys.json')
    
    # Rate limiting (requests per hour per API key)
    RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 1000))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 3600))  # seconds
    
    # Request signature validation (for high-security environments)
    REQUIRE_SIGNATURE = os.environ.get('REQUIRE_SIGNATURE', 'false').lower() == 'true'
    SIGNATURE_SECRET = os.environ.get('SIGNATURE_SECRET') or 'default-signature-secret-change-in-production'
    SIGNATURE_TOLERANCE = int(os.environ.get('SIGNATURE_TOLERANCE', 300))  # seconds
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_API_REQUESTS = os.environ.get('LOG_API_REQUESTS', 'true').lower() == 'true'

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
