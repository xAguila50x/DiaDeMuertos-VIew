# camino.py - Trayectoria del camino de cempasúchil (port de Camino.cpp).
#
# La ruta se define con pocos puntos de control y se interpola con una spline
# Catmull-Rom centrípeta (alfa = 0.5, algoritmo de Barry-Goldman). Se
# re-muestrea por longitud de arco para colocar objetos cada cierta distancia.

import math

from panda3d.core import Vec3


def _catmull_rom(p0, p1, p2, p3, u):
    def nudo(t, a, b):
        return t + max(math.sqrt((b - a).length()), 1e-4)

    t0 = 0.0
    t1 = nudo(t0, p0, p1)
    t2 = nudo(t1, p1, p2)
    t3 = nudo(t2, p2, p3)
    t = t1 + (t2 - t1) * u
    a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
    a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
    a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
    b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
    b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
    return b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1))


class Camino:
    def __init__(self):
        self.control = []
        self.muestras = []
        self.s = []

    def construir(self, control, muestras_por_tramo=24):
        control = [p if isinstance(p, Vec3) else Vec3(*p) for p in control]
        self.control = list(control)
        self.muestras = []
        self.s = []
        if len(control) < 2:
            return
        p = [control[0] * 2.0 - control[1]]
        p.extend(control)
        p.append(control[-1] * 2.0 - control[-2])
        for i in range(1, len(p) - 2):
            for k in range(muestras_por_tramo):
                self.muestras.append(_catmull_rom(p[i - 1], p[i], p[i + 1], p[i + 2], k / muestras_por_tramo))
        self.muestras.append(Vec3(control[-1]))
        self.s = [0.0] * len(self.muestras)
        for i in range(1, len(self.muestras)):
            self.s[i] = self.s[i - 1] + (self.muestras[i] - self.muestras[i - 1]).length()

    def longitud(self):
        return self.s[-1] if self.s else 0.0

    def punto(self, s):
        if not self.muestras:
            return Vec3(0)
        s = max(0.0, min(s, self.longitud()))
        # búsqueda binaria (equivale a std::upper_bound)
        lo, hi = 0, len(self.s)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.s[mid] <= s:
                lo = mid + 1
            else:
                hi = mid
        i = lo
        if i == 0:
            return Vec3(self.muestras[0])
        if i >= len(self.muestras):
            return Vec3(self.muestras[-1])
        tramo = self.s[i] - self.s[i - 1]
        f = (s - self.s[i - 1]) / tramo if tramo > 1e-6 else 0.0
        return self.muestras[i - 1] * (1.0 - f) + self.muestras[i] * f

    def tangente(self, s):
        h = 0.05
        d = self.punto(s + h) - self.punto(s - h)
        d.set_y(0.0)
        l = d.length()
        return d / l if l > 1e-6 else Vec3(0, 0, -1)

    def izquierda(self, s):
        t = self.tangente(s)
        return Vec3(t.z, 0.0, -t.x)
