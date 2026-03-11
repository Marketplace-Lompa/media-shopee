import os
import sys
import pprint

# Ativar a busca de imagens visuais
os.environ["GROUNDING_VISUAL_IMAGES"] = "html"

# Adicionar o backend ao sys.path para conseguirmos importar
sys.path.append(os.path.join(os.path.dirname(__file__), "app", "backend"))

from agent_runtime.grounding import _run_grounding_research

def test_grounding():
    print("Iniciando Grounding no Modo FULL COM IMAGEM REAL...")
    
    image_path = "/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/api/scripts/shopee_downloads/18498778728/shopee_18498778728_01.jpg"
    
    # carregar a imagem real
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Executar a pesquisa profunda (grounding) COM a imagem real e SEM dica forçada
    result = _run_grounding_research(
        uploaded_images=[image_bytes], 
        user_prompt="", # Deixando o agente inferir da imagem
        mode="full"
    )
    
    print("\n" + "="*50)
    print("RESULTADO DO GROUNDING:")
    print("="*50)
    
    # Mostrar quantas imagens baixou
    images = result.pop("grounded_images", [])
    print(f"✅ Imagens baixadas: {len(images)}")
    
    # Mostrar texto gerado e metadados
    print("\nMetadados:")
    pprint.pprint(result)

if __name__ == "__main__":
    test_grounding()
