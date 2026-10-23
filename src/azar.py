# azar.py - Generador pseudoaleatorio con semilla fija (port de struct Azar).
# Garantiza que la escena sea idéntica en cada ejecución, igual que en C++.

import random


class Azar:
    def __init__(self, semilla=20261102):
        self.gen = random.Random(semilla)

    def __call__(self, a, b):
        return self.gen.uniform(a, b)

    def normal(self, sigma):
        return self.gen.gauss(0.0, sigma)
