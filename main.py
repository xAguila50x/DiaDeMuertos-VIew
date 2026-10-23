# /// script
# dependencies = ["panda3d", "panda3d-gltf"]
# ///
# main.py - Punto de entrada del "Camino de Cempasúchil" (Python + Panda3D).

import asyncio
import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from panda3d.core import ClockObject

from src.app import App

# Obtener el reloj global de Panda3D compatible con escritorio y WebAssembly
globalClock = ClockObject.get_global_clock()

if sys.platform == "emscripten":
    try:
        import pygbag.aio as asyncio  # type: ignore
    except (ImportError, AttributeError):
        pass


async def main():
    app = App()
    app.iniciar()

    from direct.task import Task

    # Actualiza la logica de la app cada frame (taskMgr la llama en cada step()).
    def _tick(task):
        app.actualizar(globalClock.get_dt())
        return Task.cont

    app.base.taskMgr.add(_tick, "tick")

    # pygbag parchea ShowBase.run() para lanzar el bucle de render
    # (taskMgr.step() + await asyncio.sleep(0)) desde dentro de asyncio.run().
    app.base.run()


if __name__ == "__main__":
    asyncio.run(main())
