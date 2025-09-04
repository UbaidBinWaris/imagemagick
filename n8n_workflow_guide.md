# n8n ImageMagick API Workflow - Final Version

## ✅ **Working Solution**

Import: **`n8n_imagemagick_workflow.json`** - This is the only file you need!

## 🚀 **Quick Start**

1. **Import the workflow**: `n8n_imagemagick_workflow.json`
2. **Click "Test workflow"**
3. **Click "Execute workflow"**
4. **Get your processed image!**

## 📋 **Workflow Overview**

This workflow has **4 connected nodes** in sequence:

### **Node 1: Start Workflow** 
- Manual trigger to start the process

### **Node 2: Health Check**
- Checks API server status
- Verifies ImageMagick installation
- **URL**: `http://127.0.0.1:5000/health`

### **Node 3: Process Image**
- Adds text to the default image
- **URL**: `http://127.0.0.1:5000/process-default`
- **Text**: "Hello from n8n!"
- **Position**: Center
- **Color**: White
- **Size**: 120pt

### **Node 4: Final Result**
- Combines all results into summary
- Shows health status, image info, and processing details

## 🎯 **Expected Output**

```json
{
  "status": "SUCCESS",
  "message": "Image processed successfully with text overlay",
  "api_health": "healthy",
  "imagemagick_installed": true,
  "processed_image_size": 340992,
  "image_mime_type": "image/png",
  "image_filename": "default_output_24c69ab1-8cca-4838-bbfc-d83568b71419.png",
  "processing_timestamp": "2025-09-03T04:30:00.000Z"
}
```

**Plus**: The actual processed image file in the "Process Image" node!

## ⚙️ **Customization**

To change the text or styling, edit the "Process Image" node:

### **Text Options:**
- **text**: "Your custom message"
- **text_color**: white, black, red, blue, green, yellow
- **text_size**: 50, 100, 150, 200 (points)
- **text_position**: Center, North, South, East, West, NorthEast, NorthWest, SouthEast, SouthWest
- **text_font**: Arial, Times, Helvetica

### **Image Options:**
- **default_image**: Change to another PNG file in `src/default-image/`

### **API Options:**
- **URL**: Change port if server runs on different port
- **API Key**: Update if using different authentication

## 🔧 **Technical Details**

### **Authentication**
- **Header**: `X-API-Key`
- **Value**: `ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M`

### **API Endpoints**
- **Health**: `GET /health`
- **Process**: `POST /process-default`

### **Request Body**
```json
{
  "default_image": "Capture.PNG",
  "text": "Hello from n8n!",
  "text_position": "Center",
  "text_size": "120",
  "text_color": "white",
  "text_font": "Arial"
}
```

### **Response**
- **Success**: Binary PNG image file
- **Error**: JSON with error message

## 🆘 **Troubleshooting**

### **Common Issues:**

1. **Connection Refused**
   - Ensure Flask server runs on `127.0.0.1:5000`
   - Check API key is correct

2. **Image Not Found**
   - Verify `Capture.PNG` exists in `src/default-image/`
   - Check file permissions

3. **Bad Request**
   - Ensure Content-Type is `application/json`
   - Verify JSON body format

4. **No Response**
   - Check if ImageMagick is installed on server
   - Verify server is not busy processing other requests

## 📁 **File Structure**

After execution, you'll have:
- **Input**: Default image (`Capture.PNG`)
- **Output**: Processed image with text overlay
- **Metadata**: File size, mime type, filename, timestamp

This single workflow file contains everything you need for ImageMagick API integration! 🎉
