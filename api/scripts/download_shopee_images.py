#!/usr/bin/env python3
"""
Script para baixar imagens de anúncios da Shopee via Playwright (headless).
Uso: python download_shopee_images.py <URL_DO_ANUNCIO>
"""

import os
import re
import sys
import time
import requests
from playwright.sync_api import sync_playwright


def extract_ids_from_url(url: str) -> tuple[str, str]:
    """Extrai shop_id e item_id da URL da Shopee (suporta múltiplos formatos)."""
    # Formato 1: ...i.123456.789012
    match = re.search(r'i\.(\d+)\.(\d+)', url)
    if match:
        return match.group(1), match.group(2)
    # Formato 2: /product/123456/789012
    match = re.search(r'/product/(\d+)/(\d+)', url)
    if match:
        return match.group(1), match.group(2)
    raise ValueError(f"Não foi possível extrair shop_id e item_id da URL: {url}")


def get_high_res_url(url: str) -> str:
    """Converte URL de thumbnail para alta resolução."""
    # Remove sufixos de redimensionamento como _tn, _thumbnail, etc.
    url = re.sub(r'_tn\b', '', url)
    # Remove parâmetros de query que limitam tamanho
    url = re.sub(r'\?.*$', '', url)
    return url


# Tamanho mínimo em KB para considerar como imagem de produto (filtrar ícones de UI)
MIN_IMAGE_SIZE_KB = 50


