"""
Example script showing how to use the ImageMagick API with authentication
"""
import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:5000"
API_KEY = "JRO6liHv3-mVZtmcD-TwBbxa3jwUeROSFr5AqQ5dfmg"  # Replace with your actual API key

def get_headers():
    """Get headers with API key authentication"""
    return {
        'X-API-Key': API_KEY
    }

def check_health():
    """Check API health and authentication"""
    print("🔍 Checking API health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Health Check Successful!")
            print(f"   Status: {data['status']}")
            print(f"   ImageMagick: {'✅' if data['imagemagick_installed'] else '❌'}")
            print(f"   API Auth: {'✅' if data.get('api_auth_enabled') else '❌'}")
            if data.get('authenticated_as'):
                print(f"   Authenticated as: {data['authenticated_as']}")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid API key")
            return False
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def process_image(image_path, action="text", text="Hello API!", **params):
    """Process an image using the API"""
    print(f"🎨 Processing image: {image_path}")
    print(f"   Action: {action}")
    if action == "text":
        print(f"   Text: {text}")
    
    try:
        # Prepare the files and data
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            data = {
                'action': action,
                'text': text,
                **params
            }
            
            response = requests.post(
                f"{API_BASE_URL}/process",
                files=files,
                data=data,
                headers=get_headers()
            )
        
        if response.status_code == 200:
            # Save the processed image
            output_path = f"processed_{action}_{image_path}"
            with open(output_path, 'wb') as output_file:
                output_file.write(response.content)
            print(f"✅ Image processed successfully!")
            print(f"   Output saved to: {output_path}")
            return output_path
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid API key")
            return None
        else:
            error_data = response.json()
            print(f"❌ Processing failed: {error_data.get('error', 'Unknown error')}")
            return None
            
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def list_api_keys():
    """List all API keys (admin permission required)"""
    print("📋 Listing API keys...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/keys", headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            keys = data['api_keys']
            
            if not keys:
                print("   No API keys found.")
                return
            
            print(f"   Found {len(keys)} API key(s):")
            for key in keys:
                status = "Active" if key['active'] else "Revoked"
                print(f"   - {key['name']} ({key['key_id'][:8]}...) - {status}")
                print(f"     Permissions: {', '.join(key['permissions'])}")
                print(f"     Usage: {key['usage_count']} requests")
                
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid API key or insufficient permissions")
        else:
            print(f"❌ Failed to list keys: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def create_api_key(name, permissions=None, expires_days=None):
    """Create a new API key (admin permission required)"""
    print(f"🔑 Creating new API key: {name}")
    
    data = {
        'name': name,
        'permissions': permissions or ['process', 'health']
    }
    if expires_days:
        data['expires_days'] = expires_days
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/keys",
            json=data,
            headers=get_headers()
        )
        
        if response.status_code == 201:
            result = response.json()
            key_info = result['key_info']
            print("✅ API Key created successfully!")
            print(f"   Name: {key_info['name']}")
            print(f"   Key ID: {key_info['key_id']}")
            print(f"   API Key: {key_info['api_key']}")
            print(f"   Permissions: {', '.join(key_info['permissions'])}")
            print("⚠️  Save this API key securely!")
            return key_info
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid API key or insufficient permissions")
        else:
            error_data = response.json()
            print(f"❌ Failed to create key: {error_data.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main demo function"""
    print("🎨 ImageMagick API Demo")
    print("=" * 50)
    
    # Check health first
    if not check_health():
        print("\n❌ Health check failed. Exiting.")
        return
    
    print("\n" + "=" * 50)
    
    # List existing API keys
    list_api_keys()
    
    print("\n" + "=" * 50)
    
    # Example image processing (uncomment and provide a real image path)
    # if process_image("example.jpg", action="text", text="API Test!"):
    #     print("Image processing demo completed!")
    # 
    # if process_image("example.jpg", action="resize", resize_percentage="25"):
    #     print("Image resizing demo completed!")
    
    print("\n📝 To test image processing:")
    print("   1. Put an image file in this directory")
    print("   2. Uncomment the process_image calls above")
    print("   3. Update the image filename")
    print("   4. Run the script again")
    
    print("\n🔑 To create a new API key:")
    print("   create_api_key('My New Key', ['process', 'health'])")

if __name__ == "__main__":
    main()
