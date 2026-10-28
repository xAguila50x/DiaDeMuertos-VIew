# controles.py - Cámara libre FPV con teclado/ratón (escritorio) y táctil (móvil).

import math

from panda3d.core import Vec3


class Camara:
    """Cámara libre (vuelo) equivalente a la del proyecto C++."""

    def __init__(self):
        self.posicion = Vec3(0.0, 1.7, 10.0)
        self.guinada = -90.0  # yaw: -90° mira hacia -Z
        self.cabeceo = 0.0    # pitch
        self.velocidad = 6.0
        self.sensibilidad = 0.12
        self.fov = 60.0

    def frente(self):
        gy = math.radians(self.guinada)
        gc = math.radians(self.cabeceo)
        return Vec3(
            math.cos(gy) * math.cos(gc),   # x
            math.sin(gc),                   # y (altura)
            math.sin(gy) * math.cos(gc),   # z (profundidad)
        )

    def derecha(self):
        f = self.frente()
        return Vec3(-f.z, 0.0, f.x).normalized()

    def mirar_hacia(self, punto):
        d = (punto - self.posicion)
        ln = d.length()
        if ln < 1e-6:
            return
        d /= ln
        self.cabeceo = math.degrees(math.asin(max(-1.0, min(1.0, d.y))))
        self.guinada = math.degrees(math.atan2(d.z, d.x))

    def girar(self, dx, dy):
        self.guinada += dx * self.sensibilidad
        self.cabeceo += dy * self.sensibilidad
        self.cabeceo = max(-89.0, min(89.0, self.cabeceo))

    def desplazar(self, direccion_local, dt, multiplicador=1.0):
        f = self.frente()
        r = self.derecha()
        arriba = Vec3(0, 1, 0)
        v = r * direccion_local.x + arriba * direccion_local.y + f * direccion_local.z
        self.posicion = self.posicion + v * (self.velocidad * multiplicador * dt)
        if self.posicion.y < 0.25:
            self.posicion.y = 0.25


class Controles:
    """Entrada unificada de teclado, ratón y táctil."""

    def __init__(self, base, camara):
        self.base = base
        self.camara = camara
        self.tactil = None
        self.teclas = set()
        self.raton_presionado = False
        self.ultimo_x = 0.0
        self.ultimo_y = 0.0
        self.joystick = Vec3(0, 0, 0)
        self.joystick_activo = False
        self._instalar()

    def _instalar(self):
        base = self.base
        for tecla in ("w", "a", "s", "d", "q", "e", "shift", "control"):
            base.accept(tecla, self._pulsar, [tecla])
            base.accept(tecla + "-up", self._soltar, [tecla])

        base.accept("mouse1", self._raton_abajo)
        base.accept("mouse1-up", self._raton_arriba)

    def _pulsar(self, tecla):
        self.teclas.add(tecla)

    def _soltar(self, tecla):
        self.teclas.discard(tecla)

    def _raton_abajo(self):
        mwn = getattr(self.base, "mouseWatcherNode", None)
        if not mwn or not mwn.has_mouse():
            return
        m = mwn.get_mouse()
        self.ultimo_x = m.get_x()
        self.ultimo_y = m.get_y()

        # Si el toque cae dentro del joystick táctil, lo atiende el joystick
        if self.tactil and getattr(self.tactil, "activo", False):
            if self.tactil.procesar_toque(m):
                return
            if hasattr(self.tactil, "manejar_toque_ui") and self.tactil.manejar_toque_ui(m):
                return

        # Si no, es rotación libre de cámara
        self.raton_presionado = True

    def _raton_arriba(self):
        self.raton_presionado = False
        if self.tactil:
            self.tactil.soltar()

    def actualizar(self, dt):
        mwn = getattr(self.base, "mouseWatcherNode", None)
        if mwn and mwn.has_mouse():
            m = mwn.get_mouse()
            x, y = m.get_x(), m.get_y()
            if self.tactil and getattr(self.tactil, "arrastrando", False):
                self.tactil.actualizar_arrastre(m)
            elif self.raton_presionado:
                dx = (x - self.ultimo_x) * self.base.get_aspect_ratio() * 60.0
                dy = (y - self.ultimo_y) * 60.0
                self.camara.girar(dx, dy)
            self.ultimo_x, self.ultimo_y = x, y

        direccion = Vec3(0, 0, 0)
        if "w" in self.teclas:
            direccion.z += 1
        if "s" in self.teclas:
            direccion.z -= 1
        if "d" in self.teclas:
            direccion.x += 1
        if "a" in self.teclas:
            direccion.x -= 1
        if "e" in self.teclas:
            direccion.y += 1
        if "q" in self.teclas:
            direccion.y -= 1

        # Sumar el movimiento del joystick virtual
        direccion.x += self.joystick.x
        direccion.z += self.joystick.z

        multiplicador = 1.0
        if "shift" in self.teclas:
            multiplicador = 3.0
        elif "control" in self.teclas:
            multiplicador = 0.3

        self.camara.desplazar(direccion, dt, multiplicador)

        base = self.base
        base.camera.set_pos(self.camara.posicion)
        base.camera.set_hpr(-self.camara.guinada - 90.0, self.camara.cabeceo, 0.0)
