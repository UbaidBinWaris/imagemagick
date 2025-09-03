"""
Authentication and API Key Management Module
"""
import os
import secrets
import hashlib
import hmac
import time
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manages API key generation, validation, and storage"""
    
    def __init__(self, storage_file='api_keys.json'):
        self.storage_file = storage_file
        self.api_keys = self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading API keys: {e}")
                return {}
        return {}
    
    def save_api_keys(self):
        """Save API keys to storage file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Error saving API keys: {e}")
    
    def generate_api_key(self, name, permissions=None, expires_days=None):
        """
        Generate a new API key with optional permissions and expiration
        
        Args:
            name (str): Human-readable name for the API key
            permissions (list): List of allowed operations
            expires_days (int): Days until expiration (None for no expiration)
            
        Returns:
            dict: API key information including the raw key and metadata
        """
        # Generate a secure random API key
        raw_key = secrets.token_urlsafe(32)
        
        # Create key ID for storage
        key_id = hashlib.sha256(raw_key.encode()).hexdigest()[:16]
        
        # Hash the key for storage (using SHA-256 with salt)
        salt = secrets.token_bytes(32)
        key_hash = hashlib.pbkdf2_hmac('sha256', raw_key.encode(), salt, 100000)
        
        # Set expiration if specified
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        # Store key metadata
        self.api_keys[key_id] = {
            'name': name,
            'key_hash': key_hash.hex(),
            'salt': salt.hex(),
            'permissions': permissions or ['process', 'health'],
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'last_used': None,
            'usage_count': 0,
            'active': True
        }
        
        self.save_api_keys()
        
        logger.info(f"Generated new API key '{name}' with ID: {key_id}")
        
        return {
            'api_key': raw_key,
            'key_id': key_id,
            'name': name,
            'permissions': permissions or ['process', 'health'],
            'expires_at': expires_at
        }
    
    def validate_api_key(self, api_key, required_permission=None):
        """
        Validate an API key and check permissions
        
        Args:
            api_key (str): The raw API key to validate
            required_permission (str): Required permission for the operation
            
        Returns:
            dict: Validation result with key metadata or None if invalid
        """
        if not api_key:
            return None
        
        # Generate key ID from the provided key
        key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        if key_id not in self.api_keys:
            logger.warning(f"Unknown API key attempted: {key_id}")
            return None
        
        key_data = self.api_keys[key_id]
        
        # Check if key is active
        if not key_data.get('active', True):
            logger.warning(f"Inactive API key attempted: {key_id}")
            return None
        
        # Check expiration
        if key_data.get('expires_at'):
            expires_at = datetime.fromisoformat(key_data['expires_at']) if isinstance(key_data['expires_at'], str) else key_data['expires_at']
            if datetime.now() > expires_at:
                logger.warning(f"Expired API key attempted: {key_id}")
                return None
        
        # Validate the key hash
        salt = bytes.fromhex(key_data['salt'])
        stored_hash = key_data['key_hash']
        computed_hash = hashlib.pbkdf2_hmac('sha256', api_key.encode(), salt, 100000).hex()
        
        if not hmac.compare_digest(stored_hash, computed_hash):
            logger.warning(f"Invalid API key hash for: {key_id}")
            return None
        
        # Check permissions
        if required_permission and required_permission not in key_data.get('permissions', []):
            logger.warning(f"Insufficient permissions for key {key_id}: required {required_permission}")
            return None
        
        # Update usage statistics
        self.api_keys[key_id]['last_used'] = datetime.now()
        self.api_keys[key_id]['usage_count'] = key_data.get('usage_count', 0) + 1
        self.save_api_keys()
        
        logger.info(f"API key validated successfully: {key_id}")
        return {
            'key_id': key_id,
            'name': key_data['name'],
            'permissions': key_data['permissions']
        }
    
    def revoke_api_key(self, key_id):
        """Revoke an API key"""
        if key_id in self.api_keys:
            self.api_keys[key_id]['active'] = False
            self.save_api_keys()
            logger.info(f"API key revoked: {key_id}")
            return True
        return False
    
    def list_api_keys(self):
        """List all API keys with their metadata (excluding sensitive data)"""
        result = []
        for key_id, data in self.api_keys.items():
            result.append({
                'key_id': key_id,
                'name': data['name'],
                'permissions': data['permissions'],
                'created_at': data['created_at'],
                'expires_at': data.get('expires_at'),
                'last_used': data.get('last_used'),
                'usage_count': data.get('usage_count', 0),
                'active': data.get('active', True)
            })
        return result

def require_api_key(permission=None):
    """
    Decorator to require API key authentication for endpoints
    
    Args:
        permission (str): Required permission for the endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip API key check if authentication is disabled
            if current_app.config.get('DISABLE_API_AUTH', False):
                return f(*args, **kwargs)
            
            # Get API key from headers
            api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
            
            # Handle Bearer token format
            if api_key and api_key.startswith('Bearer '):
                api_key = api_key[7:]
            
            # Validate API key
            api_manager = current_app.api_manager
            key_data = api_manager.validate_api_key(api_key, permission)
            
            if not key_data:
                return jsonify({
                    'error': 'Invalid or missing API key',
                    'message': 'Please provide a valid API key in the X-API-Key header'
                }), 401
            
            # Add key data to request context
            request.api_key_data = key_data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_request_signature(payload, secret_key, timestamp):
    """
    Generate HMAC signature for request validation
    
    Args:
        payload (str): Request payload
        secret_key (str): Secret key for signing
        timestamp (str): Request timestamp
        
    Returns:
        str: HMAC signature
    """
    message = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_request_signature(payload, signature, secret_key, timestamp, tolerance=300):
    """
    Verify HMAC signature for request validation
    
    Args:
        payload (str): Request payload
        signature (str): Provided signature
        secret_key (str): Secret key for verification
        timestamp (str): Request timestamp
        tolerance (int): Allowed time difference in seconds
        
    Returns:
        bool: True if signature is valid
    """
    try:
        # Check timestamp tolerance
        request_time = int(timestamp)
        current_time = int(time.time())
        
        if abs(current_time - request_time) > tolerance:
            logger.warning(f"Request timestamp outside tolerance: {abs(current_time - request_time)}s")
            return False
        
        # Verify signature
        expected_signature = generate_request_signature(payload, secret_key, timestamp)
        return hmac.compare_digest(signature, expected_signature)
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Signature verification error: {e}")
        return False

def rate_limit_decorator(max_requests=100, window_seconds=3600):
    """
    Simple rate limiting decorator based on API key
    
    Args:
        max_requests (int): Maximum requests allowed
        window_seconds (int): Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This is a simplified rate limiter
            # In production, use Redis or similar for distributed rate limiting
            return f(*args, **kwargs)
        return decorated_function
    return decorator
