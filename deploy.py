#!/usr/bin/env python3
"""
Production deployment script for ImageMagick Processing API
This script helps configure the API for production use
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path

def generate_secure_keys():
    """Generate secure keys for production"""
    return {
        'SECRET_KEY': secrets.token_hex(32),
        'API_KEY': secrets.token_urlsafe(32),
        'JWT_SECRET': secrets.token_hex(32),
        'ADMIN_PASSWORD': secrets.token_urlsafe(16)
    }

def create_production_env():
    """Create production environment file"""
    keys = generate_secure_keys()
    
    env_content = f"""# ImageMagick Processing API - Production Configuration
# Generated on {os.getenv('COMPUTERNAME', 'server')} at {subprocess.check_output(['date'], shell=True).decode().strip()}

# Security Settings (CHANGE THESE!)
SECRET_KEY={keys['SECRET_KEY']}
API_KEY={keys['API_KEY']}
JWT_SECRET={keys['JWT_SECRET']}
ADMIN_PASSWORD={keys['ADMIN_PASSWORD']}

# Flask Configuration
FLASK_ENV=production
PORT=5000

# Redis Configuration (recommended for production)
# REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO

# Optional: Database URL if you add database support
# DATABASE_URL=postgresql://user:password@localhost/imagemagick_api
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Production environment file created: .env")
    print(f"🔑 Your API key: {keys['API_KEY']}")
    print(f"🔐 Admin password: {keys['ADMIN_PASSWORD']}")
    print("\n⚠️  IMPORTANT: Save these credentials securely!")
    return keys

def create_systemd_service():
    """Create systemd service file for Linux"""
    current_dir = Path.cwd()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=ImageMagick Processing API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory={current_dir}
Environment=PATH=/usr/bin:/usr/local/bin
EnvironmentFile={current_dir}/.env
ExecStart={python_path} app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "imagemagick-api.service"
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Systemd service file created: {service_file}")
    print("   To install:")
    print(f"   sudo cp {service_file} /etc/systemd/system/")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable imagemagick-api")
    print("   sudo systemctl start imagemagick-api")

def create_docker_files():
    """Create Docker files for containerized deployment"""
    
    # Dockerfile
    dockerfile_content = """FROM python:3.11-slim

# Install ImageMagick and dependencies
RUN apt-get update && apt-get install -y \\
    imagemagick \\
    libmagickwand-dev \\
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the application
CMD ["python", "app.py"]
"""
    
    # Docker Compose
    compose_content = """version: '3.8'

services:
  imagemagick-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - API_KEY=${API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    depends_on:
      - redis
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - imagemagick-api
    restart: unless-stopped

volumes:
  redis_data:
"""
    
    # Nginx configuration
    nginx_content = """events {
    worker_connections 1024;
}

http {
    upstream api {
        server imagemagick-api:5000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # Redirect HTTP to HTTPS
        # return 301 https://$server_name$request_uri;
        
        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts for image processing
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
            proxy_send_timeout 300;
            
            # File upload size
            client_max_body_size 20M;
        }
    }
    
    # Uncomment for HTTPS
    # server {
    #     listen 443 ssl http2;
    #     server_name localhost;
    #     
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #     
    #     location / {
    #         proxy_pass http://api;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #         
    #         proxy_read_timeout 300;
    #         proxy_connect_timeout 300;
    #         proxy_send_timeout 300;
    #         
    #         client_max_body_size 20M;
    #     }
    # }
}
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    with open('nginx.conf', 'w') as f:
        f.write(nginx_content)
    
    print("✅ Docker files created:")
    print("   - Dockerfile")
    print("   - docker-compose.yml")
    print("   - nginx.conf")
    print("\n   To deploy with Docker:")
    print("   docker-compose up -d")

def create_production_requirements():
    """Create production requirements with additional packages"""
    prod_requirements = """Flask==2.3.3
Flask-CORS==4.0.0
Flask-Limiter==3.5.0
PyJWT==2.8.0
Werkzeug==2.3.7
requests==2.31.0
gunicorn==21.2.0
redis==5.0.1
python-dotenv==1.0.0
"""
    
    with open('requirements-prod.txt', 'w') as f:
        f.write(prod_requirements)
    
    print("✅ Production requirements created: requirements-prod.txt")

def main():
    """Main deployment setup"""
    print("🚀 ImageMagick API Production Setup")
    print("=" * 50)
    
    # Check if in production environment
    if os.path.exists('.env'):
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Skipping environment file creation")
        else:
            keys = create_production_env()
    else:
        keys = create_production_env()
    
    create_production_requirements()
    
    # Ask what deployment method to prepare
    print("\nChoose deployment method:")
    print("1. Docker (recommended)")
    print("2. Systemd service (Linux)")
    print("3. Both")
    print("4. Skip")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice in ['1', '3']:
        create_docker_files()
    
    if choice in ['2', '3']:
        create_systemd_service()
    
    print("\n🎉 Production setup complete!")
    print("\n📋 Next steps:")
    print("1. Review and customize the .env file")
    print("2. Install production requirements:")
    print("   pip install -r requirements-prod.txt")
    print("3. Configure your reverse proxy (nginx)")
    print("4. Set up SSL certificates")
    print("5. Configure monitoring and logging")
    print("6. Test the API thoroughly")
    
    print("\n🔗 For n8n integration:")
    print("- Use the API key from the .env file")
    print("- Point n8n to your production URL")
    print("- Monitor rate limits and adjust as needed")

if __name__ == "__main__":
    main()
