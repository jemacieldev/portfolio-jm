#!/usr/bin/env python3
"""
Lê o RSS de cada pasta do Pinterest listada em PASTAS abaixo,
pega os pins mais recentes e salva em pins.json — o arquivo que
o site lê para montar o mural de inspirações.

Roda sozinho todo dia via GitHub Actions (veja .github/workflows/atualizar-pins.yml).
Se quiser rodar na sua máquina: pip install feedparser  &&  python atualizar_pins.py
"""
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

import feedparser

# ============ CONFIGURAÇÃO ============
# Uma linha por pasta: (categoria mostrada no site, link da pasta no Pinterest)
PASTAS = [
    ("Unhada",    "https://br.pinterest.com/ijelost/unhada/"),
    ("Aconchego", "https://br.pinterest.com/ijelost/aconchego/"),
]

MAX_POR_PASTA = 10
SAIDA = Path(__file__).parent / "pins.json"
ANTERIOR = SAIDA if SAIDA.exists() else None


def rss_url(link_pasta: str) -> str:
    """Transforma o link da pasta no endereço do feed: só soma .rss no final."""
    return link_pasta.rstrip("/") + ".rss"


def extrai_imagem(entrada) -> str | None:
    """O RSS do Pinterest guarda a imagem dentro do HTML da descrição."""
    html = entrada.get("summary", "") or entrada.get("description", "")
    m = re.search(r'<img[^>]+src="([^"]+)"', html)
    return m.group(1) if m else None


def busca_pasta(categoria: str, link: str) -> list[dict]:
    pedido = Request(rss_url(link), headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(pedido, timeout=20) as resposta:
        feed = feedparser.parse(resposta.read())

    pins = []
    for entrada in feed.entries[:MAX_POR_PASTA]:
        imagem = extrai_imagem(entrada)
        if not imagem:
            continue
        pins.append({
            "categoria": categoria,
            "titulo": entrada.get("title", "").strip(),
            "imagem": imagem,
            "link": entrada.get("link", ""),
        })
    return pins


def main():
    todos = []
    falhas = []
    for categoria, link in PASTAS:
        try:
            todos += busca_pasta(categoria, link)
            print(f"✓ {categoria}: ok")
        except Exception as erro:
            # Plano B: se uma pasta falhar, o site continua com o que já tinha.
            falhas.append(categoria)
            print(f"✗ {categoria}: {erro}")
        time.sleep(1)  # educado com o servidor do Pinterest

    if not todos and ANTERIOR:
        print("Nada novo encontrado — mantendo o pins.json anterior.")
        return

    SAIDA.write_text(
        json.dumps({"atualizado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "falhas": falhas, "pins": todos}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Salvo {len(todos)} pins em {SAIDA}")


if __name__ == "__main__":
    main()
