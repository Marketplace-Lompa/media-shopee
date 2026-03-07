#!/usr/bin/env python3
"""
publicar-shopee.py — Automação da Shopee Seller Center via Playwright CDP.

Conecta ao Chrome REAL já logado (via --remote-debugging-port=9222),
navega para a Seller Center e cria um rascunho de produto passo a passo.

Uso:
    python3 publicar-shopee.py --config produto.json --cor vermelho [--publicar]

Flags:
    --config    Caminho para o arquivo produto.json
    --cor       Cor a publicar (deve coincidir com subpasta criada pelo analisa-fotos.py)
    --publicar  Se presente, tenta publicar. Sem a flag, SALVA COMO RASCUNHO.
    --dry-run   Navega e preenche mas NÃO salva nem publica. Gera screenshots.
    --port      Porta do CDP (padrão: 9222)
    --debug     Mostra mais detalhes no terminal
"""

import os
import sys
import json
import time
import random
import argparse
import traceback
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("❌ Playwright não instalado. Rode: pip3 install playwright")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────────────────────────

SELLER_CENTER_URL = "https://seller.shopee.com.br"
ADICIONAR_PRODUTO_URL = f"{SELLER_CENTER_URL}/portal/product/add"
MAX_FOTOS = 9        # Shopee permite até 9 fotos por anúncio
AUDIT_DIR = "/tmp/shopee-audit"
DELAY_MIN = 1.0      # segundos mínimos entre ações
DELAY_MAX = 2.5      # segundos máximos entre ações


def delay(min_s: float = DELAY_MIN, max_s: float = DELAY_MAX):
    """Pausa humanizada entre ações para evitar detecção de bot."""
    time.sleep(random.uniform(min_s, max_s))


