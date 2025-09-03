#!/usr/bin/env python3
"""
Test script for ImageMagick Processing API
This script demonstrates how to use the API for n8n integration
"""

import requests
import json
import base64
import os
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:5000/api"
API_KEY = "default-api-key-change-me"  # Change this in production

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        
        data = response.json()
        print("✅ Health check passed!")
        print(f"   Status: {data['status']}")
        print(f"   ImageMagick: {'✅' if data['imagemagick_installed'] else '❌'}")
        print(f"   Command: {data.get('magick_command', 'N/A')}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_api_status():
    """Test the API status endpoint"""
    print("\n🔍 Testing API status...")
    
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.get(f"{API_BASE_URL}/status", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print("✅ API status check passed!")
        print(f"   Service: {data['service']}")
        print(f"   Version: {data['version']}")
        print(f"   Status: {data['status']}")
        print(f"   Supported actions: {', '.join(data['supported_actions'])}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API status check failed: {e}")
        return False

def create_sample_image():
    """Create a sample image for testing using ImageMagick"""
    print("\n🎨 Creating sample image...")
    
    import subprocess
    
    # Create a simple test image using ImageMagick
    sample_path = "test_image.png"
    
    try:
        # Create a 300x200 blue image with text
        cmd = [
            "magick",
            "-size", "300x200",
            "xc:lightblue",
            "-gravity", "center",
            "-pointsize", "24",
            "-fill", "navy",
            "-annotate", "+0+0", "Test Image",
            sample_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Sample image created: {sample_path}")
        return sample_path
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠️  Could not create sample image: {e}")
        print("   You can use any existing image file instead")
        return None

def test_image_processing(image_path=None):
    """Test image processing endpoint"""
    print("\n🖼️  Testing image processing...")
    
    # If no image provided, try to create one
    if not image_path:
        image_path = create_sample_image()
    
    if not image_path or not os.path.exists(image_path):
        print("❌ No image available for testing")
        return False
    
    try:
        # Test resize operation
        headers = {"X-API-Key": API_KEY}
        
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            data = {
                'action': 'resize',
                'resize_percentage': '75'
            }
            
            response = requests.post(
                f"{API_BASE_URL}/process",
                headers=headers,
                files=files,
                data=data
            )
            response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            print("✅ Image processing succeeded!")
            print(f"   Action: {result['data']['action']}")
            print(f"   Format: {result['data']['format']}")
            print(f"   Size: {result['data']['size_bytes']} bytes")
            print(f"   Processing time: {result['data']['processing_time_seconds']}s")
            
            # Save the processed image
            image_data = base64.b64decode(result['data']['image'])
            output_path = f"processed_{image_path}"
            
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            print(f"   Processed image saved: {output_path}")
            return True
        else:
            print(f"❌ Image processing failed: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Image processing request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_authentication():
    """Test authentication"""
    print("\n🔐 Testing authentication...")
    
    # Test without API key
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        if response.status_code == 401:
            print("✅ Authentication protection working (no API key)")
        else:
            print(f"⚠️  Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"❌ Auth test failed: {e}")
    
    # Test with wrong API key
    try:
        headers = {"X-API-Key": "wrong-key"}
        response = requests.get(f"{API_BASE_URL}/status", headers=headers)
        if response.status_code == 401:
            print("✅ Authentication protection working (wrong API key)")
        else:
            print(f"⚠️  Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"❌ Auth test failed: {e}")

def demonstrate_n8n_integration():
    """Show example for n8n integration"""
    print("\n🔗 n8n Integration Example:")
    print("=" * 50)
    
    print("1. In n8n, create an HTTP Request node with these settings:")
    print(f"   URL: {API_BASE_URL}/process")
    print("   Method: POST")
    print("   Headers:")
    print(f"     X-API-Key: {API_KEY}")
    print("")
    print("2. Set Body Type to 'Form Data' and add:")
    print("   - image: [your image file]")
    print("   - action: resize")
    print("   - resize_percentage: 50")
    print("")
    print("3. The response will contain:")
    print("   - success: true/false")
    print("   - data.image: base64 encoded processed image")
    print("   - data.format: image format")
    print("   - metadata: additional information")
    print("")
    print("4. Use a Code node to decode the base64 image:")
    print("""
    const response = items[0].json;
    const imageData = response.data.image;
    const buffer = Buffer.from(imageData, 'base64');
    
    return [{
        binary: {
            image: {
                data: buffer,
                mimeType: `image/${response.data.format}`,
                fileName: response.metadata.filename
            }
        }
    }];
    """)

def main():
    """Run all tests"""
    print("🧪 ImageMagick Processing API Test Suite")
    print("=" * 50)
    
    # Check if server is running
    if not test_health_check():
        print("\n❌ Server is not running. Please start the API server first:")
        print("   python app.py")
        return
    
    # Run tests
    test_api_status()
    test_authentication()
    test_image_processing()
    demonstrate_n8n_integration()
    
    print("\n🎉 Test suite completed!")
    print("\nYour ImageMagick Processing API is ready for n8n integration!")

if __name__ == "__main__":
    main()
