#!/usr/bin/env python3
"""
Simple server runner for n8n integration
"""
import os
import sys
from app import app

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Flask ImageMagick API for n8n")
    print("=" * 60)
    print(f"🌐 Server will run on: http://127.0.0.1:5000")
    print(f"🔑 API Key: ZWIHZc5e-SWR-XdIPykAZ3K6PncdnwBxa9VlZ9yuZ3M")
    print(f"📡 Health Check: http://127.0.0.1:5000/api/health")
    print("=" * 60)
    
    try:
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
