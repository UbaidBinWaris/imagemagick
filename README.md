# ImageMagick Processing API

A secure, production-ready API for image processing using ImageMagick, designed for n8n integration.

## Features

- 🔐 **Secure**: API key authentication, rate limiting, input validation
- 🚀 **Fast**: Efficient image processing with ImageMagick
- 🛡️ **Robust**: Comprehensive error handling and logging
- 🔄 **n8n Ready**: Designed for seamless n8n workflow integration
- 📊 **Monitoring**: Health checks and status endpoints
- 🎯 **Flexible**: Support for multiple image operations

## Supported Operations

- **resize**: Resize images by percentage
- **grayscale**: Convert to grayscale
- **rotate**: Rotate images by angle
- **text**: Add text overlays
- **blur**: Apply blur effects
- **sharpen**: Sharpen images
- **sepia**: Apply sepia tone
- **negative**: Create negative effect
- **flip**: Flip vertically
- **flop**: Flip horizontally

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install ImageMagick

**Windows:**
```bash
# Using Chocolatey (recommended)
choco install imagemagick

# Or download from: https://imagemagick.org/script/download.php#windows
```

**Linux:**
```bash
sudo apt-get install imagemagick
```

**macOS:**
```bash
brew install imagemagick
```

### 3. Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env and set your API key and other settings
```

### 4. Run the API

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /api/health
```
No authentication required. Returns service status.

### Process Image
```
POST /api/process
```
**Headers:**
- `X-API-Key`: Your API key

**Body (multipart/form-data):**
- `image`: Image file
- `action`: Operation to perform
- Additional parameters based on action

**Example Response:**
```json
{
  "success": true,
  "message": "Image processed successfully",
  "data": {
    "image": "base64-encoded-image-data",
    "format": "jpg",
    "size_bytes": 12345,
    "processing_time_seconds": 0.523,
    "action": "resize",
    "parameters": {...},
    "timestamp": "2024-01-01T12:00:00"
  },
  "metadata": {
    "request_id": "uuid",
    "content_type": "image/jpg",
    "filename": "processed_uuid.jpg"
  }
}
```

### API Status
```
GET /api/status
```
**Headers:**
- `X-API-Key`: Your API key

Returns API configuration and capabilities.

### Documentation
```
GET /api/docs
```
Returns complete API documentation.

## n8n Integration

### Setting up n8n Workflow

1. **Add HTTP Request Node**
2. **Configure the node:**
   - **Method**: POST
   - **URL**: `http://your-server:5000/api/process`
   - **Headers**: 
     ```json
     {
       "X-API-Key": "your-api-key-here"
     }
     ```
   - **Body**: Form Data
     - Add `image` field (file)
     - Add `action` field (text)
     - Add other parameters as needed

3. **Example n8n Configuration:**
```json
{
  "httpRequestOptions": {
    "url": "http://localhost:5000/api/process",
    "method": "POST",
    "headers": {
      "X-API-Key": "your-api-key"
    },
    "body": {
      "mode": "formData",
      "formData": {
        "image": "={{$binary.data}}",
        "action": "resize",
        "resize_percentage": "75"
      }
    }
  }
}
```

### Processing the Response

The API returns the processed image as base64 data. In n8n:

1. **Use Code Node** to decode base64:
```javascript
// Decode base64 image
const imageData = items[0].json.data.image;
const buffer = Buffer.from(imageData, 'base64');

return [
  {
    binary: {
      image: {
        data: buffer,
        mimeType: `image/${items[0].json.data.format}`,
        fileName: items[0].json.metadata.filename
      }
    }
  }
];
```

## Security Features

- **API Key Authentication**: Secure access control
- **Rate Limiting**: Prevents abuse (20 requests/minute for processing)
- **Input Validation**: Sanitizes all inputs
- **File Type Validation**: Only allows safe image formats
- **Size Limits**: 16MB maximum file size
- **Timeout Protection**: 60-second processing timeout
- **Secure Filename Handling**: Prevents path traversal attacks

## Error Handling

All errors return JSON with structured error information:

```json
{
  "error": "Error Type",
  "message": "Human-readable description",
  "code": "MACHINE_READABLE_CODE"
}
```

Common error codes:
- `INVALID_API_KEY`: Authentication failed
- `INVALID_FILE_TYPE`: Unsupported file format
- `PROCESSING_ERROR`: Image processing failed
- `TIMEOUT`: Processing took too long
- `RATE_LIMIT_EXCEEDED`: Too many requests

## Production Deployment

### Environment Variables

Set these in production:

```bash
export SECRET_KEY="your-strong-secret-key"
export API_KEY="your-secure-api-key"
export JWT_SECRET="your-jwt-secret"
export FLASK_ENV="production"
export PORT="5000"
```

### Using with Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install ImageMagick
RUN apt-get update && apt-get install -y imagemagick && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

### Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for image processing
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        
        # Increase max body size for file uploads
        client_max_body_size 20M;
    }
}
```

## Monitoring

### Health Monitoring

Monitor the `/api/health` endpoint:

```bash
curl http://localhost:5000/api/health
```

### Logs

The application logs all processing activities. In production, configure proper log rotation.

## Troubleshooting

### ImageMagick Not Found
- Ensure ImageMagick is installed and in PATH
- Try the full path to the binary if needed
- Restart the application after installation

### Rate Limit Issues
- Check your request frequency
- Consider implementing Redis for distributed rate limiting

### Processing Timeouts
- Reduce image size
- Check available system resources
- Adjust timeout in code if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
