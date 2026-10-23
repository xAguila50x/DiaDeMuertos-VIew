# escena.py - Construcción del mundo "Camino de Cempasúchil" (port de Escena.cpp).
#
# Distribución (vista superior, eje -Z = norte):
#
#          [ casa de adobe con portal ]  z = -16
#              altar + arco + ofrendas
#                    |
#      faroles  ~ camino de pétalos ~  papel picado      (spline Catmull-Rom)
#                    |
#          [ portada del panteón ]       z = +16
#        tumbas, criptas, cruz atrial, cipreses

import math

from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    SamplerState,
    TextureStage,
    Vec2,
    Vec3,
    Vec4,
)

from .azar import Azar
from .camino import Camino
from .config import ruta_asset

# Catálogo de modelos: clave de archivo, título, descripción y origen.
PROPIOS = [
    ("altar_muertos", "Altar de muertos", "Tres niveles escalonados."),
    ("arco_cempasuchil", "Arco de cempasúchil", "Marco cubierto de cempasúchil."),
    ("flor_cempasuchil", "Flor de cempasúchil", "Cabeza de 39 pétalos."),
    ("petalo_cempasuchil", "Pétalo de cempasúchil", "Pieza del camino."),
    ("veladora", "Veladora", "Vaso, cera, mecha y flama."),
    ("cirio", "Cirio con candelero", "Vela alta sobre candelero."),
    ("pan_de_muerto", "Pan de muerto", "Domo con huesitos."),
    ("calaverita_azucar", "Calaverita de azúcar", "Esfera decorada."),
    ("papel_picado", "Papel picado", "Cordel con banderitas."),
    ("sahumerio", "Sahumerio", "Copalero de barro."),
    ("portarretrato", "Portarretrato", "Marco con fotografía."),
    ("jarron_talavera", "Jarrón de Talavera", "Cerámica azul cobalto."),
    ("vaso_agua", "Vaso con agua", "Vidrio y agua translúcidos."),
    ("maceta_cempasuchil", "Maceta con cempasúchil", "Maceta con siete flores."),
    ("mariposa_monarca", "Mariposa monarca", "Cuerpo y alas articuladas."),
    ("farol", "Farol de hojalata", "Poste, brazo, lámpara y vela."),
    ("entrada_panteon", "Portada del panteón", "Pilastras, arco, cruz y reja."),
    ("casa_adobe", "Casa de adobe con portal", "Muros, techo de teja y portal."),
]

LIBRERIA = [
    ("grave", "Tumba de tierra"),
    ("grave-border", "Tumba con bordillo"),
    ("gravestone-cross", "Lápida con cruz"),
    ("gravestone-round", "Lápida redonda"),
    ("gravestone-bevel", "Lápida biselada"),
    ("gravestone-decorative", "Lápida decorativa"),
    ("cross-wood", "Cruz de madera"),
    ("cross-column", "Cruz atrial"),
    ("crypt", "Cripta"),
    ("iron-fence", "Reja de hierro"),
    ("stone-wall", "Barda de piedra"),
    ("stone-wall-column", "Columna de barda"),
    ("pine", "Ciprés"),
    ("pine-crooked", "Ciprés torcido"),
    ("bench", "Banca"),
    ("urn-round", "Urna funeraria"),
    ("pumpkin", "Calabaza de Castilla"),
    ("pumpkin-tall", "Calabaza alargada"),
    ("rocks", "Rocas"),
    ("candle-multiple", "Velas"),
    ("detail-bowl", "Cazuela"),
    ("detail-plate", "Plato"),
    ("character-skeleton", "Esqueleto (calaca)"),
    ("character-ghost", "Ánima"),
    ("character-keeper", "Panteonero"),
]


def alinear_x(d):
    """Ángulo (grados) que alinea el eje local +X con la dirección horizontal d."""
    return math.degrees(math.atan2(-d.z, d.x))


def alinear_z(d):
    """Ángulo (grados) que alinea el eje local +Z con d."""
    return math.degrees(math.atan2(d.x, d.z))


