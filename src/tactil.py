# tactil.py - Interfaz t├íctil para m├│vil: joystick virtual y acceso r├ípido a vistas.

from panda3d.core import (
    Point3,
    TransparencyAttrib,
    Vec3,
)
from direct.gui.DirectGui import DirectFrame


class JoystickTactil:
    """Controles t├íctiles responsivos: joystick virtual abajo a la izquierda,

    bot├│n de ciclo r├ípido y men├║ desplegable de acceso r├ípido a todas las vistas
    abajo a la derecha. Se reposicionan y redimensionan al cambiar el tama├▒o de
    la ventana o la orientaci├│n del dispositivo (vertical / horizontal).
    """

    def __init__(self, base, controles, vistas=None):
        self.base = base
        self.controles = controles
        self.controles.tactil = self
        self.vistas = vistas or []
        self.activo = True
        self.arrastrando = False
        self.menu_abierto = False

        self._w = 1
        self._h = 1
        self._ultimo_tamano = (0, 0)
        self._pedido_tamano = (0, 0)
        self._margen = 16.0
        self._radio = 72.0
        self._perilla = 26.0
        self._bw = 170.0
        self._bh = 46.0
        self._gap = 8.0
        self._centro_joy = (80.0, -100.0)
        self._panel_w = 300.0
        self._panel_h = 300.0
        self._panel_z0 = -400.0
        self._columnas = 1
        self._ancho_celda = 300.0
        self._esc_p = 14.0
        self._nombre_vista = "Vista Libre"
        self._botones_acceso = []
        self._rects = {"menu": None, "vista": None, "panel": None, "filas": []}

        self._construir()
        self._reubicar(forzar=True)

    # ------------------------------------------------------------------ build
    def _construir(self):
        base = self.base
        padre = base.pixel2d

        # ---------------- Joystick virtual (abajo a la izquierda) ----------------
        self.fondo = DirectFrame(
            parent=padre,
            frameColor=(0.10, 0.08, 0.16, 0.55),
            frameSize=(-self._radio, self._radio, -self._radio, self._radio),
            pos=(self._centro_joy[0], 0, self._centro_joy[1]),
            relief=1,
            suppressMouse=0,
        )
        self.fondo.set_transparency(TransparencyAttrib.M_alpha)
        self.fondo.set_bin("fixed", 10)

        self.perilla = DirectFrame(
            frameColor=(1.0, 0.72, 0.22, 0.85),
            frameSize=(-self._perilla, self._perilla, -self._perilla, self._perilla),
            pos=(0, 0, 0),
            parent=self.fondo,
            relief=1,
            suppressMouse=0,
        )
        self.perilla.set_transparency(TransparencyAttrib.M_alpha)

        # ---------------- Botones de vista (abajo a la derecha) ----------------
        self.boton_vista = DirectFrame(
            parent=padre,
            text="Vista Libre >",
            text_scale=(16, 16),
            text_fg=(1.0, 0.85, 0.35, 1.0),
            frameColor=(0.15, 0.12, 0.22, 0.85),
            frameSize=(-self._bw / 2, self._bw / 2, -self._bh / 2, self._bh / 2),
            relief=1,
            suppressMouse=0,
        )
        self.boton_vista.set_transparency(TransparencyAttrib.M_alpha)
        self.boton_vista.set_bin("fixed", 15)

        self.boton_menu = DirectFrame(
            parent=padre,
            text="Vistas...",
            text_scale=(16, 16),
            text_fg=(1.0, 0.90, 0.50, 1.0),
            frameColor=(0.25, 0.16, 0.08, 0.90),
            frameSize=(-self._bw / 2, self._bw / 2, -self._bh / 2, self._bh / 2),
            relief=1,
            suppressMouse=0,
        )
        self.boton_menu.set_transparency(TransparencyAttrib.M_alpha)
        self.boton_menu.set_bin("fixed", 15)

        # ---------------- Panel desplegable de acceso r├ípido ----------------
        self.panel_menu = DirectFrame(
            parent=padre,
            frameColor=(0.12, 0.09, 0.18, 0.92),
            frameSize=(-self._panel_w / 2, self._panel_w / 2, -self._panel_h / 2, self._panel_h / 2),
            pos=(base.win.get_x_size() - self._panel_w / 2, 0, -self._panel_h / 2),
            relief=1,
            suppressMouse=0,
        )
        self.panel_menu.set_transparency(TransparencyAttrib.M_alpha)
        self.panel_menu.set_bin("fixed", 20)
        self.panel_menu.hide()

        for idx, item in enumerate(self.vistas):
            nombre = item[0] if isinstance(item, (list, tuple)) else str(item)
            btn = DirectFrame(
                parent=self.panel_menu,
                text=f"{idx + 1}. {nombre}",
                text_scale=(14, 14),
                text_fg=(0.95, 0.92, 0.85, 1.0),
                frameColor=(0.20, 0.16, 0.28, 0.80),
                frameSize=(-100, 100, -16, 16),
                pos=(0, 0, 0),
                relief=1,
                suppressMouse=0,
            )
            btn.set_transparency(TransparencyAttrib.M_alpha)
            self._botones_acceso.append(btn)

        base.accept("t", self.alternar)

    # ---------------------------------------------------------- layout din├ímico
    def _tamano_css(self):
        """Tama├▒o real de la ventana del navegador en p├¡xeles CSS."""
        try:
            import platform as _plataforma
            w = int(_plataforma.window.innerWidth)
            h = int(_plataforma.window.innerHeight)
            if w > 1 and h > 1:
                return w, h
        except Exception:
            pass
        return None

    def _pedir_tamano(self, w, h):
        """Pide a Panda3D que adapte su backbuffer al tama├▒o del navegador."""
        if self._pedido_tamano == (w, h):
            return
        self._pedido_tamano = (w, h)
        try:
            from panda3d.core import WindowProperties
            props = WindowProperties()
            props.set_size(int(w), int(h))
            self.base.win.request_properties(props)
        except Exception:
            pass

    def _reubicar(self, forzar=False):
        base = self.base
        win = getattr(base, "win", None)
        if win is None:
            return
        css = self._tamano_css()
        if css is None:
            try:
                css = (int(win.get_x_size()), int(win.get_y_size()))
            except Exception:
                return
        w, h = css
        if w < 2 or h < 2:
            return
        try:
            if (int(win.get_x_size()), int(win.get_y_size())) != (w, h):
                self._pedir_tamano(w, h)
        except Exception:
            pass
        if not forzar and (w, h) == self._ultimo_tamano:
            return
        self._ultimo_tamano = (w, h)
        self._w, self._h = w, h

        # ShowBase solo fija pixel2d/aspect2d al iniciar: recalcular al redimensionar.
        base.pixel2d.set_pos(-1, 0, 1)
        base.pixel2d.set_scale(2.0 / w, 1.0, 2.0 / h)

        ar = float(w) / float(h)
        base.aspect2d.set_scale(1.0 / ar, 1.0, 1.0)
        base.a2dLeft, base.a2dRight = -ar, ar
        for nombre, x, z in (
            ("a2dTopLeft", -ar, 1.0),
            ("a2dTopRight", ar, 1.0),
            ("a2dBottomLeft", -ar, -1.0),
            ("a2dBottomRight", ar, -1.0),
        ):
            nodo = getattr(base, nombre, None)
            if nodo is not None:
                nodo.set_pos(x, 0, z)
        try:
            base.camLens.set_aspect_ratio(ar)
        except Exception:
            pass

        corto = float(min(w, h))
        m = max(10.0, round(corto * 0.035))
        gap = max(6.0, round(m * 0.4))
        self._margen, self._gap = m, gap

        # Joystick: radio proporcional al lado corto de la pantalla.
        radio = max(42.0, min(corto * 0.12, 110.0))
        perilla = max(14.0, radio * 0.36)
        self._radio, self._perilla = radio, perilla
        cx = m + radio
        cz = -(h - m - radio)
        self._centro_joy = (cx, cz)
        self.fondo.set_pos(cx, 0, cz)
        self.fondo["frameSize"] = (-radio, radio, -radio, radio)
        self.perilla["frameSize"] = (-perilla, perilla, -perilla, perilla)

        # Botones de la derecha, apilados en vertical.
        bw = max(110.0, min(w * 0.20, 240.0))
        bw = min(bw, max(110.0, w * 0.45))
        bh = max(40.0, min(h * 0.075, 64.0))
        self._bw, self._bh = bw, bh
        x_der = w - m - bw / 2
        self.boton_menu.set_pos(x_der, 0, -(h - m - bh / 2))
        self.boton_vista.set_pos(x_der, 0, -(h - m - bh - gap - bh / 2))
        fs = (-bw / 2, bw / 2, -bh / 2, bh / 2)
        esc_b = max(11.0, min(20.0, bh * 0.36))
        for boton in (self.boton_vista, self.boton_menu):
            boton["frameSize"] = fs
            boton["text_scale"] = (esc_b, esc_b)

        # Panel: encima de los botones; 2 columnas si la pantalla es baja/estrecha.
        n = max(1, len(self._botones_acceso))
        columnas = 1
        if n > 4 and h < 560:
            columnas = 2
        elif n > 6 and w < 560:
            columnas = 2
        filas = (n + columnas - 1) // columnas
        fila_h = max(30.0, bh * 0.9)
        panel_w = max(180.0, w * 0.46)
        panel_w = min(panel_w, w - 2 * m)
        panel_w = min(panel_w, w - m - (m + 2 * radio + 6.0) - m)
        panel_w = max(140.0, panel_w)
        z0 = -(h - m - 2 * bh - gap - 12.0)
        alto_disponible = (-(m + 4.0)) - z0
        panel_h = filas * fila_h + 18.0
        if panel_h > alto_disponible:
            fila_h = max(24.0, (alto_disponible - 18.0) / filas)
            panel_h = filas * fila_h + 18.0
        self._panel_w, self._panel_h, self._panel_z0 = panel_w, panel_h, z0
        self.panel_menu.set_pos(w - m - panel_w / 2, 0, z0 + panel_h / 2)
        self.panel_menu["frameSize"] = (-panel_w / 2, panel_w / 2, -panel_h / 2, panel_h / 2)

        ancho_celda = panel_w / columnas
        esc_p = max(10.0, min(18.0, fila_h * 0.36))
        self._columnas, self._ancho_celda, self._esc_p = columnas, ancho_celda, esc_p
        for idx, boton in enumerate(self._botones_acceso):
            col = idx % columnas
            fila = idx // columnas
            bx = -panel_w / 2 + ancho_celda * (col + 0.5)
            bz = panel_h / 2 - 9.0 - fila_h * (fila + 0.5)
            boton.set_pos(bx, 0, bz)
            boton["frameSize"] = (-ancho_celda * 0.46, ancho_celda * 0.46,
                                  -fila_h * 0.40, fila_h * 0.40)
            boton["text_scale"] = (esc_p, esc_p)

        # Zonas pulsables en coordenadas de pixel2d (para no depender de DirectGui).
        x_btn = w - m - bw / 2
        z_menu = -(h - m - bh / 2)
        z_vista = -(h - m - bh - gap - bh / 2)
        self._rects["menu"] = (x_btn - bw / 2, x_btn + bw / 2,
                               z_menu - bh / 2, z_menu + bh / 2)
        self._rects["vista"] = (x_btn - bw / 2, x_btn + bw / 2,
                                z_vista - bh / 2, z_vista + bh / 2)
        panel_cx = w - m - panel_w / 2
        panel_cz = z0 + panel_h / 2
        self._rects["panel"] = (panel_cx - panel_w / 2, panel_cx + panel_w / 2,
                                z0, z0 + panel_h)
        filas_rects = []
        for idx in range(n):
            col = idx % columnas
            fila = idx // columnas
            cx = panel_cx - panel_w / 2 + ancho_celda * (col + 0.5)
            cz = panel_cz + panel_h / 2 - 9.0 - fila_h * (fila + 0.5)
            hw = ancho_celda * 0.46
            hh = fila_h * 0.40
            filas_rects.append((cx - hw, cx + hw, cz - hh, cz + hh))
        self._rects["filas"] = filas_rects

        self._refrescar_textos()

    def _texto_corto(self, texto, ancho_px, escala):
        maximo = max(6, int((ancho_px - 14.0) / max(1.0, escala * 0.58)))
        return texto if len(texto) <= maximo else texto[:maximo - 2] + ".."

    def _refrescar_textos(self):
        self.boton_vista["text"] = self._texto_corto(self._nombre_vista, self._bw, max(11.0, self._bh * 0.36)) + " >"
        self.boton_menu["text"] = "Cerrar" if self.menu_abierto else "Vistas..."
        for idx, item in enumerate(self.vistas):
            nombre = item[0] if isinstance(item, (list, tuple)) else str(item)
            etiqueta = self._texto_corto(f"{idx + 1}. {nombre}", self._ancho_celda, self._esc_p)
            self._botones_acceso[idx]["text"] = etiqueta

    # ------------------------------------------------------------------ eventos
    def _toggle_menu(self):
        self.menu_abierto = not self.menu_abierto
        if self.menu_abierto:
            self.panel_menu.show()
        else:
            self.panel_menu.hide()
        self._refrescar_textos()

    def _ir_a_vista(self, indice):
        self.base.messenger.send("ir-a-vista", [indice])
        # Cerrar el panel tras seleccionar para no tapar la pantalla en m├│vil
        self.menu_abierto = False
        self.panel_menu.hide()
        self._refrescar_textos()

    def set_nombre_vista(self, nombre):
        """Actualiza el texto del bot├│n r├ípido al cambiar de vista."""
        self._nombre_vista = nombre
        self._refrescar_textos()

    def _siguiente_vista(self):
        self.base.messenger.send("vista-siguiente")

    def _a_pixel(self, m):
        return self.base.pixel2d.get_relative_point(
            self.base.render2d, Point3(m.get_x(), 0, m.get_y())
        )

    @staticmethod
    def _en_rect(x, z, rect):
        if not rect:
            return False
        return rect[0] <= x <= rect[1] and rect[2] <= z <= rect[3]

    def manejar_toque_ui(self, m):
        """Atiende botones/men├║ y devuelve True si el toque cay├│ en la interfaz."""
        if not self.activo:
            return False
        pt = self._a_pixel(m)
        x, z = pt.x, pt.z
        if self.menu_abierto:
            for idx, rect in enumerate(self._rects["filas"]):
                if self._en_rect(x, z, rect):
                    self._ir_a_vista(idx)
                    return True
        if self._en_rect(x, z, self._rects["menu"]):
            self._toggle_menu()
            return True
        if self._en_rect(x, z, self._rects["vista"]):
            self._siguiente_vista()
            return True
        if self.menu_abierto and self._en_rect(x, z, self._rects["panel"]):
            return True
        return False

    def procesar_toque(self, m):
        """Devuelve True si el toque cay├│ en el ├írea del joystick virtual."""
        if not self.activo:
            return False
        pt = self._a_pixel(m)
        dx = pt.x - self._centro_joy[0]
        dz = pt.z - self._centro_joy[1]
        # Margen amplio y c├│modo para dedos en pantalla t├íctil
        if dx * dx + dz * dz <= (self._radio * 1.7) ** 2:
            self.arrastrando = True
            self.controles.joystick_activo = True
            self._aplicar_desplazamiento(dx, dz)
            return True
        return False

    def actualizar_arrastre(self, m):
        if not self.arrastrando:
            return
        pt = self._a_pixel(m)
        self._aplicar_desplazamiento(
            pt.x - self._centro_joy[0], pt.z - self._centro_joy[1]
        )

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
        # Detecta cambios de tama├▒o u orientaci├│n del navegador/dispositivo.
        self._reubicar()

    def alternar(self):
        self.activo = not self.activo
        if self.activo:
            self.fondo.show()
            self.perilla.show()
            self.boton_vista.show()
            self.boton_menu.show()
            if self.menu_abierto:
                self.panel_menu.show()
        else:
            self.fondo.hide()
            self.perilla.hide()
            self.boton_vista.hide()
            self.boton_menu.hide()
            self.panel_menu.hide()
            self.menu_abierto = False
            self.soltar()
            self._refrescar_textos()
