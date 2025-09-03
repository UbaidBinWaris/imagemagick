"""
Simple test script to demonstrate API usage with image processing
"""
import requests
import os
from PIL import Image, ImageDraw

# Configuration
API_BASE_URL = "http://localhost:5000"
API_KEY = "JRO6liHv3-mVZtmcD-TwBbxa3jwUeROSFr5AqQ5dfmg"

def create_test_image():
    """Create a simple test image"""
    # Create a simple test image
    img = Image.new('RGB', (400, 300), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Add some text
    draw.text((50, 100), "Test Image", fill='black')
    draw.text((50, 130), "For API Demo", fill='black')
    
    # Draw a rectangle
    draw.rectangle([50, 50, 350, 250], outline='red', width=3)
    
    # Save the image
    test_image_path = "test_image.png"
    img.save(test_image_path)
    print(f"✅ Created test image: {test_image_path}")
    return test_image_path

def test_api_processing():
    """Test API image processing"""
    print("🎨 Testing ImageMagick API with Authentication")
    print("=" * 50)
    
    # Create test image if it doesn't exist
    test_image = "test_image.png"
    if not os.path.exists(test_image):
        test_image = create_test_image()
    
    headers = {'X-API-Key': API_KEY}
    
    # Test different operations
    operations = [
        {
            'action': 'text',
            'text': 'API Works!',
            'text_color': 'red',
            'text_size': '150',
            'text_position': 'Center'
        },
        {
            'action': 'resize',
            'resize_percentage': '75'
        },
        {
            'action': 'grayscale'
        },
        {
            'action': 'sepia'
        }
    ]
    
    for i, params in enumerate(operations, 1):
        print(f"\n🔄 Test {i}: {params['action'].title()}")
        
        try:
            with open(test_image, 'rb') as img_file:
                files = {'image': img_file}
                
                response = requests.post(
                    f"{API_BASE_URL}/process",
                    files=files,
                    data=params,
                    headers=headers
                )
            
            if response.status_code == 200:
                output_file = f"output_{params['action']}_{i}.png"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ Success! Saved to: {output_file}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n🎉 API testing completed!")
    print(f"📂 Check the generated output files in the current directory")

if __name__ == "__main__":
    try:
        test_api_processing()
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure the Flask server is running and API_KEY is valid")
