"""Servidor estatico para probar el build web, con log de peticiones a archivo.

Uso:
    .\.venv\Scripts\python.exe tools\serve.py [puerto] [raiz]

El access log normal de http.server va a stderr; aqui se escribe tambien en
build/serve.log para poder consultar las peticiones /log de la telemetria.
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8099
DIR = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else (RAIZ / "build" / "web")
LOG = RAIZ / "build" / "serve.log"

LOG.parent.mkdir(parents=True, exist_ok=True)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DIR), **kw)

    def do_GET(self):
        if self.path.startswith("/log"):
            try:
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(self.path + "\n")
            except Exception:
                pass
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler)
    print(f"serviendo {DIR} en http://localhost:{PUERTO}  (log: {LOG})", flush=True)
    srv.serve_forever()
