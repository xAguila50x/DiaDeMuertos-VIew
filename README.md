# Camino de Cempasúchil

Escena 3D interactiva de Día de Muertos, portada del proyecto C++/OpenGL a
**Python + Panda3D** y ejecutable en el **navegador** (escritorio y móvil) con
**pygbag** (Python en WebAssembly/WebGL).

Incluye: casa de adobe con portal y ofrenda, arco de flores, camino de ~7000
pétalos de cempasúchil, panteón, papel picado, faroles, mariposas monarcas,
alrededores y cielo (skybox de atardecer), con sombreado PBR y niebla.

## Requisitos

- Windows (probado) con Python **3.12** (`py -3.12`) — pygbag usa 3.12.
- Conexión a Internet la primera vez (descarga el runtime de Panda3D para WASM).

## Arranque rápido

### Escritorio (nativo, más rápido para desarrollar)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

### Navegador (WebAssembly) — un comando

```powershell
.\.venv\Scripts\python.exe -m pygbag --disable-sound-format-error main.py
```

Abre <http://localhost:8000/>. La primera carga tarda porque descarga el
runtime WASM; deja la terminal abierta para ver los mensajes de la página.

> Para generar un paquete estático listo para publicar (itch.io/web):
> `python -m pygbag --build --archive --disable-sound-format-error main.py`
> → produce `build/web/` y `build/web.zip`.

## Controles

| Acción | Escritorio | Móvil (navegador) |
| --- | --- | --- |
| Mirar | Arrastrar con el ratón (clic) | Arrastrar en la mitad derecha |
| Moverse | `W`/`A`/`S`/`D` | Joystick virtual (abajo-izquierda) |
| Subir/Bajar | `E`/`Q` | — |
| Rápido / Lento | `Shift` / `Ctrl` | — |
| Vistas 1–7 | Teclas `1`..`7` | Botón **Vista** |
| Reiniciar vista | `R` | — |
| Mostrar/ocultar controles | — | `T` (o automático) |

### Vistas predefinidas

1. Vista general
2. Entrada del panteón
3. Camino de pétalos
4. Altar de muertos
5. Ofrenda (detalle)
6. Panteón
7. Vista aérea

## Estructura

```
main.py            Entrada async (compatible pygbag)
pygbag.ini         Exclusión de carpetas al empaquetar (.venv, build…)
requirements.txt   Dependencias (panda3d, panda3d-gltf, pygbag)
shaders/           escena.vert / escena.frag (GLSL ES 3.00, PBR + niebla)
src/
  config.py        Config de Panda3D, rutas y carga de glTF (import gltf)
  azar.py          PRNG con semilla fija (20261102) para reproducibilidad
  camino.py        Spline Catmull-Rom centrípeta del camino de pétalos
  controles.py     Cámara libre FPV (teclado/ratón y joystick táctil)
  escena.py        Construcción del mundo (casa, ofrenda, camino, panteón,…)
  tactil.py        Interfaz táctil (joystick virtual y botón de vistas)
  app.py           Ventana, bucle, shader y entrada del usuario
assets/            Modelos (glTF/glb propios y Kenney), texturas y skybox
```

## Notas

- El proyecto C++ de referencia decide toda la disposición (casa en z=-16,
  panteón en z=+16, spline del camino, semilla fija). Ver
  `assets/CREDITOS.md` para la autoría de los recursos.
- Los modelos glTF se cargan con `panda3d-gltf` (evita cuelgues nativos de assimp);
  `assets` se copian del proyecto C++ sin modificar.
