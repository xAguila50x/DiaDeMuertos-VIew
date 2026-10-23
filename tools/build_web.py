# build_web.py - Build web autocontenido para "Camino de Cempasuchil".
#
# Genera un sitio estatico en build/web/ que NO depende del CDN de pygbag
# (cuyo browserfs.min.js da 404 en 0.9.3). Sirve igual en localhost y en
# GitHub Pages dentro de un subpath, porque todas las rutas son relativas.
#
# Uso:
#   .\.venv\Scripts\python.exe tools\build_web.py
#
# Pasos:
#   1. pygbag --build --archive  ->  build/web/
#   2. Espeja el runtime WASM desde build/web-cache/ a build/web/cdn/...
#   3. Descarga browserfs.min.js local (jsdelivr).
#   4. Parchea build/web/index.html para usar rutas relativas.

import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BUILD = RAIZ / "build"
WEB = BUILD / "web"
CACHE = BUILD / "web-cache"

CDN_HOST = "https://pygame-web.github.io"
CDN_VERSION = "0.9.3"
CDN_BASE = f"{CDN_HOST}/cdn/{CDN_VERSION}/"

# Paquetes puros que la app necesita en runtime y que NO estan en el indice
# del CDN. Se descargan de PyPI en build y se publican en el indice local para
# que el sitio final sea 100% local (sin peticiones a pypi.org).
WHEELS_PYPI = {
    "panda3d_gltf": (
        "https://files.pythonhosted.org/packages/24/0f/b9406c4434422822039a4daefdc479e71326131f2a0f8"
        "0f88f7cfc60e9c8/panda3d_gltf-1.3.0-py3-none-any.whl",
        "panda3d_gltf-1.3.0-py3-none-any.whl",
    ),
    "panda3d_simplepbr": (
        "https://files.pythonhosted.org/packages/11/5d/3744c6550dddf933785a37cdd4a9921fe13284e6d115b"
        "5a2637fe390f158/panda3d_simplepbr-0.13.1-py3-none-any.whl",
        "panda3d_simplepbr-0.13.1-py3-none-any.whl",
    ),
    "typing_extensions": (
        "https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80"
        "/typing_extensions-4.16.0-py3-none-any.whl",
        "typing_extensions-4.16.0-py3-none-any.whl",
    ),
}

# URL del CDN -> ruta destino relativa dentro de build/web/
RUNTIME = {
    f"/cdn/{CDN_VERSION}/pythons.js": f"cdn/{CDN_VERSION}/pythons.js",
    f"/cdn/{CDN_VERSION}/empty.html": f"cdn/{CDN_VERSION}/empty.html",
    f"/cdn/{CDN_VERSION}/empty.ogg": f"cdn/{CDN_VERSION}/empty.ogg",
    f"/cdn/{CDN_VERSION}/cpythonrc.py": f"cdn/{CDN_VERSION}/cpythonrc.py",
    f"/cdn/{CDN_VERSION}/cpython312/main.js": f"cdn/{CDN_VERSION}/cpython312/main.js",
    f"/cdn/{CDN_VERSION}/cpython312/main.data": f"cdn/{CDN_VERSION}/cpython312/main.data",
    f"/cdn/{CDN_VERSION}/cpython312/main.wasm": f"cdn/{CDN_VERSION}/cpython312/main.wasm",
    "/cdn/vtx.js": "cdn/vtx.js",
    "/cdn/vt/xterm.css": "cdn/vt/xterm.css",
    "/cdn/vt/xterm.js": "cdn/vt/xterm.js",
    "/cdn/vt/xterm-addon-image.js": "cdn/vt/xterm-addon-image.js",
    "/cdn/cp312/panda3d-1.11.0-cp312-cp312-wasm32_bi_emscripten.whl":
        "cdn/cp312/panda3d-1.11.0-cp312-cp312-wasm32_bi_emscripten.whl",
}

# Recursos que no siempre estan cacheados: se descargan del CDN si faltan.
DESCARGAS = {
    "/cdn/index-0.9.3-cp312.json": "cdn/index-0.9.3-cp312.json",
    "/cdn/cp312/panda3d-1.11.0-cp312-cp312-wasm32_bi_emscripten.whl":
        "cdn/cp312/panda3d-1.11.0-cp312-cp312-wasm32_bi_emscripten.whl",
}


def md5(txt):
    return hashlib.md5(txt.encode()).hexdigest()


