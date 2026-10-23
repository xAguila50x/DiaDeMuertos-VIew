# app.py - Ventana, bucle principal, entrada del usuario e interfaz.
#
# Reemplaza a App.cpp del proyecto C++ usando Panda3D:
#   - Crea el ShowBase y la escena.
#   - Aplica el shader PBR (escena.vert/frag) a todos los modelos.
#   - Instala los controles de cámara libre.

from panda3d.core import (
    Shader,
    Vec2,
    Vec3,
    Vec4,
    loadPrcFileData,
)

from .camino import Camino
from .config import configurar_panda3d, es_web, ruta_shader
from .controles import Camara, Controles
from .escena import Escena


class App:
    def __init__(self, ancho=1280, alto=720):
        self.ancho = ancho
        self.alto = alto

    def iniciar(self):
        configurar_panda3d(self.ancho, self.alto)
        # En la web el canvas controla el tamaño; en escritorio fijamos la ventana.
        from .config import es_web
        if not es_web():
            loadPrcFileData("", "win-size %d %d" % (self.ancho, self.alto))

        from direct.showbase.ShowBase import ShowBase

        self.base = ShowBase()
        self.base.disable_mouse()
        self.base.set_frame_rate_meter(False)
        # Campo de visión igual al del proyecto C++ (60°).
        self.base.camLens.set_fov(60.0)
        self.base.camLens.set_near_far(0.05, 400.0)

        self.escena = Escena(self.base)
        self.escena.cargar()

        self.camara = Camara()
        # Vista inicial equivalente a vista 0 del C++:
        # posicion (-17, 12, 26) mirando hacia (0, 0, 2)
        self.camara.posicion = Vec3(-17.0, 12.0, 26.0)
        self.camara.mirar_hacia(Vec3(0.0, 0.0, 2.0))
        self.controles = Controles(self.base, self.camara)

        self.tactil = None
        self.vista_actual = 0
        if es_web():
            try:
                import platform
                doc = getattr(platform.window, "document", None)
                if doc:
                    doc.body.style.touchAction = "none"
                    doc.body.style.userSelect = "none"
                    doc.body.style.webkitUserSelect = "none"
                    doc.body.style.overscrollBehavior = "none"
                canvas = getattr(platform.window, "canvas", None)
                if canvas:
                    canvas.style.touchAction = "none"
                    canvas.style.userSelect = "none"
                    canvas.style.webkitUserSelect = "none"
            except Exception:
                pass

            from .tactil import JoystickTactil

            self.tactil = JoystickTactil(self.base, self.controles, self.escena.vistas)
            self.base.accept("vista-siguiente", self._vista_siguiente)
            self.base.accept("ir-a-vista", self._ir_a_vista)

        self._aplicar_shader()
        self._instalar_entrada_extra()
        self._ir_a_vista(0)  # aplica también posicion/orientacion iniciales

    # --------------------------------------------------------------- shader
    def _aplicar_shader(self):
        try:
            shader = Shader.load(
                Shader.SL_GLSL,
                vertex=ruta_shader("escena.vert"),
                fragment=ruta_shader("escena.frag"),
            )
            self.shader = shader
            self.escena.raiz.set_shader(shader)
            self.escena.raiz.set_shader_input("uDirLuz", Vec3(0.55, 0.42, -0.55))
            self.escena.raiz.set_shader_input("uColorLuz", Vec3(1.0, 0.82, 0.62) * 2.5)
            self.escena.raiz.set_shader_input("uAmbienteCielo", Vec3(0.45, 0.40, 0.55))
            self.escena.raiz.set_shader_input("uAmbienteSuelo", Vec3(0.28, 0.22, 0.18))
            self.escena.raiz.set_shader_input("uColorNiebla", Vec3(0.42, 0.35, 0.45))
            self.escena.raiz.set_shader_input("uDensidadNiebla", 0.007)
            # Luz cálida en la entrada del panteón
            self.escena.raiz.set_shader_input("uLuzEntradaPos", Vec3(0.0, 3.2, 15.4))
            self.escena.raiz.set_shader_input("uLuzEntradaColor", Vec3(1.0, 0.78, 0.42) * 3.5)
            # Valores por defecto del material
            self.escena.raiz.set_shader_input("uColor", Vec4(1, 1, 1, 1))
            self.escena.raiz.set_shader_input("uEmision", Vec3(0, 0, 0))
            self.escena.raiz.set_shader_input("uMetalico", 0.0)
            self.escena.raiz.set_shader_input("uRugosidad", 0.8)
            self.escena.raiz.set_shader_input("uCapa", 0.0)
            self.escena.raiz.set_shader_input("uRugosidadCapa", 0.0)
            self.escena.raiz.set_shader_input("uModoAlfa", 0)
            self.escena.raiz.set_shader_input("uCorte", 0.5)
            self.escena.raiz.set_shader_input("uEscalaUV", Vec2(1, 1))
            self.escena.raiz.set_shader_input("uTinte", Vec4(1, 1, 1, 1))
        except Exception as e:
            print("Aviso: no se pudo aplicar el shader PBR:", e)
            self.shader = None

    # -------------------------------------------------------------- entrada
    def _instalar_entrada_extra(self):
        base = self.base
        num_vistas = len(self.escena.vistas)
        for i in range(1, num_vistas + 1):
            base.accept(str(i), self._ir_a_vista, [i - 1])
        base.accept("v", self._vista_siguiente)
        base.accept("r", self._reset)

    def _ir_a_vista(self, indice):
        vistas = self.escena.vistas
        if not vistas:
            return
        indice = indice % len(vistas)
        nombre, pos, objetivo = vistas[indice]
        self.camara.posicion = Vec3(pos)
        self.camara.mirar_hacia(Vec3(objetivo))
        self.vista_actual = indice
        if self.tactil is not None and hasattr(self.tactil, "set_nombre_vista"):
            self.tactil.set_nombre_vista(nombre)

    def _vista_siguiente(self):
        vistas = self.escena.vistas
        if not vistas:
            return
        sig = (getattr(self, "vista_actual", 0) + 1) % len(vistas)
        self._ir_a_vista(sig)

    def _reset(self):
        self._ir_a_vista(0)

    def actualizar(self, dt):
        self.controles.actualizar(dt)
        self.escena.actualizar_camara(self.camara.posicion)
        if self.tactil is not None:
            self.tactil.actualizar()
        if self.shader is not None:
            self.escena.raiz.set_shader_input("uPosCamara", self.camara.posicion)
