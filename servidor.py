#!/usr/bin/env python3
"""
Servidor HTTP para o Gerador Universal de Diagramas de Acordes.
Serve index.html do diretorio ATUAL e endpoint /gerar
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Garante que estamos no diretorio correto
DIR_ATUAL = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR_ATUAL)

# Importa o gerador do diretorio atual
sys.path.insert(0, DIR_ATUAL)
from gerador_web_dinamico import gerar_dinamico


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Log colorido para facilitar debug
        print(f"[SERVIDOR] {self.address_string()} - {format % args}")

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # Headers anti-cache para evitar problemas de cache
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_html(self, html_bytes, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(html_bytes)

    def _send_error(self, message, status=400):
        self._send_json({"erro": message}, status)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/gerar":
            acorde = query.get("acorde", [""])[0].strip()
            if not acorde:
                self._send_error("Parametro 'acorde' obrigatorio", 400)
                return
            try:
                resultado = gerar_dinamico(acorde)
                self._send_json(resultado)
            except Exception as e:
                self._send_error(str(e), 500)
            return

        if path == "/" or path == "/index.html":
            index_path = os.path.join(DIR_ATUAL, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    self._send_html(f.read())
            else:
                self._send_error(f"index.html nao encontrado em: {index_path}", 404)
            return

        # 404 para tudo o mais
        self._send_error(f"Rota nao encontrada: {path}", 404)


def run(port=8000):
    print(f"=" * 60)
    print(f" GERADOR DE ACORDES - SERVIDOR")
    print(f"=" * 60)
    print(f" Diretorio de trabalho: {DIR_ATUAL}")
    print(f" index.html esperado em: {os.path.join(DIR_ATUAL, 'index.html')}")
    print(f" Endpoint: http://localhost:{port}/gerar?acorde=C")
    print(f" Frontend: http://localhost:{port}/")
    print(f"=" * 60)
    server = HTTPServer(("", port), Handler)
    print(f" Servidor rodando na porta {port}...")
    print(f" Pressione Ctrl+C para parar.")
    print(f"=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n Servidor encerrado.")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run(port)
