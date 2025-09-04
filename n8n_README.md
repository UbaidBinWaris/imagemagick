# 🎨 n8n ImageMagick Integration

## 📁 Files
- **`n8n_imagemagick_workflow.json`** - Import this into n8n
- **`n8n_workflow_guide.md`** - Detailed documentation

## 🚀 Quick Start
1. Import `n8n_imagemagick_workflow.json` into n8n
2. Ensure your Flask server is running on `127.0.0.1:5000`
3. Click "Test workflow" → "Execute workflow"
4. Get your processed image with text overlay!

## ✅ What It Does
- Checks API health
- Processes default image (`Capture.PNG`)
- Adds text "Hello from n8n!" in center
- Returns processed image as PNG file

## 🔧 Working Configuration
- **API Key**: `ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M`
- **Server**: `http://127.0.0.1:5000`
- **Endpoints**: `/health` and `/process-default`
- **Response**: Binary image file (333KB PNG)

## 📋 Output Example
```json
{
  "status": "SUCCESS",
  "message": "Image processed successfully with text overlay",
  "api_health": "healthy", 
  "imagemagick_installed": true,
  "processed_image_size": 340992,
  "image_mime_type": "image/png",
  "image_filename": "default_output_[uuid].png",
  "processing_timestamp": "2025-09-03T04:30:00.000Z"
}
```

**Plus the actual processed image file!** 🖼️

## 🎯 Features
- ✅ Sequential workflow (no connection errors)
- ✅ Proper error handling  
- ✅ Health check integration
- ✅ Binary file response handling
- ✅ Metadata extraction
- ✅ Timestamp tracking

This is a **single, working workflow** that successfully integrates with your ImageMagick API! 🎉
