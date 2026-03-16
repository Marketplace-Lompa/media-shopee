#!/usr/bin/env python3
"""
test_look_contract.py — Teste integrado do Style Agent (look_contract).

Usa as imagens de referência reais do poncho-teste para:
  1. Chamar /generate/async com múltiplas imagens de referência
  2. Aguardar resultado e salvar em tests/output/look_contract_test/
  3. Verificar que o look_contract foi inferido e injetado via logs do servidor
  4. Exibir resultado gerado e comparação com resultado1.png (baseline)

Uso:
  cd /Users/lompa-marketplace/Documents/MEDIA-SHOPEE
  python app/tests/test_look_contract.py
"""

import os
import sys
import json
import time
import shutil
import requests
from pathlib import Path
from dotenv import load_dotenv

# ── Setup ────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent.parent  # raiz do mono-repo
APP_DIR    = Path(__file__).parent.parent          # app/
TESTS_DIR  = Path(__file__).parent                 # app/tests/
INPUT_DIR  = TESTS_DIR / "samples" / "poncho-ruana-listras"
OUTPUT_DIR = TESTS_DIR / "output" / "look_contract_test"
BASELINE   = TESTS_DIR / "output" / "gen_01.png"
BASE_URL   = os.getenv("API_BASE_URL", "http://localhost:8000")

load_dotenv(ROOT / ".env")

OUTPUT_DIR.mkdir(exist_ok=True)

GREEN  = "\033[92m"; RED    = "\033[91m"
YELLOW = "\033[93m"; CYAN   = "\033[96m"
BOLD   = "\033[1m";  RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg): print(f"  {RED}❌ {msg}{RESET}")
def info(msg): print(f"  {CYAN}ℹ️  {msg}{RESET}")
def sep():     print(f"\n{'─'*62}\n")


# ── Imagens de referência ────────────────────────────────────────────────────
# Usa as 4 melhores fotos do poncho (ângulos diferentes)
REFERENCE_FILES = [
    INPUT_DIR / "IMG_3327.jpg",   # frente
    INPUT_DIR / "IMG_3328.jpg",   # angulo lateral
    INPUT_DIR / "IMG_3325.jpg",   # detalhe textura
    INPUT_DIR / "IMG_3330.jpg",   # pose alternativa
]


