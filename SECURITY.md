# 🔐 Security Features & API Authentication

## Overview

Your ImageMagick Web Application now includes comprehensive security features:

- **API Key Authentication** with hashed storage
- **Permission-based Access Control**
- **Rate Limiting** capabilities
- **Request Signature Validation** (for high-security environments)
- **Secure Key Management** with CLI tools

## 🔑 API Key Authentication

### Current Status
- **API Authentication**: Currently **DISABLED** (default for development)
- **Available API Key**: `JRO6liHv3-mVZtmcD-TwBbxa3jwUeROSFr5AqQ5dfmg`
- **Key Permissions**: `process`, `health`, `admin`

### Enabling API Authentication

#### Method 1: Environment Variable
```powershell
# PowerShell
$env:API_KEY_REQUIRED="true"
python app_new.py
```

#### Method 2: Create .env file
```bash
# Create .env file from template
copy .env.example .env

# Edit .env file and set:
API_KEY_REQUIRED=true
```

#### Method 3: Production Environment
```bash
# For production deployment
set FLASK_ENV=production
set API_KEY_REQUIRED=true
python app_new.py
```

## 🛠️ Managing API Keys

### Using the CLI Tool

#### Generate a new API key:
```powershell
python manage_keys.py generate "My App Key" --permissions process health
```

#### List all API keys:
```powershell
python manage_keys.py list
```

#### Revoke an API key:
```powershell
python manage_keys.py revoke <key_id>
```

#### Show key details:
```powershell
python manage_keys.py show <key_id>
```

### Using the Web API (Admin Permission Required)

#### Create a new key:
```bash
curl -X POST http://localhost:5000/api/keys \
  -H "X-API-Key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Key", "permissions": ["process", "health"]}'
```

#### List keys:
```bash
curl http://localhost:5000/api/keys \
  -H "X-API-Key: YOUR_ADMIN_KEY"
```

## 🔒 Permission System

### Available Permissions:
- **`process`** - Allow image processing operations
- **`health`** - Allow health check access
- **`admin`** - Allow API key management

### Permission Examples:
```python
# Read-only access
permissions = ["health"]

# Standard user access
permissions = ["process", "health"]

# Administrator access
permissions = ["process", "health", "admin"]
```

## 🌐 Using API Keys in Requests

### Frontend (JavaScript)
```javascript
// The frontend automatically handles API keys
// Just configure it in the UI or localStorage
localStorage.setItem('imagemagick_api_key', 'YOUR_API_KEY');
```

### cURL Examples
```bash
# Health check with API key
curl http://localhost:5000/health \
  -H "X-API-Key: JRO6liHv3-mVZtmcD-TwBbxa3jwUeROSFr5AqQ5dfmg"

# Process image with API key
curl -X POST http://localhost:5000/process \
  -H "X-API-Key: JRO6liHv3-mVZtmcD-TwBbxa3jwUeROSFr5AqQ5dfmg" \
  -F "image=@example.jpg" \
  -F "action=text" \
  -F "text=Hello API!"
```

### Python Example
```python
import requests

headers = {'X-API-Key': 'YOUR_API_KEY'}

# Health check
response = requests.get('http://localhost:5000/health', headers=headers)

# Process image
with open('image.jpg', 'rb') as f:
    files = {'image': f}
    data = {'action': 'text', 'text': 'Hello!'}
    response = requests.post('http://localhost:5000/process', 
                           files=files, data=data, headers=headers)
```

## 🔐 Advanced Security Features

### Request Signature Validation
For high-security environments, enable HMAC signature validation:

```bash
# Enable signature validation
REQUIRE_SIGNATURE=true
SIGNATURE_SECRET=your-super-secret-key
```

### Rate Limiting
Configure rate limits per API key:

```bash
# 1000 requests per hour per API key
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
```

### CORS Configuration
Restrict allowed origins:

```bash
# Allow specific domains
CORS_ORIGINS=https://myapp.com,https://api.myapp.com
```

## 🚀 Testing Your Setup

### 1. Test Without Authentication (Default)
```powershell
python app_new.py
python api_example.py
```

### 2. Test With Authentication Enabled
```powershell
$env:API_KEY_REQUIRED="true"
python app_new.py

# In another terminal:
python api_example.py
```

### 3. Test Frontend with API Key
1. Open http://localhost:5000
2. If API auth is enabled, you'll see the API key input section
3. Enter your API key: `JRO6liHv3-mVZtmcD-TwBbxa3jwUeROSFr5AqQ5dfmg`
4. Upload and process images normally

## 🔧 Troubleshooting

### Common Issues:

#### "Invalid or missing API key"
- Check that `API_KEY_REQUIRED=true` is set
- Verify your API key is correct
- Ensure the key hasn't been revoked

#### "Insufficient permissions"
- Check your API key permissions with `python manage_keys.py list`
- Generate a new key with appropriate permissions

#### "Cannot connect to backend"
- Ensure the Flask server is running
- Check the correct port (default: 5000)
- Verify firewall settings

### Debug Mode:
```powershell
# Enable detailed logging
$env:LOG_LEVEL="DEBUG"
$env:LOG_API_REQUESTS="true"
python app_new.py
```

## 🛡️ Security Best Practices

1. **Always use HTTPS in production**
2. **Store API keys securely** (environment variables, key management systems)
3. **Rotate API keys regularly**
4. **Use minimal permissions** for each key
5. **Monitor API usage** and set up alerts
6. **Enable rate limiting** in production
7. **Use strong secret keys** for signatures
8. **Regularly audit** API key usage

## 📊 Monitoring & Logging

The application logs all API requests when `LOG_API_REQUESTS=true`:

```
2025-09-03 02:59:58,095 - app_new - INFO - Image processing request from API key: Demo Key
```

Monitor your `api_keys.json` file for usage statistics:
- `usage_count` - Number of requests made
- `last_used` - Last request timestamp
- `created_at` - Key creation date

## 🔄 Migration from Non-Authenticated Version

If you're upgrading from the original version:

1. **Backup your data**
2. **Set `API_KEY_REQUIRED=false`** initially
3. **Generate API keys** for your users
4. **Update client applications** to include API keys
5. **Enable authentication** once clients are updated
6. **Test thoroughly** before production deployment

Your API authentication system is now fully functional and ready for production use! 🎉
