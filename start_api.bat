@echo off
echo Starting Flask ImageMagick API...
set FLASK_ENV=production
python -c "from app import app; app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)"
pause