def check_server() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def send_generate(files: list[Path]) -> str | None:
    """Envia imagens para /generate/async e retorna job_id."""
    multipart = []
    opened    = []
    try:
        for f in files:
            if not f.exists():
                print(f"  {YELLOW}⚠️  Arquivo não encontrado, pulando: {f.name}{RESET}")
                continue
            fh = open(f, "rb")
            opened.append(fh)
            ext  = f.suffix.lstrip(".").lower()
            mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else 'png'}"
            multipart.append(("images", (f.name, fh, mime)))

        if not multipart:
            return None

        resp = requests.post(
            f"{BASE_URL}/generate/async",
            files=multipart,
            data={"prompt": ""},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("job_id")
    finally:
        for fh in opened:
            fh.close()


def poll_job(job_id: str, timeout: int = 300) -> dict | None:
    """Aguarda o job terminar e retorna o payload final."""
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(5)
        elapsed = int(time.time() - start)
        try:
            r = requests.get(f"{BASE_URL}/generate/jobs/{job_id}", timeout=10)
            if r.status_code != 200:
                print(f"  ... {elapsed}s (status check falhou: {r.status_code})")
                continue
            data = r.json()
            status = data.get("status", "")
            print(f"  ... {elapsed}s — {status}")
            if status == "done":
                return data
            if status == "error":
                print(f"{RED}❌ Job falhou: {data.get('error')}{RESET}")
                return None
        except Exception as e:
            print(f"  ... {elapsed}s (erro: {e})")
    print(f"{RED}❌ Timeout após {timeout}s{RESET}")
    return None


def find_output_image(job_data: dict) -> Path | None:
    """Localiza a imagem gerada nos outputs do projeto."""
    results = job_data.get("results", [])
    for r in results:
        path_str = r.get("output_path") or r.get("path", "")
        if path_str:
            p = Path(path_str)
            if p.exists():
                return p

    # Fallback: procura a pasta mais recente em app/outputs/
    outputs_dir = APP_DIR / "outputs"
    if not outputs_dir.exists():
        return None
    folders = sorted(
        [d for d in outputs_dir.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for folder in folders[:3]:  # verifica os 3 mais recentes
        pngs = list(folder.glob("gen_*.png"))
        if pngs:
            return sorted(pngs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    return None


def extract_look_contract_from_diag(outputs_dir: Path) -> dict | None:
    """Tenta extrair look_contract do report.json de diagnóstico mais recente."""
    folders = sorted(
        [d for d in outputs_dir.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for folder in folders[:5]:
        diag_candidates = [
            folder / "report.json",
            folder / "diag" / "report.json",
        ]
        # Busca subpastas v2diag_*
        for sub in folder.glob("**/report.json"):
            diag_candidates.append(sub)

        for report_path in diag_candidates:
            if not report_path.exists():
                continue
            try:
                d = json.loads(report_path.read_text())
                lc = (
                    d.get("look_contract")
                    or d.get("context_meta", {}).get("look_contract")
                    or d.get("unified_vision", {}).get("look_contract")
                )
                if lc:
                    return lc
            except Exception:
                pass
    return None


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{BOLD}{'='*62}{RESET}")
    print(f"{BOLD}  STYLE AGENT — Teste Integrado (Look Contract){RESET}")
    print(f"{BOLD}  Usando imagens reais: {INPUT_DIR.name}/{RESET}")
    print(f"{BOLD}{'='*62}{RESET}\n")

    # 1. Servidor
    print(f"{BOLD}[1/5] Verificando servidor...{RESET}")
    if not check_server():
        fail(f"Servidor não está rodando em {BASE_URL}")
        fail("Rode: ./start-dev.sh ou /restart")
        sys.exit(1)
    ok(f"Servidor OK ({BASE_URL})")
    sep()

    # 2. Imagens de referência
    print(f"{BOLD}[2/5] Carregando imagens de referência...{RESET}")
    refs = [f for f in REFERENCE_FILES if f.exists()]
    if len(refs) < 2:
        fail(f"Precisa de pelo menos 2 imagens em {INPUT_DIR}")
        sys.exit(1)
    for f in refs:
        ok(f"{f.name} ({f.stat().st_size // 1024} KB)")
    sep()

    # 3. Envia geração
    print(f"{BOLD}[3/5] Enviando {len(refs)} imagem(ns) para /generate/async...{RESET}")
    t0 = time.time()
    job_id = send_generate(refs)
    if not job_id:
        fail("Falha ao criar job")
        sys.exit(1)
    ok(f"Job criado: {job_id}")
    info("Aguardando resultado (pode levar 60-120s)...\n")
    sep()

    # 4. Aguarda resultado
    print(f"{BOLD}[4/5] Aguardando job...{RESET}")
    job_data = poll_job(job_id, timeout=300)
    if not job_data:
        sys.exit(1)

    elapsed = time.time() - t0
    ok(f"Job concluído em {elapsed:.0f}s")
    sep()

    # 5. Localiza e salva resultado
    print(f"{BOLD}[5/5] Localizando e validando resultado...{RESET}")
    outputs_dir = APP_DIR / "outputs"
    result_img  = find_output_image(job_data)

    if not result_img or not result_img.exists():
        fail(f"Imagem de resultado não encontrada em {outputs_dir}")
        sys.exit(1)

    ok(f"Imagem gerada: {result_img}")

    # Copia para tests/output/look_contract_test/
    dest = OUTPUT_DIR / "resultado_com_look_contract.png"
    shutil.copy2(result_img, dest)
    ok(f"Salva em: {dest}")

    # Extrai look_contract usado
    lc = extract_look_contract_from_diag(outputs_dir)
    if lc:
        print(f"\n  {BOLD}look_contract aplicado:{RESET}")
        print(f"    bottom_style:      {CYAN}{lc.get('bottom_style','')}{RESET}")
        print(f"    bottom_color:      {CYAN}{lc.get('bottom_color','')}{RESET}")
        print(f"    forbidden_bottoms: {RED}{', '.join(lc.get('forbidden_bottoms', []))}{RESET}")
        print(f"    occasion:          {CYAN}{lc.get('occasion','')}{RESET}")
        print(f"    confidence:        {GREEN}{lc.get('confidence', 0):.2f}{RESET}")
    else:
        info("look_contract não encontrado no report.json — verifique logs do servidor")

    sep()

    # ── Comparação ANTES vs DEPOIS ────────────────────────────────────────────
    print(f"{BOLD}COMPARAÇÃO:{RESET}\n")
    print(f"  {BOLD}BASELINE (resultado1.png — sem look_contract):{RESET}")
    print(f"    {BASELINE}")
    print(f"\n  {BOLD}RESULTADO (com look_contract ativo):{RESET}")
    print(f"    {dest}")
    print()

    if BASELINE.exists():
        ok("Abra ambos para comparar:")
        print(f"\n  {CYAN}open '{BASELINE}'{RESET}")
        print(f"  {CYAN}open '{dest}'{RESET}")

    sep()
    ok("Teste concluído!")
    print(f"  Saída em: {OUTPUT_DIR}\n")


if __name__ == "__main__":
    main()