def screenshot(page, nome: str, audit_dir: str):
    """Salva screenshot de auditoria."""
    os.makedirs(audit_dir, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    caminho = os.path.join(audit_dir, f"{ts}_{nome}.png")
    page.screenshot(path=caminho, full_page=False)
    print(f"   📸 Screenshot: {caminho}")
    return caminho


def log(msg: str, debug: bool = False, is_debug: bool = False):
    """Log condicional."""
    if is_debug and not debug:
        return
    prefix = "   🔍" if is_debug else "  "
    print(f"{prefix} {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

def carregar_config(caminho_config: str, cor: str) -> dict:
    """Carrega e valida o produto.json."""
    p = Path(caminho_config)
    if not p.exists():
        print(f"❌ Arquivo de configuração não encontrado: {caminho_config}")
        sys.exit(1)

    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)

    obrigatorios = ["nome_base", "preco", "pasta_fotos"]
    for campo in obrigatorios:
        if campo not in cfg:
            print(f"❌ Campo obrigatório ausente no produto.json: '{campo}'")
            sys.exit(1)

    # Valida pasta de fotos para a cor específica
    pasta_fotos = Path(cfg["pasta_fotos"]) / cor
    if not pasta_fotos.exists():
        print(f"❌ Pasta de fotos para '{cor}' não encontrada: {pasta_fotos}")
        print(f"   Execute primeiro: python3 analisa-fotos.py {cfg['pasta_fotos']}")
        sys.exit(1)

    cfg["_pasta_cor"] = str(pasta_fotos)
    cfg["_cor_atual"] = cor

    # Nome completo inclui a cor
    nome_cor_display = cor.capitalize()
    cfg["_nome_completo"] = cfg["nome_base"].strip()
    if cor.lower() not in cfg["nome_base"].lower():
        cfg["_nome_completo"] += f" {nome_cor_display}"

    return cfg


def listar_fotos_para_upload(cfg: dict) -> list[str]:
    """Lista fotos da subpasta da cor, respeitando o limite de 9."""
    pasta = Path(cfg["_pasta_cor"])
    extensoes = {".jpg", ".jpeg", ".png", ".webp"}
    fotos = sorted([
        str(f) for f in pasta.iterdir()
        if f.is_file() and f.suffix.lower() in extensoes
    ])
    if len(fotos) > MAX_FOTOS:
        print(f"   ⚠️  {len(fotos)} fotos encontradas. Usando as primeiras {MAX_FOTOS}.")
        fotos = fotos[:MAX_FOTOS]
    print(f"   📸 {len(fotos)} foto(s) para upload: {pasta}")
    return fotos


# ─────────────────────────────────────────────────────────────────────────────
# CONEXÃO COM CHROME
# ─────────────────────────────────────────────────────────────────────────────

def conectar_chrome(port: int = 9222):
    """Conecta ao Chrome real via CDP."""
    cdp_url = f"http://localhost:{port}"
    print(f"\n🔗 Conectando ao Chrome via CDP: {cdp_url}")

    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.connect_over_cdp(cdp_url)
    except Exception as e:
        print(f"\n❌ Não foi possível conectar ao Chrome na porta {port}.")
        print("   Verifique se o Chrome está rodando com:")
        print(f'   open -a "Google Chrome" --args --remote-debugging-port={port}')
        print(f"   Erro: {e}")
        playwright.stop()
        sys.exit(1)

    # Usar contexto existente (com cookies/sessão)
    contextos = browser.contexts
    if not contextos:
        print("❌ Nenhum contexto de browser encontrado. O Chrome está logado?")
        browser.close()
        playwright.stop()
        sys.exit(1)

    context = contextos[0]
    print(f"✅ Conectado! {len(context.pages)} página(s) abertas.")
    return playwright, browser, context


# ─────────────────────────────────────────────────────────────────────────────
# FLUXO DE CRIAÇÃO DO PRODUTO
# ─────────────────────────────────────────────────────────────────────────────

def navegar_para_adicionar_produto(page, audit_dir: str):
    """Navega para a página de adicionar produto na Seller Center."""
    print("\n📍 ETAPA 1: Navegando para Adicionar Produto...")
    page.goto(ADICIONAR_PRODUTO_URL, wait_until="domcontentloaded", timeout=30000)
    delay(2, 4)
    screenshot(page, "01_pagina_adicionar", audit_dir)
    print("   ✅ Página de cadastro aberta.")


def preencher_nome(page, cfg: dict, audit_dir: str):
    """Preenche o nome do produto."""
    print("\n📝 ETAPA 2: Preenchendo nome do produto...")
    nome = cfg["_nome_completo"]
    if len(nome) > 120:
        nome = nome[:120]
        print(f"   ⚠️  Nome truncado para 120 chars.")

    seletores_nome = [
        'input[placeholder*="nome"]',
        'input[placeholder*="Nome"]',
        'input[placeholder*="product name"]',
        'textarea[placeholder*="nome"]',
        '[data-testid="product-name-input"] input',
        '.product-name input',
        'input[name="name"]',
    ]

    campo = None
    for sel in seletores_nome:
        try:
            campo = page.wait_for_selector(sel, timeout=3000)
            if campo:
                break
        except PlaywrightTimeout:
            continue

    if not campo:
        print("   ⚠️  Campo nome não encontrado automaticamente. Tentando clique por posição...")
        # Fallback: primeiro campo de texto grande visível
        campos = page.query_selector_all('input[type="text"]')
        if campos:
            campo = campos[0]

    if campo:
        campo.click()
        delay(0.3, 0.7)
        campo.fill("")
        campo.type(nome, delay=30)
        delay()
        print(f"   ✅ Nome preenchido: {nome}")
        screenshot(page, "02_nome_preenchido", audit_dir)
    else:
        print("   ❌ Campo nome não encontrado. Prosseguindo...")


def fazer_upload_fotos(page, fotos: list[str], audit_dir: str):
    """Faz upload das fotos do produto."""
    print(f"\n🖼️  ETAPA 3: Upload de {len(fotos)} foto(s)...")

    # Seletores comuns de input de arquivo na Shopee Seller Center
    seletores_upload = [
        'input[type="file"][accept*="image"]',
        'input[type="file"]',
    ]

    input_file = None
    for sel in seletores_upload:
        try:
            input_file = page.query_selector(sel)
            if input_file:
                break
        except Exception:
            continue

    if not input_file:
        print("   ⚠️  Input de arquivo não encontrado diretamente.")
        print("   Tentando clicar na área de upload...")
        areas_upload = [
            'div[class*="upload"]',
            'div[class*="image-upload"]',
            'label[class*="upload"]',
            '.upload-btn',
            '.image-add',
        ]
        for sel in areas_upload:
            try:
                area = page.query_selector(sel)
                if area:
                    area.click()
                    delay()
                    input_file = page.query_selector('input[type="file"]')
                    if input_file:
                        break
            except Exception:
                continue

    if input_file:
        for i, foto in enumerate(fotos, 1):
            print(f"   [{i}/{len(fotos)}] Enviando: {Path(foto).name}")
            try:
                with page.expect_file_chooser() as fc_info:
                    input_file.click()
                file_chooser = fc_info.value
                file_chooser.set_files(foto)
                delay(1.5, 3.0)  # aguardar upload
            except Exception:
                # Fallback: set_input_files direto
                try:
                    input_file.set_input_files(foto)
                    delay(1.5, 3.0)
                except Exception as e2:
                    print(f"   ❌ Falha no upload da foto {i}: {e2}")
        delay(2, 4)
        screenshot(page, "03_fotos_enviadas", audit_dir)
        print("   ✅ Upload concluído.")
    else:
        print("   ❌ Área de upload não encontrada. Upload manual necessário.")
        screenshot(page, "03_upload_falhou", audit_dir)


def preencher_preco_estoque(page, cfg: dict, cor: str, audit_dir: str):
    """Preenche preço e estoque."""
    print("\n💰 ETAPA 4: Preenchendo preço e estoque...")

    preco = cfg.get("preco", 0)
    estoque_por_cor = cfg.get("estoque_por_cor", {})
    estoque = estoque_por_cor.get(cor, cfg.get("estoque", 10))

    # Preço
    seletores_preco = [
        'input[placeholder*="preço"]',
        'input[placeholder*="Preço"]',
        'input[placeholder*="price"]',
        'input[placeholder*="Price"]',
        '[data-testid="price-input"] input',
        'input[name="price"]',
    ]
    for sel in seletores_preco:
        try:
            campo = page.wait_for_selector(sel, timeout=2000)
            if campo:
                campo.click()
                delay(0.3)
                campo.fill(str(preco))
                print(f"   ✅ Preço: R$ {preco}")
                break
        except PlaywrightTimeout:
            continue

    delay()

    # Estoque
    seletores_estoque = [
        'input[placeholder*="estoque"]',
        'input[placeholder*="Estoque"]',
        'input[placeholder*="stock"]',
        'input[placeholder*="Stock"]',
        'input[placeholder*="quantidade"]',
        '[data-testid="stock-input"] input',
        'input[name="stock"]',
    ]
    for sel in seletores_estoque:
        try:
            campo = page.wait_for_selector(sel, timeout=2000)
            if campo:
                campo.click()
                delay(0.3)
                campo.fill(str(estoque))
                print(f"   ✅ Estoque: {estoque} unidades")
                break
        except PlaywrightTimeout:
            continue

    delay()
    screenshot(page, "04_preco_estoque", audit_dir)


def preencher_descricao(page, cfg: dict, audit_dir: str):
    """Preenche a descrição do produto."""
    print("\n📋 ETAPA 5: Preenchendo descrição...")

    descricao = cfg.get("descricao", "")
    if not descricao:
        # Gera descrição básica se não fornecida
        nome = cfg.get("nome_base", "Produto")
        descricao = (
            f"✨ {nome}\n\n"
            f"📦 Produto de alta qualidade\n"
            f"🚚 Enviamos por Shopee Envios\n"
            f"🔄 Troca em até 7 dias conforme CDC\n\n"
            f"Dúvidas? Fale no chat! 😊"
        )

    seletores_desc = [
        'textarea[placeholder*="descrição"]',
        'textarea[placeholder*="Descrição"]',
        'textarea[placeholder*="description"]',
        'div[contenteditable="true"]',
        '.ql-editor',
        '[data-testid="description-input"]',
        'textarea[name="description"]',
    ]

    campo = None
    for sel in seletores_desc:
        try:
            campo = page.wait_for_selector(sel, timeout=2000)
            if campo:
                break
        except PlaywrightTimeout:
            continue

    if campo:
        campo.click()
        delay(0.3)
        try:
            campo.fill(descricao)
        except Exception:
            # ContentEditable: usar keyboard
            campo.evaluate("el => el.innerHTML = ''")
            page.keyboard.type(descricao, delay=15)
        delay()
        print("   ✅ Descrição preenchida.")
        screenshot(page, "05_descricao", audit_dir)
    else:
        print("   ⚠️  Campo de descrição não encontrado.")


def salvar_rascunho(page, audit_dir: str, dry_run: bool = False):
    """Salva como rascunho."""
    if dry_run:
        print("\n🔍 DRY RUN: Pulando salvamento. Screenshot final:")
        screenshot(page, "06_dryrun_final", audit_dir)
        return

    print("\n💾 ETAPA 6: Salvando como rascunho...")

    seletores_rascunho = [
        'button:has-text("Salvar rascunho")',
        'button:has-text("salvar rascunho")',
        'button:has-text("Save as Draft")',
        'button:has-text("Rascunho")',
        '[data-testid="save-draft-btn"]',
        'button.btn-draft',
    ]

    for sel in seletores_rascunho:
        try:
            btn = page.wait_for_selector(sel, timeout=3000)
            if btn:
                btn.click()
                delay(2, 4)
                screenshot(page, "06_rascunho_salvo", audit_dir)
                print("   ✅ Rascunho salvo com sucesso!")
                return
        except PlaywrightTimeout:
            continue

    print("   ⚠️  Botão 'Salvar rascunho' não encontrado.")
    print("   Salvando screenshot para diagnóstico...")
    screenshot(page, "06_rascunho_botao_nao_encontrado", audit_dir)


def publicar_produto(page, audit_dir: str):
    """Tenta publicar o produto (apenas com --publicar)."""
    print("\n🚀 PUBLICANDO produto...")

    seletores_publicar = [
        'button:has-text("Publicar")',
        'button:has-text("publicar")',
        'button:has-text("Publish")',
        'button:has-text("Submit")',
        '[data-testid="publish-btn"]',
        'button.btn-primary',
    ]

    for sel in seletores_publicar:
        try:
            btn = page.wait_for_selector(sel, timeout=3000)
            if btn:
                btn.click()
                delay(3, 5)
                screenshot(page, "07_publicado", audit_dir)
                print("   ✅ Produto publicado!")
                return
        except PlaywrightTimeout:
            continue

    print("   ❌ Botão de publicar não encontrado.")
    screenshot(page, "07_publicar_falhou", audit_dir)


# ─────────────────────────────────────────────────────────────────────────────
# ORQUESTRADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def criar_produto(cfg: dict, cor: str, publicar: bool, dry_run: bool, port: int, debug: bool):
    """Fluxo completo de criação do produto."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    audit_dir = os.path.join(AUDIT_DIR, f"{ts}_{cor}")
    os.makedirs(audit_dir, exist_ok=True)

    fotos = listar_fotos_para_upload(cfg)
    if not fotos:
        print(f"❌ Nenhuma foto encontrada em: {cfg['_pasta_cor']}")
        sys.exit(1)

    playwright = None
    try:
        playwright, browser, context = conectar_chrome(port)

        # Abrir nova aba na Seller Center
        page = context.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})

        # ── Fluxo de criação ──────────────────────────────────────────────────
        navegar_para_adicionar_produto(page, audit_dir)
        preencher_nome(page, cfg, audit_dir)
        fazer_upload_fotos(page, fotos, audit_dir)
        preencher_preco_estoque(page, cfg, cor, audit_dir)
        preencher_descricao(page, cfg, audit_dir)

        if dry_run:
            salvar_rascunho(page, audit_dir, dry_run=True)
            print(f"\n✅ DRY RUN concluído! Screenshots em: {audit_dir}")
        elif publicar:
            publicar_produto(page, audit_dir)
            print(f"\n✅ Produto publicado! Screenshots em: {audit_dir}")
        else:
            salvar_rascunho(page, audit_dir)
            print(f"\n✅ Rascunho salvo! Screenshots em: {audit_dir}")
            print("   Para publicar, re-execute com --publicar")

        print(f"\n📁 Auditoria completa: {audit_dir}")

    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        if debug:
            traceback.print_exc()
        if playwright:
            try:
                page.screenshot(path=os.path.join(audit_dir, "ERRO_fatal.png"))
            except Exception:
                pass
        raise
    finally:
        if playwright:
            playwright.stop()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cria produto na Shopee Seller Center via Chrome já logado."
    )
    parser.add_argument("--config", required=True, help="Caminho para produto.json")
    parser.add_argument("--cor", required=True, help="Cor a publicar (ex: vermelho)")
    parser.add_argument("--publicar", action="store_true",
                        help="Publicar diretamente (sem flag = salva rascunho)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true",
                        help="Executa sem salvar. Apenas screenshots.")
    parser.add_argument("--port", type=int, default=9222,
                        help="Porta do Chrome DevTools Protocol (padrão: 9222)")
    parser.add_argument("--debug", action="store_true",
                        help="Ativa log detalhado e traceback completo")

    args = parser.parse_args()

    cfg = carregar_config(args.config, args.cor)

    print("\n" + "═" * 60)
    print("  🛍️  SHOPEE PUBLISHER — Criação Automática de Produto")
    print("═" * 60)
    print(f"  Produto : {cfg['_nome_completo']}")
    print(f"  Cor     : {args.cor}")
    print(f"  Fotos   : {cfg['_pasta_cor']}")
    print(f"  Modo    : {'🔍 DRY RUN' if args.dry_run else ('🚀 PUBLICAR' if args.publicar else '💾 RASCUNHO')}")
    print("═" * 60 + "\n")

    criar_produto(
        cfg=cfg,
        cor=args.cor,
        publicar=args.publicar,
        dry_run=args.dry_run,
        port=args.port,
        debug=args.debug,
    )