def download_image(url: str, filepath: str) -> int:
    """Baixa uma imagem e salva no caminho especificado. Retorna tamanho em bytes ou 0 se falhar."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://shopee.com.br/',
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return len(response.content)
    except Exception as e:
        print(f"  ❌ Erro ao baixar {url}: {e}")
        return 0


def scrape_shopee_images(url: str, output_dir: str = None):
    """
    Abre a página da Shopee com Playwright headless,
    extrai URLs das imagens do produto e baixa todas.
    """
    shop_id, item_id = extract_ids_from_url(url)
    print(f"🔍 Shop ID: {shop_id} | Item ID: {item_id}")

    # Define pasta de saída
    if output_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "shopee_downloads", item_id)

    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Pasta de saída: {output_dir}")

    print("🌐 Abrindo página com Playwright (headless)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
        )

        page = context.new_page()

        # Bloquear recursos desnecessários para acelerar
        def route_handler(route):
            resource_type = route.request.resource_type
            if resource_type in ['font', 'media', 'websocket']:
                route.abort()
            else:
                route.fallback()

        page.route("**/*", route_handler)

        try:
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            print("⏳ Aguardando carregamento das imagens...")

            # Esperar as imagens do produto carregarem
            # Tenta múltiplos seletores possíveis
            selectors = [
                'div[class*="product-image"] img',
                'div[class*="image-carousel"] img',
                'div[class*="flex-column"] img[src*="susercontent"]',
                'img[src*="down-br.img.susercontent.com"]',
                'img[src*="susercontent.com"]',
            ]

            # Aguardar pelo menos uma imagem do CDN aparecer
            page.wait_for_selector(
                'img[src*="susercontent.com"]',
                timeout=15000
            )

            # Dar tempo extra para todas as imagens carregarem
            time.sleep(3)

            # Scrollar para carregar lazy images
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(1)

            # Coletar todas as imagens do CDN
            image_urls = set()

            for selector in selectors:
                elements = page.query_selector_all(selector)
                for el in elements:
                    src = el.get_attribute('src')
                    if src and 'susercontent.com' in src:
                        image_urls.add(src)

                    # Também checar data-src (lazy loading)
                    data_src = el.get_attribute('data-src')
                    if data_src and 'susercontent.com' in data_src:
                        image_urls.add(data_src)

            # Também buscar em background-image de divs
            bg_elements = page.evaluate("""
                () => {
                    const urls = [];
                    document.querySelectorAll('[style*="background-image"]').forEach(el => {
                        const style = el.getAttribute('style');
                        const match = style.match(/url\\(["']?(https?:\\/\\/[^"')]+susercontent[^"')]+)["']?\\)/);
                        if (match) urls.push(match[1]);
                    });
                    return urls;
                }
            """)
            for bg_url in bg_elements:
                image_urls.add(bg_url)

            # Buscar via JS no DOM completo
            all_img_urls = page.evaluate("""
                () => {
                    const urls = [];
                    document.querySelectorAll('img').forEach(img => {
                        const src = img.src || img.dataset.src || '';
                        if (src.includes('susercontent.com') && !src.includes('icon') && !src.includes('favicon')) {
                            urls.push(src);
                        }
                    });
                    return urls;
                }
            """)
            for img_url in all_img_urls:
                image_urls.add(img_url)

        except Exception as e:
            print(f"⚠️  Erro durante scraping: {e}")
            # Tentar capturar o que tiver disponível
            all_img_urls = page.evaluate("""
                () => {
                    const urls = [];
                    document.querySelectorAll('img').forEach(img => {
                        const src = img.src || '';
                        if (src.includes('susercontent.com')) urls.push(src);
                    });
                    return urls;
                }
            """)
            image_urls = set(all_img_urls)
        finally:
            browser.close()

    if not image_urls:
        print("❌ Nenhuma imagem encontrada! A Shopee pode estar bloqueando ou a página mudou.")
        return

    # Filtrar para pegar apenas imagens do produto (não ícones, logos, etc.)
    # Imagens de produto geralmente são maiores e contêm hashes no path
    product_images = []
    for img_url in image_urls:
        # Ignorar imagens muito pequenas (ícones, thumbnails de UI)
        if any(x in img_url for x in ['icon', 'logo', 'avatar', 'badge', 'flag', 'banner',
                                        '20x20', '24x24', '32x32', '40x40', '48x48',
                                        'rating_star', 'shopee-logo']):
            continue
        product_images.append(get_high_res_url(img_url))

    # Remover duplicatas mantendo ordem
    seen = set()
    unique_images = []
    for img in product_images:
        # Normalizar URL para detectar duplicatas
        base = img.split('?')[0].rstrip('/')
        if base not in seen:
            seen.add(base)
            unique_images.append(img)

    print(f"\n📸 Encontradas {len(unique_images)} imagens do produto")
    print("-" * 50)

    # Baixar cada imagem em pasta temporária para filtrar depois
    temp_files = []  # (filepath, size_bytes)
    for i, img_url in enumerate(unique_images, 1):
        # Determinar extensão
        ext = '.jpg'
        if '.png' in img_url:
            ext = '.png'
        elif '.webp' in img_url:
            ext = '.webp'

        filename = f"_temp_{i:02d}{ext}"
        filepath = os.path.join(output_dir, filename)

        size = download_image(img_url, filepath)
        if size > 0:
            temp_files.append((filepath, size, ext))

    # Filtrar: manter apenas imagens maiores que MIN_IMAGE_SIZE_KB
    min_bytes = MIN_IMAGE_SIZE_KB * 1024
    kept = [(fp, sz, ext) for fp, sz, ext in temp_files if sz >= min_bytes]
    removed = [(fp, sz, ext) for fp, sz, ext in temp_files if sz < min_bytes]

    # Remover arquivos pequenos (ícones de UI)
    for fp, sz, _ in removed:
        os.remove(fp)

    # Renumerar os arquivos mantidos sequencialmente
    final_count = 0
    for i, (fp, sz, ext) in enumerate(kept, 1):
        new_name = f"shopee_{item_id}_{i:02d}{ext}"
        new_path = os.path.join(output_dir, new_name)
        os.rename(fp, new_path)
        size_kb = sz / 1024
        print(f"  ✅ {new_name} ({size_kb:.1f} KB)")
        final_count += 1

    print("-" * 50)
    if removed:
        print(f"🗑️  Removidas {len(removed)} imagens pequenas (ícones/thumbnails de UI < {MIN_IMAGE_SIZE_KB}KB)")
    print(f"✅ Download concluído! {final_count} imagens do produto salvas em:")
    print(f"   {output_dir}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python download_shopee_images.py <URL_DO_ANUNCIO>")
        print("Exemplo: python download_shopee_images.py 'https://shopee.com.br/...-i.123456.789012'")
        sys.exit(1)

    url = sys.argv[1]
    scrape_shopee_images(url)
