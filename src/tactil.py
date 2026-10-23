# tactil.py - Interfaz táctil para móvil: joystick virtual y acceso rápido a vistas.

from panda3d.core import (
    Point3,
    TransparencyAttrib,
    Vec3,
)
from direct.gui.DirectGui import DirectButton, DirectFrame


class JoystickTactil:
    """Controles táctiles: joystick virtual en esquina inferior izquierda,

    botón de ciclo rápido y menú desplegable de acceso rápido a todas las vistas
    en la esquina inferior derecha.
    """

    def __init__(self, base, controles, vistas=None):
        self.base = base
        self.controles = controles
        self.controles.tactil = self
        self.vistas = vistas or []
        self.activo = True
        self.arrastrando = False
        self.menu_abierto = False
        self._radio = 0.20
        self._pos_x = 0.36
        self._pos_z = 0.36
        self._botones_acceso = []
        self._construir()

    def _construir(self):
        base = self.base
        padre_izq = getattr(base, "a2dBottomLeft", base.aspect2d)
        padre_der = getattr(base, "a2dBottomRight", base.aspect2d)

        # ---------------- Joystick virtual (abajo a la izquierda) ----------------
        self.fondo = DirectFrame(
            parent=padre_izq,
            frameColor=(0.10, 0.08, 0.16, 0.55),
            frameSize=(-self._radio, self._radio, -self._radio, self._radio),
            pos=(self._pos_x, 0, self._pos_z),
            relief=1,
        )
        self.fondo.set_transparency(TransparencyAttrib.M_alpha)
        self.fondo.set_bin("fixed", 10)

        self.perilla = DirectFrame(
            frameColor=(1.0, 0.72, 0.22, 0.85),
            frameSize=(-0.075, 0.075, -0.075, 0.075),
            pos=(0, 0, 0),
            parent=self.fondo,
            relief=1,
        )
        self.perilla.set_transparency(TransparencyAttrib.M_alpha)

        # ---------------- Botones de vista (abajo a la derecha) ----------------
        # 1. Botón de ciclo rápido de vista (avanza a la siguiente en un toque)
        self.boton_vista = DirectButton(
            parent=padre_der,
            text="Vista Libre >",
            scale=0.048,
            pos=(-0.52, 0, 0.15),
            frameColor=(0.15, 0.12, 0.22, 0.85),
            text_fg=(1.0, 0.85, 0.35, 1.0),
            pad=(0.35, 0.25),
            relief=1,
            command=self._siguiente_vista,
        )
        self.boton_vista.set_transparency(TransparencyAttrib.M_alpha)

        # 2. Botón para abrir/cerrar menú de acceso rápido
        self.boton_menu = DirectButton(
            parent=padre_der,
            text="Vistas...",
            scale=0.048,
            pos=(-0.16, 0, 0.15),
            frameColor=(0.25, 0.16, 0.08, 0.90),
            text_fg=(1.0, 0.90, 0.50, 1.0),
            pad=(0.3, 0.25),
            relief=1,
            command=self._toggle_menu,
        )
        self.boton_menu.set_transparency(TransparencyAttrib.M_alpha)

        # 3. Panel desplegable de acceso rápido con las 8 vistas directas
        n_vistas = len(self.vistas) if self.vistas else 8
        alto_panel = n_vistas * 0.08 + 0.06
        self.panel_menu = DirectFrame(
            parent=padre_der,
            frameColor=(0.12, 0.09, 0.18, 0.92),
            frameSize=(-0.48, 0.48, -0.02, alto_panel),
            pos=(-0.36, 0, 0.24),
            relief=1,
        )
        self.panel_menu.set_transparency(TransparencyAttrib.M_alpha)
        self.panel_menu.set_bin("fixed", 20)
        self.panel_menu.hide()

        # Generar los botones de salto directo para cada vista
        for idx, item in enumerate(self.vistas):
            nombre = item[0] if isinstance(item, (list, tuple)) else str(item)
            y_offset = (n_vistas - 1 - idx) * 0.08 + 0.04
            btn = DirectButton(
                parent=self.panel_menu,
                text=f"{idx + 1}. {nombre}",
                scale=0.042,
                pos=(0, 0, y_offset),
                frameColor=(0.20, 0.16, 0.28, 0.80),
                text_fg=(0.95, 0.92, 0.85, 1.0),
                pad=(0.6, 0.15),
                relief=1,
                command=self._ir_a_vista,
                extraArgs=[idx],
            )
            btn.set_transparency(TransparencyAttrib.M_alpha)
            self._botones_acceso.append(btn)

        base.accept("t", self.alternar)

    def _toggle_menu(self):
        self.menu_abierto = not self.menu_abierto
        if self.menu_abierto:
            self.panel_menu.show()
            self.boton_menu["text"] = "X Cerrar"
        else:
            self.panel_menu.hide()
            self.boton_menu["text"] = "Vistas..."

    def _ir_a_vista(self, indice):
        self.base.messenger.send("ir-a-vista", [indice])
        # Cerrar el panel tras seleccionar para no tapar la pantalla en móvil
        self.menu_abierto = False
        self.panel_menu.hide()
        self.boton_menu["text"] = "Vistas..."

    def set_nombre_vista(self, nombre):
        """Actualiza el texto del botón rápido al cambiar de vista."""
        texto = nombre if len(nombre) <= 14 else nombre[:12] + ".."
        self.boton_vista["text"] = f"{texto} >"

    def _siguiente_vista(self):
        self.base.messenger.send("vista-siguiente")

    def es_toque_en_ui(self, m):
        """Devuelve True si el toque cayó en el área de botones UI de la derecha."""
        if not self.activo:
            return False
        padre_der = getattr(self.base, "a2dBottomRight", self.base.aspect2d)
        pt = padre_der.get_relative_point(self.base.render2d, Point3(m.get_x(), 0, m.get_y()))
        # Si el menú de acceso rápido está abierto, cubre una zona más alta
        z_max = 0.95 if self.menu_abierto else 0.30
        return -0.80 <= pt.x <= 0.0 and 0.0 <= pt.z <= z_max

    def procesar_toque(self, m):
        """Devuelve True si el toque cayó en el área del joystick virtual."""
        if not self.activo:
            return False
        padre_izq = getattr(self.base, "a2dBottomLeft", self.base.aspect2d)
        pt = padre_izq.get_relative_point(self.base.render2d, Point3(m.get_x(), 0, m.get_y()))
        dx = pt.x - self._pos_x
        dz = pt.z - self._pos_z
        # Margen amplio y cómodo para dedos en pantalla táctil
        if dx * dx + dz * dz <= (self._radio * 1.8) ** 2:
            self.arrastrando = True
            self.controles.joystick_activo = True
            self._aplicar_desplazamiento(dx, dz)
            return True
        return False

    def actualizar_arrastre(self, m):
        if not self.arrastrando:
            return
        padre_izq = getattr(self.base, "a2dBottomLeft", self.base.aspect2d)
        pt = padre_izq.get_relative_point(self.base.render2d, Point3(m.get_x(), 0, m.get_y()))
        self._aplicar_desplazamiento(pt.x - self._pos_x, pt.z - self._pos_z)

    def _aplicar_desplazamiento(self, dx, dz):
        dist = (dx * dx + dz * dz) ** 0.5
        if dist > self._radio:
            dx *= self._radio / dist
            dz *= self._radio / dist
        self.perilla.set_pos(dx, 0, dz)
        # dx: desplazamiento horizontal, dz: avance/retroceso
        self.controles.joystick = Vec3(dx / self._radio, 0, dz / self._radio)

    def soltar(self):
        if self.arrastrando:
            self.arrastrando = False
            self.controles.joystick_activo = False
            self.perilla.set_pos(0, 0, 0)
            self.controles.joystick = Vec3(0, 0, 0)

    def actualizar(self):
        pass

    def alternar(self):
        self.activo = not self.activo
        if self.activo:
            self.fondo.show()
            self.perilla.show()
            self.boton_vista.show()
            self.boton_menu.show()
        else:
            self.fondo.hide()
            self.perilla.hide()
            self.boton_vista.hide()
            self.boton_menu.hide()
            self.panel_menu.hide()
            self.menu_abierto = False
