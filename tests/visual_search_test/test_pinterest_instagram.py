"""
Teste isolado: Playwright headless → Pinterest + Instagram
Objetivo: ver o que conseguimos extrair de referências visuais de moda brasileira
"""
import asyncio
import json
import os
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output_social")
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def test_pinterest():
    """Testa busca no Pinterest por referências de moda brasileira."""
    from playwright.async_api import async_playwright
    
    print("\n" + "=" * 60)
    print("🔴 TESTE PINTEREST")
    print("=" * 60)
    
    results = {
        "plataforma": "pinterest",
        "timestamp": datetime.now().isoformat(),
        "buscas": []
    }
    
    queries = [
        "modelo brasileira moda casual e-commerce",
        "look feminino casual brasileiro shopee",
        "influencer brasileira moda street style",
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = await context.new_page()
        
        for i, query in enumerate(queries):
            print(f"\n  🔍 Busca {i+1}: '{query}'")
            search_result = {
                "query": query,
                "status": "pending",
                "pins_encontrados": 0,
                "dados_extraidos": [],
                "screenshot": None,
                "erro": None
            }
            
            try:
                url = f"https://br.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
                await page.goto(url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(2000)
                
                # Fecha modal de login do Pinterest
                try:
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(500)
                except:
                    pass
                try:
                    # Remove modal via JS
                    await page.evaluate("""
                        () => {
                            // Remove overlays de login
                            document.querySelectorAll('[data-test-id="loginForm"], [role="dialog"], .Modal, .Closeup').forEach(el => el.remove());
                            // Remove backdrop/overlay escuro
                            document.querySelectorAll('[data-test-id="modal-overlay"], .OverlayBackground, div[style*="position: fixed"]').forEach(el => {
                                if (el.textContent.includes('login') || el.textContent.includes('Entrar') || el.textContent.includes('Criar conta')) {
                                    el.remove();
                                }
                            });
                            // Remove qualquer overlay fixo que cubra tudo
                            document.querySelectorAll('div[style*="z-index"]').forEach(el => {
                                const z = parseInt(getComputedStyle(el).zIndex);
                                if (z > 100 && (el.textContent.includes('login') || el.textContent.includes('Email'))) {
                                    el.remove();
                                }
                            });
                            document.body.style.overflow = 'auto';
                        }
                    """)
                    await page.wait_for_timeout(500)
                except:
                    pass
                
                # Screenshot LIMPO
                ss_path = os.path.join(OUTPUT_DIR, f"pinterest_busca_{i+1}.png")
                await page.screenshot(path=ss_path, full_page=False)
                search_result["screenshot"] = ss_path
                print(f"  📸 Screenshot salvo: {ss_path}")
                
                # Verifica login wall
                login_wall = await page.query_selector('[data-test-id="loginForm"]')
                if login_wall:
                    search_result["status"] = "login_wall"
                    search_result["erro"] = "Pinterest exige login"
                    print(f"  ❌ Login wall detectada")
                    continue
                
                # Tenta extrair pins
                pins = await page.query_selector_all('[data-test-id="pin"]')
                if not pins:
                    # Tenta seletores alternativos
                    pins = await page.query_selector_all('[role="listitem"]')
                if not pins:
                    pins = await page.query_selector_all('div[data-grid-item]')
                
                search_result["pins_encontrados"] = len(pins)
                print(f"  📌 {len(pins)} pins encontrados")
                
                # Extrai dados dos primeiros 10 pins
                for j, pin in enumerate(pins[:10]):
                    pin_data = {}
                    
                    # Imagem
                    img = await pin.query_selector("img")
                    if img:
                        pin_data["img_src"] = await img.get_attribute("src")
                        pin_data["img_alt"] = await img.get_attribute("alt")
                    
                    # Link
                    link = await pin.query_selector("a")
                    if link:
                        pin_data["href"] = await link.get_attribute("href")
                    
                    # Texto
                    text = await pin.inner_text()
                    if text and len(text.strip()) > 0:
                        pin_data["texto"] = text.strip()[:200]
                    
                    if pin_data:
                        search_result["dados_extraidos"].append(pin_data)
                
                # Tenta JS extraction como fallback
                js_data = await page.evaluate("""
                    () => {
                        const imgs = document.querySelectorAll('img[src*="pinimg"]');
                        return Array.from(imgs).slice(0, 15).map(img => ({
                            src: img.src,
                            alt: img.alt || '',
                            width: img.naturalWidth,
                            height: img.naturalHeight
                        }));
                    }
                """)
                
                if js_data:
                    search_result["imagens_pinimg"] = len(js_data)
                    search_result["amostras_imagens"] = js_data[:5]
                    print(f"  🖼️  {len(js_data)} imagens pinimg extraídas via JS")
                
                search_result["status"] = "sucesso"
                
                # Extrai texto visível da página
                page_text = await page.evaluate("""
                    () => {
                        const texts = [];
                        document.querySelectorAll('div, span, p, h1, h2, h3').forEach(el => {
                            const t = el.textContent?.trim();
                            if (t && t.length > 10 && t.length < 200 && !texts.includes(t)) {
                                texts.push(t);
                            }
                        });
                        return texts.slice(0, 20);
                    }
                """)
                search_result["textos_pagina"] = page_text[:10]
                
            except Exception as e:
                search_result["status"] = "erro"
                search_result["erro"] = str(e)
                print(f"  ❌ Erro: {e}")
            
            results["buscas"].append(search_result)
        
        await browser.close()
    
    # Salva resultados
    out_path = os.path.join(OUTPUT_DIR, "pinterest_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 Resultados salvos: {out_path}")
    
    return results


async def test_instagram():
    """Testa acesso a perfis de Instagram de marcas/influencers brasileiras."""
    from playwright.async_api import async_playwright
    
    print("\n" + "=" * 60)
    print("📷 TESTE INSTAGRAM")
    print("=" * 60)
    
    results = {
        "plataforma": "instagram",
        "timestamp": datetime.now().isoformat(),
        "perfis": []
    }
    
    profiles = [
        {"url": "https://www.instagram.com/lojasrenner/", "nome": "Lojas Renner"},
        {"url": "https://www.instagram.com/amfrfrm/", "nome": "AMFR"},
        {"url": "https://www.instagram.com/cea_brasil/", "nome": "C&A Brasil"},
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = await context.new_page()
        
        for i, profile in enumerate(profiles):
            print(f"\n  👤 Perfil {i+1}: {profile['nome']} ({profile['url']})")
            profile_result = {
                "nome": profile["nome"],
                "url": profile["url"],
                "status": "pending",
                "bio": None,
                "seguidores": None,
                "posts_visiveis": 0,
                "imagens_extraidas": [],
                "screenshot": None,
                "erro": None
            }
            
            try:
                await page.goto(profile["url"], wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(2000)
                
                # Fecha modal de login/cadastro do Instagram
                try:
                    # Tenta clicar no X do modal
                    close_btn = await page.query_selector('[aria-label="Fechar"], [aria-label="Close"], button svg[aria-label="Fechar"]')
                    if close_btn:
                        await close_btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass
                try:
                    # Remove modal via JS
                    await page.evaluate("""
                        () => {
                            document.querySelectorAll('[role="dialog"], [role="presentation"]').forEach(el => {
                                if (el.textContent.includes('Cadastre-se') || el.textContent.includes('Entrar') || el.textContent.includes('login')) {
                                    el.remove();
                                }
                            });
                            // Remove backdrop escuro
                            document.querySelectorAll('div[style*="position: fixed"]').forEach(el => el.remove());
                            document.body.style.overflow = 'auto';
                        }
                    """)
                    await page.wait_for_timeout(500)
                except:
                    pass
                
                # Screenshot LIMPO
                ss_path = os.path.join(OUTPUT_DIR, f"instagram_perfil_{i+1}.png")
                await page.screenshot(path=ss_path, full_page=False)
                profile_result["screenshot"] = ss_path
                print(f"  📸 Screenshot salvo: {ss_path}")
                
                # Verifica login wall
                login_form = await page.query_selector('input[name="username"]')
                login_text = await page.query_selector('text="Entrar"')
                
                current_url = page.url
                if "accounts/login" in current_url:
                    profile_result["status"] = "login_redirect"
                    profile_result["erro"] = "Redirecionado para login"
                    print(f"  ❌ Redirecionado para login")
                    continue
                
                # Tenta extrair dados do perfil
                js_data = await page.evaluate("""
                    () => {
                        const data = {};
                        
                        // Bio
                        const bioEl = document.querySelector('div.-vDIg span, section > div > span');
                        if (bioEl) data.bio = bioEl.textContent;
                        
                        // Meta tags (geralmente acessíveis)
                        const metaDesc = document.querySelector('meta[property="og:description"]');
                        if (metaDesc) data.og_description = metaDesc.content;
                        
                        const metaTitle = document.querySelector('meta[property="og:title"]');
                        if (metaTitle) data.og_title = metaTitle.content;
                        
                        const metaImage = document.querySelector('meta[property="og:image"]');
                        if (metaImage) data.og_image = metaImage.content;
                        
                        // Imagens
                        const imgs = document.querySelectorAll('img');
                        data.total_images = imgs.length;
                        data.image_samples = Array.from(imgs).slice(0, 10).map(img => ({
                            src: img.src,
                            alt: img.alt || ''
                        }));
                        
                        // Texto da página
                        data.page_title = document.title;
                        
                        // Links
                        const links = document.querySelectorAll('a[href*="/p/"]');
                        data.post_links = Array.from(links).slice(0, 5).map(a => a.href);
                        
                        return data;
                    }
                """)
                
                profile_result["dados_extraidos"] = js_data
                profile_result["posts_visiveis"] = len(js_data.get("post_links", []))
                profile_result["status"] = "sucesso" if js_data.get("total_images", 0) > 0 else "parcial"
                
                print(f"  📊 {js_data.get('total_images', 0)} imagens, {len(js_data.get('post_links', []))} links de posts")
                if js_data.get("og_description"):
                    print(f"  📝 OG: {js_data['og_description'][:100]}...")
                
            except Exception as e:
                profile_result["status"] = "erro"
                profile_result["erro"] = str(e)
                print(f"  ❌ Erro: {e}")
            
            results["perfis"].append(profile_result)
        
        # Teste extra: hashtag de moda
        print(f"\n  #️⃣ Testando hashtag: #modafemininabrasileira")
        hashtag_result = {"tipo": "hashtag", "status": "pending"}
        try:
            await page.goto("https://www.instagram.com/explore/tags/modafemininabrasileira/", 
                          wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(3000)
            ss_path = os.path.join(OUTPUT_DIR, "instagram_hashtag.png")
            await page.screenshot(path=ss_path, full_page=False)
            
            current_url = page.url
            hashtag_result["url_final"] = current_url
            hashtag_result["redirecionou_login"] = "accounts/login" in current_url
            hashtag_result["screenshot"] = ss_path
            
            if "accounts/login" not in current_url:
                js_data = await page.evaluate("""
                    () => ({
                        images: document.querySelectorAll('img').length,
                        title: document.title,
                        post_links: Array.from(document.querySelectorAll('a[href*="/p/"]')).slice(0, 5).map(a => a.href)
                    })
                """)
                hashtag_result["dados"] = js_data
                hashtag_result["status"] = "sucesso"
            else:
                hashtag_result["status"] = "login_required"
                print(f"  ❌ Hashtag requer login")
                
        except Exception as e:
            hashtag_result["status"] = "erro"
            hashtag_result["erro"] = str(e)
        
        results["hashtag_test"] = hashtag_result
        await browser.close()
    
    # Salva resultados
    out_path = os.path.join(OUTPUT_DIR, "instagram_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 Resultados salvos: {out_path}")
    
    return results


async def main():
    print("=" * 60)
    print("🧪 TESTE ISOLADO: Playwright Headless → Pinterest + Instagram")
    print(f"   {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    pinterest = await test_pinterest()
    instagram = await test_instagram()
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    
    print("\n  PINTEREST:")
    for b in pinterest["buscas"]:
        print(f"    '{b['query']}' → {b['status']} | {b['pins_encontrados']} pins | {len(b.get('dados_extraidos', []))} dados")
    
    print("\n  INSTAGRAM:")
    for p in instagram["perfis"]:
        print(f"    {p['nome']} → {p['status']} | {p.get('posts_visiveis', 0)} posts | erro: {p.get('erro', 'nenhum')}")
    
    ht = instagram.get("hashtag_test", {})
    print(f"    #hashtag → {ht.get('status', '?')}")


if __name__ == "__main__":
    asyncio.run(main())
