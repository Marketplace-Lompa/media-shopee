import asyncio
from generator import generate_images

def test_gen():
    try:
        res = generate_images(
            prompt="A beautiful cat", 
            thinking_level="MINIMAL", 
            aspect_ratio="1:1", 
            resolution="1K", 
            n_images=1
        )
        print("SUCCESS:", len(res))
    except Exception as e:
        print("ERROR:", repr(e))

if __name__ == "__main__":
    test_gen()