def correr_pygbag():
    print("[1/4] pygbag --build --archive ...")
    cmd = [
        sys.executable, "-m", "pygbag",
        "--build", "--archive",
        "--template", str(RAIZ / "tools" / "templates" / "mix3d.tmpl"),
        "--disable-sound-format-error",
        "main.py",
    ]
    r = subprocess.run(cmd, cwd=RAIZ)
    if r.returncode != 0:
        raise SystemExit("pygbag fallo con codigo %d" % r.returncode)
    if not WEB.is_dir():
        raise SystemExit("No se genero %s" % WEB)


def espejar_runtime():
    print("[2/4] Espejo del runtime local ...")
    faltan = []
    for url, dest_rel in RUNTIME.items():
        h = md5(CDN_HOST + url)
        src = CACHE / (h + ".data")
        dest = WEB / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dest)
        else:
            try:
                descargar(CDN_HOST + url, dest)
            except Exception as e:
                faltan.append((url, dest))
                print("   AVISO no se pudo obtener", url, e)
    for url, dest_rel in DESCARGAS.items():
        dest = WEB / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            descargar(CDN_HOST + url, dest)
        except Exception as e:
            faltan.append((url, dest))
            print("   AVISO no se pudo bajar", url, e)
    if faltan:
        print("   AVISO: %d recursos no se pudieron espejar:" % len(faltan))
        for url, _ in faltan:
            print("     -", url)
    else:
        print("   Runtime espejado OK")


