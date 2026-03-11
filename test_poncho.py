import httpx
import sys
import os

API_URL = "http://127.0.0.1:8000/generate"

def test_poncho():
    image_path = "/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/app/tests/output/poncho-teste/IMG_3321.jpg"
    
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return
        
    print(f"Testing generation with image: {image_path}")
    
    # We will use mode 2: image only, no prompt text.
    with open(image_path, "rb") as f:
        files = {
            "images": (os.path.basename(image_path), f, "image/jpeg")
        }
        data = {
            "prompt": "",
            "mode": "2",
            "aspect_ratio": "3:4"
        }
        
        with httpx.Client(timeout=300) as client:
            response = client.post(API_URL, data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("\n=== SUCCESS ===")
                print(f"Generated text: {result.get('optimized_prompt', '')}")
                print(f"Image analysis: {result.get('image_analysis', '')}")
                print(f"Garment Aesthetic: {result.get('garment_aesthetic', '')}")
                print(f"Profile used: {result.get('profile_used', '')}")
                print(f"Failed indices: {result.get('failed_indices', [])}")
                
                # Check for image saved in the results
                # The response typically contains generated_images list
                images = result.get("images", [])
                print(f"Generated {len(images)} images.")
                for img in images:
                    print(f"Image path: {img.get('path', 'unknown')}")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)

if __name__ == "__main__":
    test_poncho()
