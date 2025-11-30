import json
import os
import httpx
from openai import OpenAI

# Load config
config_path = os.path.join(os.path.dirname(__file__), 'llm_config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

client = OpenAI(
    api_key=config['llm_api_key'],
    base_url=config['llm_base_url']
)

def test_chat():
    print("\n--- Testing Text Chat (OpenAI: gpt-5-chat-latest) ---")
    try:
        response = client.chat.completions.create(
            model="gpt-5-chat-latest",
            messages=[{"role": "user", "content": "Hello, introduce yourself briefly."}]
        )
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Error: {e}")

def test_search():
    print("\n--- Testing Search/Knowledge (Gemini: gemini-3-pro-preview-search) ---")
    try:
        # Using the specific model found in the list that supports search
        model_name = "gemini-3-pro-preview-search"
        print(f"Using model: {model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "What is the current date and what are the major tech news headlines today?"}]
        )
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Error: {e}")

def test_image_generation():
    print("\n--- Testing Image Generation (dall-e-3) ---")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt="A cute robot painting a landscape on a canvas, digital art style",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        print(f"Image URL: {image_url}")
        
        # Save image
        if image_url:
            images_dir = os.path.join(os.path.dirname(__file__), 'images')
            os.makedirs(images_dir, exist_ok=True)
            image_path = os.path.join(images_dir, 'generated_robot.png')
            
            with httpx.Client() as http_client:
                img_response = http_client.get(image_url)
                with open(image_path, "wb") as f:
                    f.write(img_response.content)
            print(f"Image saved to {image_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
    test_search()
    test_image_generation()
