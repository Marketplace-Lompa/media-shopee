import os
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from google import genai

load_dotenv(".env")

api_key = os.getenv("GOOGLE_AI_API_KEY")
client = genai.Client(api_key=api_key)

TARGET_DIR = "/Users/lompa-marketplace/Documents/Ecommerce/Shopee/Tricot Oversized"
target_path = Path(TARGET_DIR)

color_counts = {}

print("Iniciando organização por cor...")

for file_path in target_path.iterdir():
    if file_path.is_file() and file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
        # Ignorar se já tiver sido renomeada (aqui não teria 'shopee_')
        if not file_path.name.startswith("shopee_"):
            continue

        try:
            img = Image.open(file_path)
            # Resize a bit to save bandwidth/tokens
            img.thumbnail((512, 512))
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    img, 
                    "Look at the main piece of clothing being modeled/displayed. What is its main color? Reply ONLY with ONE single standardized color word in Portuguese, lowercase (e.g. branco, preto, marsala, pink, marrom, cinza, vermelho, off-white, verde)."
                ],
                config={"temperature": 0.0}
            )
            color = response.text.strip().lower()
            # Clean up potential punctuation
            color = color.replace(".", "").replace(",", "")
            
            print(f"{file_path.name} -> {color}")
            
            count = color_counts.get(color, 0) + 1
            color_counts[color] = count
            
            new_name = f"{color}_{count}{file_path.suffix.lower()}"
            if count == 1:
                new_name = f"{color}{file_path.suffix.lower()}"
                
            new_path = target_path / new_name
            # Para evitar conflito caso "branco.jpg" já exista na iteração
            while new_path.exists():
                count += 1
                color_counts[color] = count
                new_name = f"{color}_{count}{file_path.suffix.lower()}"
                new_path = target_path / new_name
                
            file_path.rename(new_path)
            print(f"  Renomeado para: {new_name}")
            
        except Exception as e:
            print(f"Erro em {file_path.name}: {e}")

print("Concluído!")
