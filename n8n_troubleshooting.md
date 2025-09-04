# n8n ImageMagick Workflow - Troubleshooting Guide

## 🚨 Current Issue: "Bad request - please check your parameters"

The error you're seeing is caused by incorrect HTTP Request node configuration. Here's how to fix it:

## 🔧 Quick Fix Options:

### **Option 1: Import the Fixed Workflow (Recommended)**
1. Import the new file: `n8n_working_workflow.json`
2. This version has the correct node configuration
3. Ready to run without modifications

### **Option 2: Fix Your Current Workflow**

#### Step 1: Fix the "Process Default Image" Node
1. Click on the "Process Default Image" node
2. In the **Body** section:
   - Change from "Raw/JSON" to "JSON"
   - Remove any raw JSON text
   - Use the structured body format below

#### Step 2: Correct Body Configuration
Set the body as **JSON object** (not raw text):

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

#### Step 3: Verify Headers
Make sure these headers are set:
- `X-API-Key`: `ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M`
- `Content-Type`: `application/json`

#### Step 4: Check Response Format
In **Options** → **Response**:
- Set "Response Format" to **File**

## 📋 Working Node Configuration:

### **HTTP Request Node Settings:**
```
Method: POST
URL: http://127.0.0.1:5000/process-default

Headers:
- X-API-Key: ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M
- Content-Type: application/json

Body Type: JSON
Body:
{
  "default_image": "Capture.PNG",
  "text": "Hello from n8n!",
  "text_position": "Center",
  "text_size": "120", 
  "text_color": "white",
  "text_font": "Arial"
}

Response Format: File
```

## ✅ Expected Results:

### **Successful Response:**
- **Status**: 200 OK
- **Content-Type**: image/png
- **Body**: Binary image data
- **Size**: ~40-50KB (varies by image)

### **Error Responses to Watch For:**

#### 401 Unauthorized:
```json
{
  "error": "Unauthorized",
  "message": "Please provide a valid API key in the X-API-Key header"
}
```
**Fix**: Check API key value

#### 400 Bad Request:
```json
{
  "error": "No JSON data provided"
}
```
**Fix**: Ensure Content-Type is application/json and body is valid JSON

#### 404 Not Found:
```json
{
  "error": "Default image \"Capture.PNG\" not found"
}
```
**Fix**: Check if Capture.PNG exists in src/default-image folder

## 🧪 Testing Steps:

### 1. Test Health Check First
- Run just the health check node
- Should return: `{"status": "healthy", "imagemagick_installed": true}`

### 2. Test API with Postman
Before fixing n8n, verify the API works with Postman:
```
POST http://127.0.0.1:5000/process-default
Headers: 
  X-API-Key: ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M
  Content-Type: application/json
Body:
{
  "default_image": "Capture.PNG", 
  "text": "Test",
  "text_position": "Center",
  "text_size": "120",
  "text_color": "white",
  "text_font": "Arial"
}
```

### 3. Fix n8n Node
Once Postman works, copy the exact configuration to n8n.

## 🆘 Still Having Issues?

### Check These Common Problems:

1. **Server Not Running**
   - Ensure Flask server is running on port 5000
   - Check terminal for error messages

2. **Wrong API Key**
   - Verify API key: `ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M`
   - Check for typos or extra spaces

3. **Missing Image File**
   - Verify `Capture.PNG` exists in `src/default-image/` folder
   - Check file permissions

4. **Port Conflicts**
   - Try changing port from 5000 to 5001
   - Update both server and n8n workflow

5. **Network Issues**
   - Try `localhost:5000` instead of `127.0.0.1:5000`
   - Check Windows firewall settings

## 📁 Recommended File to Use:

**Import**: `n8n_working_workflow.json`

This workflow:
- ✅ Has correct node configuration
- ✅ Includes error handling  
- ✅ Works with your API settings
- ✅ Provides clear success/error feedback
- ✅ Runs health check and image processing in parallel

The new workflow should resolve the "Bad request" error you're experiencing!
