---
description: Regra de Diretório Padrão de Testes para Imagens (Tecnologia Nano Banana)
---

# Regra de Uso de Referências para Testes

Quando o usuário solicitar testes de geração de imagem utilizando o Nano Banana Pro (ou qualquer modelo do ecossistema Gemini Focus/Image dentro deste projeto) e houver a necessidade de analisar referências de roupas ou inputar fotos de contexto para a IA:

- **DIRETÓRIO OBRIGATÓRIO:** Todas as imagens de teste devem, obrigatoriamente, ser lidas do diretório fixo:
  `/Users/lompa-marketplace/Documents/MEDIA-SHOPEE/docs/roupa-referencia-teste`
  
- **USO ESTRITO:** Não utilize imagens da pasta `output/`, `.tmp` ou quaisquer outros diretórios temporários na área de "app/tests/", a menos que explicitamente ordenado de forma contrária numa sessão específica. Se o usuário falar de "imagens de teste" ou "pegar a imagem X para testar o Nano", busque primariamente neste diretório.

- **FALHA (FALLBACK):** Caso o diretório esteja vazio quando requisitado num script, o teste deve printar/retornar um erro alertando o usuário: "Atenção: A pasta /docs/roupa-referencia-teste está vazia. Adicione as imagens de vestuário desejadas antes de executar a geração."
