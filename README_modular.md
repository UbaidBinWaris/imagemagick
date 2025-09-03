# ImageMagick Web Processor - Modular Version

A modular web application for processing images using ImageMagick, built with Flask and modern frontend technologies.

## Project Structure

```
imagemagick/
├── app.py                 # Original monolithic application
├── app_new.py            # New modular application (main entry point)
├── config.py             # Configuration settings
├── utils.py              # Utility functions
├── templates/            # HTML templates
│   └── index.html       # Main frontend template
├── static/              # Static files
│   ├── css/
│   │   └── styles.css   # Application styles
│   └── js/
│       └── app.js       # Frontend JavaScript logic
├── uploads/             # Temporary upload storage
└── outputs/             # Processed image outputs
```

## Features

- **Modular Architecture**: Separated concerns with dedicated modules
- **Clean API Design**: RESTful endpoints for health checks and image processing
- **Frontend/Backend Separation**: Static files served separately from backend logic
- **Error Handling**: Comprehensive error handling and logging
- **File Management**: Automatic cleanup of temporary files
- **Configuration Management**: Environment-based configuration
- **Responsive Design**: Mobile-friendly user interface

## Supported Operations

1. **Resize** - Scale images by percentage
2. **Grayscale** - Convert to black and white
3. **Rotate** - Rotate images by specified angle
4. **Text Overlay** - Add text with customizable fonts, colors, and positions
5. **Blur** - Apply blur effects with configurable radius
6. **Sharpen** - Enhance image sharpness
7. **Sepia** - Apply sepia tone effect
8. **Negative** - Invert image colors
9. **Flip/Flop** - Vertical and horizontal mirroring

## API Endpoints

### GET /
Returns the main HTML interface

### GET /health
Returns server health status and ImageMagick availability
```json
{
  "status": "healthy",
  "imagemagick_installed": true,
  "magick_command": "magick",
  "timestamp": "2025-09-03T12:00:00"
}
```

### POST /process
Processes an uploaded image with specified parameters

**Request Parameters:**
- `image` (file): Image file to process
- `action` (string): Processing action (resize, grayscale, rotate, text, etc.)
- `text` (string): Text to add (for text action)
- `resize_percentage` (number): Resize percentage (default: 50)
- `rotation_angle` (number): Rotation angle (default: 90)
- `text_size` (number): Text size (default: 120)
- `text_color` (string): Text color (default: black)
- `text_font` (string): Font family (default: Arial)
- `text_position` (string): Text position (default: Center)
- `blur_radius` (string): Blur radius (default: 0x1)

**Response:**
Returns the processed image file or error message

## Installation & Setup

### Prerequisites
1. Python 3.7+
2. ImageMagick installed on your system

### ImageMagick Installation

**Windows:**
1. Download from [ImageMagick Downloads](https://imagemagick.org/script/download.php#windows)
2. Run installer as administrator
3. Ensure "Install development headers" is checked
4. Restart terminal after installation

**Alternative (Chocolatey):**
```powershell
choco install imagemagick
```

### Python Dependencies
```bash
pip install flask flask-cors
```

## Running the Application

### Development Mode
```bash
python app_new.py
```

### Production Mode
```bash
set FLASK_ENV=production
python app_new.py
```

### Custom Port
```bash
set PORT=8080
python app_new.py
```

## Configuration

The application supports different configuration environments:

- **Development**: Debug mode enabled, verbose logging
- **Production**: Optimized for production deployment
- **Testing**: Configuration for unit tests

Environment can be set using the `FLASK_ENV` environment variable.

## Frontend Architecture

### JavaScript (app.js)
- **Class-based Architecture**: `ImageProcessor` class manages all frontend logic
- **Async/Await**: Modern JavaScript for API communication
- **Event Handling**: Centralized event listener management
- **Error Handling**: User-friendly error messages and status updates
- **Form Validation**: Client-side input validation

### CSS (styles.css)
- **Modern CSS**: Flexbox and Grid layouts
- **Responsive Design**: Mobile-first approach
- **Custom Properties**: CSS variables for theming
- **Animations**: Smooth transitions and loading indicators
- **Component-based**: Modular CSS classes

### HTML (index.html)
- **Semantic Markup**: Proper HTML5 structure
- **Accessibility**: ARIA labels and semantic elements
- **Template Integration**: Flask template syntax for asset URLs

## Error Handling

The application includes comprehensive error handling:

- **Client-side Validation**: File type and size validation
- **Server-side Validation**: Parameter validation and sanitization
- **ImageMagick Errors**: Detailed error messages from processing failures
- **Network Errors**: Connection and timeout handling
- **File Management**: Automatic cleanup of temporary files

## Security Features

- **File Type Validation**: Restricted to safe image formats
- **File Size Limits**: 16MB maximum upload size
- **Secure Filenames**: UUID-based temporary file naming
- **CORS Configuration**: Configurable cross-origin requests
- **Input Sanitization**: Parameter validation and escaping

## Development Guidelines

### Adding New Image Operations
1. Add the operation to `build_imagemagick_command()` in `utils.py`
2. Update the frontend dropdown in `templates/index.html`
3. Add any required parameters to the configuration
4. Update the API documentation

### Modifying the Frontend
- CSS changes: Edit `static/css/styles.css`
- JavaScript logic: Edit `static/js/app.js`
- HTML structure: Edit `templates/index.html`

### Configuration Changes
- Add new settings to `config.py`
- Use environment variables for sensitive data
- Document new configuration options

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.9-slim
# Install ImageMagick
RUN apt-get update && apt-get install -y imagemagick
# Copy application
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "app_new.py"]
```

### Traditional Deployment
1. Install Python dependencies
2. Install ImageMagick on target system
3. Set environment variables
4. Run with production WSGI server (gunicorn, uwsgi)

## Monitoring

- **Health Endpoint**: `/health` for uptime monitoring
- **Logging**: Structured logging for debugging
- **Error Tracking**: Detailed error messages and stack traces

## Contributing

1. Follow the modular architecture patterns
2. Add appropriate error handling
3. Update documentation for new features
4. Include unit tests for new functionality
5. Maintain backward compatibility

## License

This project is open source and available under the MIT License.
