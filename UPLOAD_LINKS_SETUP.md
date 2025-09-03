# n8n Image Upload with Permanent Links Setup

## Overview
This setup allows you to upload images via n8n webhook and get permanent links to the uploaded images stored in the `/uploads` folder.

## What's New

### 1. New Webhook Endpoint
- **URL**: `http://localhost:5000/webhook/<webhook_id>`
- **Purpose**: Handles image uploads and processing specifically for n8n
- **Features**:
  - Saves original images permanently in `/uploads` folder
  - Processes images (resize, etc.)
  - Returns both processed image and permanent link to original
  - No API key required (webhook-friendly)

### 2. Image Access Endpoints
- **`/uploads/<filename>`**: Direct access to uploaded images
- **`/api/uploads`**: List all uploaded images with links

## Setup Instructions

### Step 1: Start the Flask Server
```bash
python run_server.py
```
The server will run on `http://localhost:5000`

### Step 2: Import n8n Workflow
1. Open n8n (usually at `http://localhost:5678`)
2. Import the workflow from: `n8n-webhook-with-upload-link.json`
3. Activate the workflow

### Step 3: Test the Setup

#### Option A: Use the Test Page
1. Open `n8n-upload-links-test.html` in your browser
2. Upload an image and see the permanent links generated

#### Option B: Use curl
```bash
curl -X POST \
  -F "image=@static/test-image.jpg" \
  -F "action=resize" \
  -F "resize_percentage=50" \
  http://localhost:5678/webhook/simple-upload
```

## Response Format

When you upload an image, you'll get a response like this:

```json
{
  "success": true,
  "message": "Image processed and uploaded successfully",
  "upload_info": {
    "original_filename": "test-image.jpg",
    "upload_timestamp": "20250903_143022",
    "permanent_filename": "20250903_143022_uuid_test-image.jpg",
    "original_image_url": "http://localhost:5000/uploads/20250903_143022_uuid_test-image.jpg"
  },
  "processing_info": {
    "action_performed": "resize",
    "resize_percentage": "50",
    "processing_time": 0.234
  },
  "links": {
    "view_original": "http://localhost:5000/uploads/20250903_143022_uuid_test-image.jpg",
    "upload_folder_link": "http://localhost:5000/uploads/20250903_143022_uuid_test-image.jpg",
    "list_all_uploads": "http://localhost:5000/api/uploads"
  }
}
```

## Key Benefits

1. **Permanent Storage**: Images are stored permanently in `/uploads` folder
2. **Direct Access**: Get direct URLs to access uploaded images
3. **Timestamped**: Files include timestamp for easy organization
4. **No Cleanup**: Original files are kept (only temporary processing files are cleaned)
5. **List View**: Can see all uploaded images via `/api/uploads`

## File Naming Convention

Uploaded files are saved with this format:
```
YYYYMMDD_HHMMSS_UUID_original-filename.ext
```

Example: `20250903_143022_a1b2c3d4-e5f6_my-image.jpg`

This ensures:
- Chronological sorting
- Unique filenames
- Original filename preservation

## Integration with n8n

The new workflow (`n8n-webhook-with-upload-link.json`) includes:

1. **Webhook Trigger**: Receives file uploads
2. **HTTP Request**: Sends to Flask webhook endpoint
3. **Data Processing**: Extracts upload links and metadata
4. **Response**: Returns structured data with all links

## Access Your Uploads

- **Single Image**: `http://localhost:5000/uploads/<filename>`
- **List All**: `http://localhost:5000/api/uploads`
- **Via n8n**: Links are included in every webhook response

## Troubleshooting

### Common Issues:
1. **Files not saving**: Check that `/uploads` folder exists and is writable
2. **Links not working**: Ensure Flask server is running on port 5000
3. **n8n workflow fails**: Verify the webhook URL matches your n8n setup

### Log Messages:
Check the Flask console for detailed logging of uploads and processing.

## Example Use Cases

1. **Image Gallery**: Upload images and build a gallery using the returned links
2. **Document Processing**: Store uploaded documents permanently while processing them
3. **Archive System**: Keep original files accessible while creating processed versions
4. **API Integration**: Use the permanent links in other systems or APIs

## Security Notes

- Webhook endpoints don't require API keys (by design for n8n integration)
- Uploaded files are publicly accessible via direct URLs
- Consider adding authentication if used in production
- File types are restricted to allowed image formats