def descargar(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def bajar_browserfs():
    print("[3/4] browserfs.min.js ...")
    dest = WEB / "browserfs.min.js"
    if dest.is_file():
        print("   ya existe")
        return
    url = "https://cdn.jsdelivr.net/npm/browserfs@1.4.3/dist/browserfs.min.js"
    descargar(url, dest)
    print("   descargado", dest.stat().st_size, "bytes")


def parchear_pythons():
    # Panda3D WASM resuelve los paquetes con PEP723/pep0723.py. Sin PYGPI usa el
    # CDN externo (pygame-web.github.io) y falla en un sitio estatico. Al inyectar
    # PYGPI=cdn/ en cpy_argv (que se llena desde el query string de la URL), el
    # indice y el wheel de panda3d se resuelven relativo al propio sitio.
    py = WEB / "cdn" / CDN_VERSION / "pythons.js"
    txt = py.read_text(encoding="utf-8")
    if "PYGPI=cdn/" in txt:
        return
    ancla = """    if (elems.length)
        for (const arg of elems.pop().split("&")) {
            vm.cpy_argv.push(decodeURI(arg))
        }
"""
    inyecta = ancla + """
    // PYGPI: paquetes panda3d se resuelven relativo a ./cdn/ (100% local)
    if (!vm.cpy_argv.some(a => a.startsWith("PYGPI=")))
        vm.cpy_argv.push("PYGPI=cdn/")
"""
    if ancla not in txt:
        print("   AVISO: no se encontro el ancla de cpy_argv en pythons.js")
        return
    txt = txt.replace(ancla, inyecta)
    py.write_text(txt, encoding="utf-8")


def parchear_index():
    print("[4/4] Parcheando index.html ...")
    idx = WEB / "index.html"
    html = idx.read_text(encoding="utf-8")

    # El CDN base pasa a ser relativo: cdn/0.9.3/  (funciona en subpaths).
    html = html.replace(CDN_BASE, f"cdn/{CDN_VERSION}/")
    html = html.replace(CDN_HOST + "/cdn/", "cdn/")
    html = html.replace(CDN_HOST, "")

    # browserfs local.
    html = html.replace("cdn/" + CDN_VERSION + "//browserfs.min.js", "browserfs.min.js")
    html = html.replace(f"cdn/{CDN_VERSION}/browserfs.min.js", "browserfs.min.js")

    # El canvas WebGL real es #canvas (Panda3D usa document.getElementById('canvas')).
    # El template de pygbag muestra el canvas 2D del terminal y deja #canvas3d
    # oculto. Aqui forzamos #canvas visible, ocultamos #canvas3d y usamos un fondo
    # oscuro. Se inyecta al final de custom_onload (JS) y se corrige custom_site
    # (Python embebido) que ponia el fondo gris #7f7f7f.
    #
    # IMPORTANTE: pythons.js (window_canvas_adjust) redimensiona #canvas segun el
    # layout del terminal cuando user_canvas==0, lo que DESTRUYE el tamano que
    # Panda3D le asigna. Con user_canvas=1, esa funcion retorna sin tocar el canvas
    # y Panda3D gestiona el suyo (via __canvas_resized).
    html = html.replace(
        'platform.document.body.style.background = "#7f7f7f"',
        'platform.document.body.style.background = "#101018"',
    )
    html = html.replace("user_canvas : 0,", "user_canvas : 1,")
    html = html.replace(
        "async function custom_onload(debug_hidden) {",
        "async function custom_onload(debug_hidden) {\n"
        "        var c2 = document.getElementById(\"canvas\")\n"
        "        if (c2) {\n"
        "            c2.hidden = false; c2.style.display = \"block\"; c2.style.visibility = \"visible\"\n"
        "            c2.style.position = \"absolute\"; c2.style.left = \"50%\"\n"
        "            c2.style.transform = \"translateX(-50%)\"; c2.style.top = \"0\"\n"
        "            c2.style.width = \"100vw\"; c2.style.height = \"56.25vw\"\n"
        "            c2.style.maxHeight = \"100vh\"; c2.style.maxWidth = \"177.78vh\"\n"
        "        }\n"
        "        document.body.style.background = \"#101018\"\n"
        "        // Telemetría: el estado viaja al access log del servidor (fetch a /log).\n"
        "        setInterval(function(){\n"
        "            try {\n"
        "                var t = document.querySelector(\".xterm-rows\")\n"
        "                var m = \"JS title=\" + document.title\n"
        "                m += \" termrows=\" + (t ? t.children.length : -1)\n"
        "                m += \" py=\" + (window.python ? (window.python.is_ready ? 1 : 0) : -1)\n"
        "                m += \" term=\" + (t?t.innerText.slice(-900):\"NO-TERMINAL\")\n"
        "                fetch(\"log?\" + encodeURIComponent(m), {cache:\"no-store\"})\n"
        "            } catch(e) {}\n"
        "        }, 10000)\n",
    )

    idx.write_text(html, encoding="utf-8")

    # Indice de paquetes WASM: -CDN- relativo para que el wheel de panda3d
    # se resuelva localmente (tambien en GitHub Pages).
    jidx = WEB / "cdn" / "index-0.9.3-cp312.json"
    if jidx.is_file():
        txt = jidx.read_text(encoding="utf-8")
        txt = txt.replace('"https://pygame-web.github.io/cdn/"', '"cdn/"')
        jidx.write_text(txt, encoding="utf-8")

    # Verificacion: no debe quedar ninguna referencia al CDN externo.
    externos = [l for l in html.splitlines() if "pygame-web.github.io" in l]
    externos += [
        l for l in jidx.read_text(encoding="utf-8").splitlines()
        if "pygame-web.github.io" in l
    ] if jidx.is_file() else []
    if externos:
        print("   AVISO: quedan referencias externas:")
        for l in externos:
            print("     ", l.strip()[:160])
    else:
        print("   index.html + index json sin referencias externas OK")


def parchear_indice_paquetes():
    """Publica en el indice local los wheels puros que la app necesita.

    Sin esto, pep0723 cae a https://pypi.org/simple/... en runtime, lo que
    rompe el requisito de build autocontenido y hace el arranque lento.
    """
    jidx = WEB / "cdn" / "index-0.9.3-cp312.json"
    if not jidx.is_file():
        print("   AVISO: no existe el indice de paquetes")
        return
    datos = json.loads(jidx.read_text(encoding="utf-8"))
    pkgdir = WEB / "cdn" / "pkg"
    pkgdir.mkdir(parents=True, exist_ok=True)
    for nombre, (url, fname) in WHEELS_PYPI.items():
        dest = pkgdir / fname
        if not dest.is_file():
            try:
                descargar(url, dest)
                print("   wheel local:", fname, dest.stat().st_size, "bytes")
            except Exception as e:
                print("   AVISO no se pudo bajar", fname, e)
                continue
        datos[nombre] = "pkg/" + fname
    # -CDN- relativo (site estatico, funciona en subpaths)
    datos["-CDN-"] = "cdn/"
    jidx.write_text(json.dumps(datos, indent=4, ensure_ascii=False), encoding="utf-8")
    print("   indice local con %d paquetes" % len(datos))


def main():
    correr_pygbag()
    espejar_runtime()
    bajar_browserfs()
    parchear_pythons()
    parchear_index()
    parchear_indice_paquetes()
    print("\nListo. Sirve build/web/ como sitio estatico:")
    print("   .\\.venv\\Scripts\\python.exe -m http.server 8099 --directory build/web")


if __name__ == "__main__":
    main()
