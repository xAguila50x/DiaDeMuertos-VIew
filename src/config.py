# config.py - Rutas base, ajustes de Panda3D y utilidades comunes.
#
# Centraliza la localización de la carpeta assets/ para que funcione igual al
# ejecutar desde el escritorio (Panda3D nativo) y dentro del navegador (pygbag).
#
# IMPORTANTE: se fuerza el sistema de coordenadas a Y-arriba (igual que el
# proyecto C++ de referencia y que OpenGL/GLM estándar). En Panda3D el sistema
# por defecto es Z-arriba / Y-profundidad, lo que causa que la escena aparezca
# volcada o "escalada hacia arriba" cuando los modelos y poses son Y-up.

import os
import sys

from panda3d.core import Filename, get_model_path, loadPrcFileData


def es_web():
    return sys.platform == "emscripten"


def base_dir():
    """Carpeta que contiene assets/ y shaders/ (raíz del proyecto)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def configurar_panda3d(ancho=1280, alto=720):
    """Ajustes equivalentes a los del proyecto C++."""
    ajustes = [
        # Sistema de coordenadas Y-arriba (igual que OpenGL/GLM y el .cpp).
        # Con esto set_pos(x,y,z), set_hpr y los shaders usan el mismo espacio
        # que el proyecto de referencia: Y = altura, Z = profundidad.
        "coordinate-system yup",
        "default-model-extension .gltf",
        "vfs-implicit-pz false",
        "notify-level-assimp fatal",
        "notify-level-gobj fatal",
        "audio-library-name p3openal_audio",
        "sync-video 1",
    ]
    if es_web():
        ajustes.append("gl-force-precision mediump")
        # El vblank bloquea el hilo en WASM.
        ajustes.append("sync-video 0")
    loadPrcFileData("", "\n".join(ajustes))
    get_model_path().prepend_directory(Filename.from_os_specific(base_dir()))
    # Cargador de glTF en Python puro (evita fallos nativos de assimp).
    try:
        import gltf  # noqa: F401  (registra el cargador .gltf/.glb)
    except Exception:
        pass


def ruta_asset(relativa):
    return "assets/" + relativa


def ruta_shader(nombre):
    return "shaders/" + nombre
