# -*- coding: utf-8 -*-
"""Pieni vastaanottopalvelin: selain POSTaa tiedostoja, jotka tallennetaan kansioon.

Käyttö: python tyokalut/vastaanota.py <kohdekansio> [portti]
POST /<tiedostonimi>  body = tiedoston tavut. CORS sallittu, jotta localhost:8753 voi lähettää.
Tarvitaan, kun selaimen (MediaRecorder) tuottamat videot pitää saada levylle - selainpaneeli
estää lataukset."""
import http.server, os, sys, re
sys.stdout.reconfigure(encoding="utf-8")
KOHDE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
PORTTI = int(sys.argv[2]) if len(sys.argv) > 2 else 8754
os.makedirs(KOHDE, exist_ok=True)


class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_POST(self):
        nimi = re.sub(r"[^A-Za-z0-9_.+-]", "_", os.path.basename(self.path.split("?")[0]))
        n = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(n)
        polku = os.path.join(KOHDE, nimi)
        open(polku, "wb").write(data)
        print("tallennettu %s (%d tavua)" % (polku, n), flush=True)
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


print("vastaanotto kansioon %s portissa %d" % (KOHDE, PORTTI), flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", PORTTI), H).serve_forever()