class Escena:
    def __init__(self, base):
        self.base = base
        self.raiz = base.render.attach_new_node("Escena")
        self.modelos = {}
        self.catalogo = []
        self.usos = {}
        self.camino = Camino()
        self.texturas = {}
        self.vistas = []

    # ------------------------------------------------------------------ carga
    def cargar(self):
        print("ESCENA: cargar inicio", flush=True)
        self._cargar_modelos()
        print("ESCENA: modelos OK", flush=True)
        self._crear_procedurales()
        self._crear_luces()
        self._cargar_skybox()
        print("ESCENA: procedurales/luces/skybox OK", flush=True)

        self._construir_casa_y_ofrenda()
        print("ESCENA: casa/ofrenda OK", flush=True)
        self._construir_camino()
        print("ESCENA: camino OK", flush=True)
        self._construir_panteon()
        print("ESCENA: panteon OK", flush=True)
        self._construir_alrededores()
        print("ESCENA: alrededores OK", flush=True)

        self._definir_vistas()
        print("ESCENA: cargar fin", flush=True)

    def _cargar_modelos(self):
        for clave, titulo, desc in PROPIOS:
            self._cargar_uno(clave, ruta_asset("models/propios/%s.gltf" % clave), titulo, desc, "Propio")
        for clave, titulo in LIBRERIA:
            self._cargar_uno(
                clave, ruta_asset("models/libreria/kenney_graveyard/%s.glb" % clave), titulo, "Librería", "Librería"
            )

    def _cargar_uno(self, clave, ruta, titulo, desc, origen):
        nodo = self.base.loader.load_model(ruta)
        nodo.set_light_off()
        self._vincular_material(nodo)
        self.modelos[clave] = nodo
        self.catalogo.append((clave, titulo, desc, origen))
        self.usos[clave] = 0

    def _vincular_material(self, nodo):
        """Pasa los uniforms de material por defecto sin sobreescribir texturas.
        Panda3D enlaza automáticamente p3d_Texture0 y p3d_Material a cada geom."""
        nodo.set_shader_input("uEscalaUV", Vec2(1, 1))
        nodo.set_shader_input("uTinte", Vec4(1, 1, 1, 1))
        nodo.set_shader_input("uColor", Vec4(1, 1, 1, 1))
        nodo.set_shader_input("uMetalico", 0.0)
        nodo.set_shader_input("uRugosidad", 0.8)
        nodo.set_shader_input("uEmision", Vec3(0, 0, 0))
        nodo.set_shader_input("uModoAlfa", 0)
        nodo.set_shader_input("uCorte", 0.5)

    # -------------------------------------------------------------- procedural
    def _crear_procedurales(self):
        # Terreno: plano de 200 x 200 m con textura repetida.
        from panda3d.core import CardMaker

        cm = CardMaker("terreno")
        cm.set_frame(-100, 100, -100, 100)
        terreno = self.raiz.attach_new_node(cm.generate())
        terreno.set_p(-90)
        terreno.set_pos(0, 0, 0)
        self._aplicar_textura_repetida(terreno, "textures/tierra.jpg", 40, 40)
        self._guardar_procedural("terreno", terreno, "Terreno", "Plano de 200 x 200 m.")

    def _aplicar_textura_repetida(self, np, rel, u, v):
        tex = self.base.loader.load_texture(ruta_asset(rel))
        tex.set_wrap_u(SamplerState.WM_repeat)
        tex.set_wrap_v(SamplerState.WM_repeat)
        np.set_texture(tex)
        np.set_shader_input("uEscalaUV", Vec2(u, v))
        np.set_shader_input("uTinte", Vec4(1, 1, 1, 1))
        np.set_shader_input("uColor", Vec4(1, 1, 1, 1))
        np.set_shader_input("uMetalico", 0.0)
        np.set_shader_input("uRugosidad", 0.95)
        np.set_shader_input("uEmision", Vec3(0, 0, 0))
        np.set_shader_input("uModoAlfa", 0)
        np.set_shader_input("uCorte", 0.5)

    def _guardar_procedural(self, clave, np, titulo, desc):
        self.modelos[clave] = np
        self.catalogo.append((clave, titulo, desc, "Procedural"))
        self.usos[clave] = 0

    def _crear_luces(self):
        sol = DirectionalLight("sol")
        sol.set_color(Vec4(1.0, 0.78, 0.52, 1.0) * 1.2)
        nodo_sol = self.raiz.attach_new_node(sol)
        nodo_sol.set_hpr(-35, -22, 0)
        self.raiz.set_light(nodo_sol)

        amb = AmbientLight("amb")
        amb.set_color(Vec4(0.38, 0.32, 0.42, 1.0))
        self.raiz.set_light(self.raiz.attach_new_node(amb))

        # Luz puntual cálida en la portada de la entrada
        from panda3d.core import PointLight
        luz_ent = PointLight("luz_entrada")
        luz_ent.set_color(Vec4(1.0, 0.75, 0.38, 1.0) * 2.8)
        luz_ent.set_attenuation(Vec3(1.0, 0.08, 0.012))
        nodo_ent = self.raiz.attach_new_node(luz_ent)
        nodo_ent.set_pos(0.0, 3.2, 15.4)
        self.raiz.set_light(nodo_ent)

    def _cargar_skybox(self):
        from panda3d.core import CardMaker, SamplerState
        self.base.set_background_color(Vec4(0.35, 0.28, 0.40, 1.0))
        sky = self.base.render.attach_new_node("Skybox")
        sky.set_bin("background", 0)
        sky.set_depth_write(False)
        sky.set_light_off()
        sky.set_shader_off()
        self.skybox = sky

        D = 180.0
        caras = [
            ("pz", (0, 0, D), (180, 0, 0)),
            ("nz", (0, 0, -D), (0, 0, 0)),
            ("px", (D, 0, 0), (-90, 0, 0)),
            ("nx", (-D, 0, 0), (90, 0, 0)),
            ("py", (0, D, 0), (0, -90, 0)),
            ("ny", (0, -D, 0), (0, 90, 0)),
        ]
        for nombre, pos, hpr in caras:
            try:
                cm = CardMaker(nombre)
                cm.set_frame(-D, D, -D, D)
                np = sky.attach_new_node(cm.generate())
                np.set_pos(Vec3(pos))
                np.set_hpr(Vec3(hpr))
                tex = self.base.loader.load_texture(ruta_asset("skybox/atardecer/%s.jpg" % nombre))
                if tex:
                    tex.set_wrap_u(SamplerState.WM_clamp)
                    tex.set_wrap_v(SamplerState.WM_clamp)
                    np.set_texture(tex)
            except Exception as e:
                print("Aviso skybox cara %s:" % nombre, e)

    def actualizar_camara(self, pos):
        if getattr(self, "skybox", None):
            self.skybox.set_pos(pos)

    # -------------------------------------------------------------- instancias
    def modelo(self, clave):
        return self.modelos.get(clave)

    def instanciar(self, clave, padre, nombre, pos, rot_y=0.0, escala=1.0):
        modelo = self.modelos.get(clave)
        if modelo is None:
            return padre
        # Comparte la geometría (instanciado): ideal para pétalos, veladoras y bardas.
        np = modelo.instance_under_node(padre, nombre)
        np.set_pos(Vec3(pos))
        np.set_hpr(rot_y, 0, 0)
        np.set_scale(escala)
        self.usos[clave] = self.usos.get(clave, 0) + 1
        return np

    # ------------------------------------------------------- casa y ofrenda
    def _construir_casa_y_ofrenda(self):
        azar = Azar()
        casa = self.raiz.attach_new_node("Casa")
        casa.set_pos(0.0, 0.0, -16.0)
        self.instanciar("casa_adobe", casa, "casa_adobe", (0, 0, 0))

        ofrenda = casa.attach_new_node("Ofrenda")
        ofrenda.set_pos(0.0, 0.15, 0.95)
        altar = self.instanciar("altar_muertos", ofrenda, "altar", (0, 0, 0))
        self.instanciar("arco_cempasuchil", ofrenda, "arco", (0.0, 0.0, -0.55), 0.0, 0.95)

        n1 = altar.find("**/nivel_1")
        n2 = altar.find("**/nivel_2")
        n3 = altar.find("**/nivel_3")
        sup = 0.455

        for s in (-1.0, 1.0):
            self.instanciar("cirio", n1, "cirio", (s * 1.05, sup, 0.58))
            self.instanciar("pan_de_muerto", n1, "pan", (s * 0.70, sup, 0.58), azar(0, 90))
            self.instanciar("veladora", n1, "veladora", (s * 0.40, sup, 0.60))
            self.instanciar("calaverita_azucar", n1, "calaverita", (s * 0.20, sup, 0.62), -s * 12.0, 0.8)
        self.instanciar("detail-bowl", n1, "cazuela_mole", (0.10, sup, 0.50), 0.0, 0.9)

        jarron = self.instanciar("jarron_talavera", n2, "jarron", (-0.72, sup, 0.22), 20.0)
        for k in range(3):
            a = 120.0 * k
            self.instanciar(
                "flor_cempasuchil", jarron, "flor", (0.02 * math.cos(math.radians(a)), 0.18, 0.02 * math.sin(math.radians(a))), a
            )
        self.instanciar("vaso_agua", n2, "vaso_agua", (0.72, sup, 0.22))
        for s in (-1.0, 1.0):
            self.instanciar("calaverita_azucar", n2, "calaverita", (s * 0.38, sup, 0.24), -s * 8.0)
        plato = self.instanciar("detail-plate", n2, "plato", (0.0, sup, 0.22))
        self.instanciar("pan_de_muerto", plato, "pan_plato", (0.0, 0.03, 0.0), 30.0, 0.75)

        self.instanciar("cross-wood", n3, "cruz", (0.0, sup, -0.62), 0.0, 0.5)
        self.instanciar("portarretrato", n3, "foto_izq", (-0.42, sup, -0.30), 14.0)
        self.instanciar("portarretrato", n3, "foto_centro", (0.0, sup, -0.36))
        self.instanciar("portarretrato", n3, "foto_der", (0.42, sup, -0.30), -14.0)
        for s in (-1.0, 1.0):
            self.instanciar("veladora", n3, "veladora", (s * 0.60, sup, -0.05))
            self.instanciar("calaverita_azucar", n3, "calaverita", (s * 0.22, sup, -0.02), -s * 10.0, 0.75)

        self.instanciar("sahumerio", ofrenda, "sahumerio", (0.0, 0.012, 1.20), 35.0)
        for i, p in enumerate([(-0.55, 0.012, 1.0), (0.55, 0.012, 1.0), (-0.75, 0.012, 1.6), (0.75, 0.012, 1.6)]):
            self.instanciar("veladora", ofrenda, "veladora_piso_%d" % i, p)
        for s in (-1.0, 1.0):
            self.instanciar("maceta_cempasuchil", ofrenda, "maceta", (s * 1.55, 0.0, 0.25), s * 40.0)
            self.instanciar("pumpkin" if s < 0 else "pumpkin-tall", ofrenda, "calabaza", (s * 1.55, 0.0, 0.95), s * 25.0, 0.85)

        # Cruz de pétalos (instanciado)
        self._cruz_de_petalos(ofrenda, azar)

        # Papel picado colgado bajo el techo del portal
        for z in (1.75, 2.75):
            for x in (-1.6, 1.6):
                self.instanciar("papel_picado", casa, "papel_picado_portal", (x, 2.45, z))

        self.instanciar("farol", casa, "farol_portal_izq", (-4.3, 0.0, 3.7), 0.0)
        self.instanciar("farol", casa, "farol_portal_der", (4.3, 0.0, 3.7), 180.0)
        self.instanciar("pumpkin", casa, "calabaza_portal_1", (-2.6, 0.15, 2.9), 15.0)
        self.instanciar("pumpkin", casa, "calabaza_portal_2", (-2.25, 0.15, 3.05), 70.0, 0.75)
        self.instanciar("pumpkin-tall", casa, "calabaza_portal_3", (2.5, 0.15, 2.95), -30.0, 0.9)
        self.instanciar("maceta_cempasuchil", casa, "maceta_portal_1", (-3.2, 0.15, 2.4), 10.0)
        self.instanciar("maceta_cempasuchil", casa, "maceta_portal_2", (3.2, 0.15, 2.4), -20.0)

        # Mariposas monarca alrededor del arco
        for p in [(-1.1, 2.5, 1.6), (0.8, 2.2, 2.3), (1.7, 1.6, 1.2)]:
            self.instanciar("mariposa_monarca", casa, "mariposa_portal", p, azar(0, 360), 1.5)

    def _cruz_de_petalos(self, padre, azar):
        for i in range(520):
            if i % 3 == 0:
                p = (azar(-0.42, 0.42), 0.014 + azar(0.0, 0.004), 1.30 + azar(-0.07, 0.07))
            else:
                p = (azar(-0.07, 0.07), 0.014 + azar(0.0, 0.004), azar(0.95, 1.95))
            self.instanciar("petalo_cempasuchil", padre, "petalo", p, azar(0, 360), azar(0.8, 1.2))

    # ------------------------------------------------------------------ camino
    def _construir_camino(self):
        azar = Azar()
        grupo = self.raiz.attach_new_node("Camino de cempasúchil")
        self.camino.construir(
            [
                (0.0, 0.0, 19.0),
                (0.0, 0.0, 14.0),
                (-2.2, 0.0, 8.5),
                (1.6, 0.0, 2.5),
                (-1.3, 0.0, -3.5),
                (0.6, 0.0, -8.5),
                (0.0, 0.0, -12.5),
            ]
        )
        L = self.camino.longitud()

        # Pétalos 3D a lo largo del camino
        n_petalos = 7000
        for i in range(n_petalos):
            s = azar(0.3, L - 0.2)
            lateral = max(-1.05, min(1.05, azar.normal(0.36)))
            c = self.camino.punto(s)
            ig = self.camino.izquierda(s)
            p = c + ig * lateral
            self.instanciar("petalo_cempasuchil", grupo, "petalo", (p.x, 0.016 + azar(0.0, 0.006), p.z), azar(0, 360), azar(1.0, 1.6))

        # Veladoras a ambos lados
        s = 1.2
        while s < L - 0.8:
            for lado in (-1.0, 1.0):
                c = self.camino.punto(s + lado * 0.35)
                ig = self.camino.izquierda(s)
                p = c + ig * (lado * 1.22)
                p.set_y(0.008)
                self.instanciar("veladora", grupo, "veladora", (p.x, p.y, p.z), azar(0, 360))
            s += 2.2

        # Pares de faroles con tira de papel picado
        for k, s in enumerate((5.0, 11.5, 18.0, 24.5)):
            c = self.camino.punto(s)
            ig = self.camino.izquierda(s)
            par = grupo.attach_new_node("faroles_%d" % k)
            par.set_pos(c)
            hacia_casa = alinear_x(self.camino.tangente(s))
            self.instanciar("farol", par, "farol_izq", ig * 1.55, hacia_casa)
            self.instanciar("farol", par, "farol_der", -ig * 1.55, hacia_casa)
            self.instanciar("papel_picado", par, "papel_picado", (0.0, 2.52, 0.0), alinear_x(-ig))

        # Bancas
        for s, lado in ((8.0, 1.0), (20.5, -1.0)):
            ig = self.camino.izquierda(s)
            p = self.camino.punto(s) + ig * (lado * 2.7)
            self.instanciar("bench", grupo, "banca", (p.x, p.y, p.z), alinear_z(-ig * lado), 1.8)

        # Mariposas sobre el camino
        for s in (3.0, 7.5, 9.0, 13.0, 16.5, 21.0, 23.0, 27.5, 30.0):
            c = self.camino.punto(s)
            ig = self.camino.izquierda(s)
            p = c + ig * azar(-1.3, 1.3)
            p.set_y(azar(1.0, 2.4))
            self.instanciar("mariposa_monarca", grupo, "mariposa", (p.x, p.y, p.z), azar(0, 360), 1.5)

        # Personajes
        s = 13.0
        self.instanciar("character-skeleton", grupo, "calaca_caminante", self.camino.punto(s), alinear_z(self.camino.tangente(s)), 2.0)
        s2 = 9.0
        p = self.camino.punto(s2) - self.camino.izquierda(s2) * 1.9
        p.set_y(0.35)
        self.instanciar("character-ghost", grupo, "anima", (p.x, p.y, p.z), alinear_z(self.camino.tangente(s2)), 1.7)

    # ----------------------------------------------------------------- panteón
    def _construir_panteon(self):
        azar = Azar()
        panteon = self.raiz.attach_new_node("Panteón")
        self.instanciar("entrada_panteon", panteon, "portada", (0.0, 0.0, 16.0), 180.0)
        self.instanciar("character-keeper", panteon, "panteonero", (3.4, 0.0, 14.6), 200.0, 2.0)

        # Faroles que iluminan la portada de entrada
        self.instanciar("farol", panteon, "farol_entrada_izq", (-2.2, 0.0, 15.6), 0.0, 1.2)
        self.instanciar("farol", panteon, "farol_entrada_der", (2.2, 0.0, 15.6), 180.0, 1.2)

        # Veladoras y macetas de cempasúchil en la entrada
        for s in (-1.0, 1.0):
            self.instanciar("veladora", panteon, "veladora_pilar", (s * 1.9, 0.0, 15.7), azar(0, 360), 1.3)
            self.instanciar("veladora", panteon, "veladora_pilar2", (s * 2.3, 0.0, 15.8), azar(0, 360), 1.3)
            self.instanciar("maceta_cempasuchil", panteon, "maceta_entrada", (s * 2.6, 0.0, 15.4), azar(0, 360), 1.2)

        reja = panteon.attach_new_node("reja_frontal")
        for i in range(6):
            for s in (-1.0, 1.0):
                self.instanciar("iron-fence", panteon, "reja", (s * (3.0 + 2.0 * i), 0.0, 16.65), 0.0, 2.0)

        for i in range(9):
            z = 17.0 + 2.0 * i
            self.instanciar("stone-wall", panteon, "barda", (-13.2, 0.0, z), 90.0, 2.0)
            self.instanciar("stone-wall", panteon, "barda", (13.2, 0.0, z), -90.0, 2.0)
        for i in range(14):
            self.instanciar("stone-wall", panteon, "barda", (-13.0 + 2.0 * i, 0.0, 33.2), 180.0, 2.0)
        for p in ((-14.0, 0, 16.6), (14.0, 0, 16.6), (-14.0, 0, 34.0), (14.0, 0, 34.0)):
            self.instanciar("stone-wall-column", panteon, "columna", (p[0], p[1], p[2] + 0.8), 0.0, 2.0)

        tumbas = panteon.attach_new_node("Tumbas")
        lapidas = ["gravestone-cross", "gravestone-round", "gravestone-bevel", "gravestone-decorative", "cross-wood"]
        k = 0
        for z in (19.8, 23.6, 27.4):
            for x in (-11.0, -7.5, -4.0, 4.0, 7.5, 11.0):
                k += 1
                t = tumbas.attach_new_node("tumba_%d" % k)
                t.set_pos(x + azar(-0.2, 0.2), 0.0, z + azar(-0.2, 0.2))
                t.set_hpr(azar(-4.0, 4.0), 0, 0)
                self.instanciar("grave", t, "monticulo", (0, 0, 0.05), 180.0, 2.0)
                self.instanciar("grave-border", t, "bordillo", (0, 0, 0), 180.0, 2.0)
                lap = lapidas[(k * 7) % 5]
                self.instanciar(lap, t, "lapida", (0.0, 0.0, 1.55), 180.0, 1.7 if lap == "cross-wood" else 1.6)
                for f in range(9):
                    self.instanciar("flor_cempasuchil", t, "flor", (azar(-0.40, 0.40), 0.22, azar(-0.9, 0.85)), azar(0, 360), azar(1.1, 1.5))
                for s in (-1.0, 1.0):
                    self.instanciar("veladora", t, "veladora", (s * 0.95, 0.0, -1.35), azar(0, 360))
                if k % 4 == 1:
                    self.instanciar("candle-multiple", t, "velas", (0.55, 0.0, 1.25), azar(0, 360), 1.2)
                if k % 5 == 2:
                    self.instanciar("urn-round", t, "urna", (-0.55, 0.0, 1.3), 0.0, 1.4)
                if k % 6 == 3:
                    self.instanciar("calaverita_azucar", t, "calaverita", (0.0, 0.22, -0.95), 0.0, 1.2)
                if k % 6 == 0:
                    self.instanciar("pan_de_muerto", t, "pan", (0.25, 0.2, -0.6), azar(0, 90))

        self.instanciar("crypt", panteon, "cripta_izq", (-9.0, 0.0, 31.0), 180.0, 3.0)
        self.instanciar("crypt", panteon, "cripta_der", (9.0, 0.0, 31.0), 180.0, 3.0)
        self.instanciar("cross-column", panteon, "cruz_atrial", (0.0, 0.0, 32.2), 180.0, 2.2)

        for z in (18.5, 25.0, 30.0):
            for x in (-12.4, 12.4):
                self.instanciar("pine", panteon, "cipres", (x, 0.0, z), azar(0, 360), azar(2.5, 3.0))
        for x in (-10.0, -4.0, 3.0, 9.5):
            self.instanciar("pine", panteon, "cipres", (x, 0.0, 36.0), azar(0, 360), azar(2.6, 3.2))

    # -------------------------------------------------------------- alrededores
    def _construir_alrededores(self):
        azar = Azar()
        grupo = self.raiz.attach_new_node("Alrededores")
        for p in (
            (-7.0, 0, 10.0), (6.5, 0, 6.0), (-6.5, 0, -1.0), (7.0, 0, -7.0), (-7.5, 0, -10.0),
            (8.0, 0, 12.0), (-9.5, 0, 3.0), (10.5, 0, 0.5), (-17.0, 0, 14.0), (18.0, 0, 10.0),
            (-12.0, 0, -20.0), (12.0, 0, -21.0),
        ):
            self.instanciar("pine-crooked", grupo, "arbol", p, azar(0, 360), azar(2.4, 3.2))

        for i in range(14):
            a = azar(0, 6.2831)
            r = azar(5.0, 22.0)
            px = math.cos(a) * r
            pz = math.sin(a) * r * 1.2
            if abs(px) < 3.5:
                px += -3.5 if px < 0 else 3.5
            if 15.0 < pz < 35.0 and abs(px) < 15.0:
                px = -16.5 if px < 0 else 16.5
            self.instanciar("rocks", grupo, "roca", (px, 0.0, pz), azar(0, 360), azar(1.0, 2.0))

        self.instanciar("casa_adobe", grupo, "casa_vecina_1", (-14.5, 0.0, -6.0), 75.0)
        self.instanciar("casa_adobe", grupo, "casa_vecina_2", (15.5, 0.0, -3.0), -80.0)

    # ------------------------------------------------------------------ vistas
    def _definir_vistas(self):
        c = self.camino
        self.vistas = [
            ("Vista libre", (-17.0, 12.0, 26.0), (0.0, 0.0, 2.0)),
            ("Vista general", (-17.0, 12.0, 26.0), (0.0, 0.0, 2.0)),
            ("Entrada del panteón", (1.2, 1.7, 8.5), (0.0, 2.2, 16.0)),
            ("Camino de pétalos", tuple(c.punto(3.0) + c.izquierda(3.0) * 0.8 + Vec3(0, 1.5, 0)), tuple(c.punto(14.0))),
            ("Altar de muertos", (0.5, 1.6, -10.0), (0.0, 1.15, -15.2)),
            ("Ofrenda (detalle)", (1.0, 1.35, -12.4), (0.0, 0.95, -15.1)),
            ("Panteón", (-11.0, 4.5, 15.0), (0.0, 0.5, 26.0)),
            ("Vista aérea", (0.0, 60.0, 21.0), (0.0, 0.0, 6.0)),
        ]
