@echo off
echo Testing n8n webhook workflow...
echo.

REM Test the Flask API first
echo 1. Testing Flask API health...
curl -H "X-API-Key: ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M" http://127.0.0.1:5000/api/health
echo.
echo.

REM Test with a sample image (you'll need to update the webhook URL)
echo 2. Testing n8n webhook (update the URL below):
echo Replace YOUR_WEBHOOK_URL with the actual webhook URL from n8n
echo.
echo Example:
echo curl -X POST -F "image=@static/test-image.jpg" -F "action=resize" -F "resize_percentage=50" http://localhost:5678/webhook/simple-upload
echo.

pause
