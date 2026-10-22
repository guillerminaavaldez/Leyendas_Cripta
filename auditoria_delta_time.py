#!/usr/bin/env python3
"""
=============================================================================
  AUDITORÍA DE DELTA TIME — Leyendas de la Cripta
=============================================================================

Verifica que el motor produce resultados independientes del frame-rate.

Uso:
    python auditoria_delta_time.py

Requisitos:
    - Se ejecuta sin ventana visible (SDL_VIDEODRIVER=dummy).
    - Simula 1 segundo de tiempo real a 30, 60 y 120 FPS.
    - La flecha derecha está presionada (héroe avanza en X).
    - No hay obstáculos en la escena.
    - Tolerancia máxima de desviación: 5 % sobre la velocidad esperada.

Salida:
    Tabla comparativa en consola (español) + código de salida 0/1.
=============================================================================
"""
import os
import sys
from collections import defaultdict

# ── Modo sin ventana ──────────────────────────────────────────────────────────
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Asegurar que las importaciones relativas del proyecto funcionen
_RAIZ = os.path.dirname(os.path.abspath(__file__))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

import pygame
import pygame.display

# ── Constantes del proyecto ───────────────────────────────────────────────────
from config import (
    ANCHO,
    ALTO,
    DT_MAX,
    VELOCIDAD_HEROE,
    VELOCIDAD_ENEMIGO,
    ESCENA_NIVEL_1,
)
from src.gestor_escenas import GestorEscenas
from src.escenas.nivel1 import EscenaNivel1

# ── Parámetros de la auditoría ────────────────────────────────────────────────
DURACION_SEGUNDOS = 1.0          # Duración real de cada prueba
TOLERANCIA_PORCENTAJE = 5.0      # Margen aceptable de desviación (%)
FPS_A_PROBAR = [30, 60, 120]     # Tasas de cuadro a comparar


# ── Utilidades de presentación ────────────────────────────────────────────────

def _linea_separadora(ancho: int = 72) -> str:
    return "─" * ancho


def _encabezado(titulo: str, ancho: int = 72) -> str:
    margen = (ancho - len(titulo) - 2) // 2
    return "═" * margen + " " + titulo + " " + "═" * (ancho - margen - len(titulo) - 2)


# ── Escena instrumentada ──────────────────────────────────────────────────────

class EscenaNivel1Instrumentada(EscenaNivel1):
    """
    Subclase de EscenaNivel1 que:
      - Sobreescribe ``obtener_teclas()`` para inyectar flechas simuladas.
      - Elimina los obstáculos tras la inicialización (campo libre).
    """

    def __init__(self, gestor: GestorEscenas) -> None:
        super().__init__(gestor)
        # defaultdict(bool) devuelve False para teclas no definidas,
        # replicando el comportamiento de pygame.key.get_pressed().
        self._teclas_simuladas: defaultdict = defaultdict(bool)

    def simular_tecla(self, tecla: int, presionada: bool = True) -> None:
        """Activa o desactiva una tecla en el mapa interno de simulación."""
        self._teclas_simuladas[tecla] = presionada

    def obtener_teclas(self):
        """Devuelve el mapa de teclas simuladas en lugar del estado real del teclado."""
        return self._teclas_simuladas

    def al_entrar(self, **datos):
        super().al_entrar(**datos)
        # Eliminar obstáculos para medir desplazamiento puro sin colisiones
        self.obstaculos = []


# ── Núcleo de medición ────────────────────────────────────────────────────────

def medir_velocidad(fps_objetivo: int) -> dict:
    """
    Ejecuta el motor durante ``DURACION_SEGUNDOS`` a ``fps_objetivo`` FPS.

    Retorna un diccionario con los píxeles por segundo medidos para el
    héroe (eje X) y el enemigo (distancia euclidiana recorrida).
    """
    pygame.init()
    pygame.display.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    reloj = pygame.time.Clock()

    # Montar el gestor y la escena instrumentada
    gestor = GestorEscenas()
    escena = EscenaNivel1Instrumentada(gestor)
    gestor.registrar(ESCENA_NIVEL_1, escena)
    gestor.cambiar_escena(ESCENA_NIVEL_1)

    # Simular flecha derecha presionada para que el héroe avance en X
    escena.simular_tecla(pygame.K_RIGHT, True)

    # Guardar posiciones iniciales
    x0_heroe   = escena.jugador.x
    x0_enemigo = escena.enemigo.x
    y0_enemigo = escena.enemigo.y

    tiempo_acumulado = 0.0
    frames = 0

    while tiempo_acumulado < DURACION_SEGUNDOS:
        dt_real = reloj.tick(fps_objetivo) / 1000.0
        dt = min(dt_real, DT_MAX)
        tiempo_acumulado += dt
        frames += 1
        gestor.actualizar(dt)

    # Calcular desplazamientos reales
    dx_heroe   = escena.jugador.x - x0_heroe
    dx_enemigo = escena.enemigo.x - x0_enemigo
    dy_enemigo = escena.enemigo.y - y0_enemigo
    dist_enemigo = (dx_enemigo ** 2 + dy_enemigo ** 2) ** 0.5

    pygame.quit()

    return {
        "fps": fps_objetivo,
        "frames": frames,
        "tiempo_real": tiempo_acumulado,
        "px_s_heroe":   dx_heroe   / tiempo_acumulado,
        "px_s_enemigo": dist_enemigo / tiempo_acumulado,
    }


# ── Evaluación de desviación ──────────────────────────────────────────────────

def evaluar_desviacion(mediciones: list, campo: str, esperado: float):
    """
    Compara cada medición contra el valor esperado.
    Retorna (todo_ok, lista de desviaciones porcentuales).
    """
    desviaciones = []
    todo_ok = True
    for m in mediciones:
        valor = m[campo]
        desv = abs(valor - esperado) / esperado * 100.0 if esperado > 0 else 0.0
        desviaciones.append(desv)
        if desv > TOLERANCIA_PORCENTAJE:
            todo_ok = False
    return todo_ok, desviaciones


# ── Presentación de la tabla ──────────────────────────────────────────────────

def imprimir_tabla(mediciones: list, desv_heroe: list, desv_enemigo: list) -> None:
    col = 10
    print()
    print(_encabezado("AUDITORÍA DE DELTA TIME — Leyendas de la Cripta"))
    print()
    print(f"  Duración de cada prueba : {DURACION_SEGUNDOS:.1f} s")
    print(f"  Tolerancia máxima       : {TOLERANCIA_PORCENTAJE:.1f} %")
    print(f"  Velocidad teórica héroe : {VELOCIDAD_HEROE:.1f} px/s")
    print(f"  Velocidad teórica enem. : {VELOCIDAD_ENEMIGO:.1f} px/s")
    print()
    print(_linea_separadora())
    print(
        f"  {'FPS':>{col}} | {'Frames':>{col}} | "
        f"{'Héroe px/s':>{col}} | {'Desv.%':>{col}} | "
        f"{'Enem. px/s':>{col}} | {'Desv.%':>{col}}"
    )
    print(_linea_separadora())

    for i, m in enumerate(mediciones):
        ok_h = "OK" if desv_heroe[i]   <= TOLERANCIA_PORCENTAJE else "FALLA"
        ok_e = "OK" if desv_enemigo[i] <= TOLERANCIA_PORCENTAJE else "FALLA"
        print(
            f"  {m['fps']:>{col}} | {m['frames']:>{col}} | "
            f"{m['px_s_heroe']:>{col}.2f} | "
            f"{desv_heroe[i]:>{col-2}.2f} {ok_h:>5} | "
            f"{m['px_s_enemigo']:>{col}.2f} | "
            f"{desv_enemigo[i]:>{col-2}.2f} {ok_e:>5}"
        )

    print(_linea_separadora())
    print()


# ── Punto de entrada ──────────────────────────────────────────────────────────

def main() -> int:
    """
    Ejecuta la auditoría y devuelve 0 si todas las métricas pasan,
    o 1 si alguna supera la tolerancia.
    """
    print()
    print("Iniciando auditoría de delta time...")
    print(f"Tasas de cuadro a probar: {FPS_A_PROBAR} FPS\n")

    mediciones = []
    for fps in FPS_A_PROBAR:
        print(f"  Midiendo a {fps:>3} FPS... ", end="", flush=True)
        resultado = medir_velocidad(fps)
        mediciones.append(resultado)
        print(
            f"héroe={resultado['px_s_heroe']:6.1f} px/s  "
            f"enemigo={resultado['px_s_enemigo']:6.1f} px/s  "
            f"({resultado['frames']} frames)"
        )

    # Evaluar desviaciones respecto al valor teórico
    ok_heroe,   desv_heroe   = evaluar_desviacion(mediciones, "px_s_heroe",   VELOCIDAD_HEROE)
    ok_enemigo, desv_enemigo = evaluar_desviacion(mediciones, "px_s_enemigo", VELOCIDAD_ENEMIGO)

    imprimir_tabla(mediciones, desv_heroe, desv_enemigo)

    if ok_heroe and ok_enemigo:
        print("  RESULTADO: APROBADO — el motor es determinístico e independiente del FPS.")
        print()
        return 0
    else:
        print(
            f"  RESULTADO: FALLIDO — Se detectaron desviaciones superiores al "
            f"{TOLERANCIA_PORCENTAJE:.0f} %."
        )
        if not ok_heroe:
            for i, m in enumerate(mediciones):
                if desv_heroe[i] > TOLERANCIA_PORCENTAJE:
                    print(f"     • Héroe   a {m['fps']} FPS: desviación {desv_heroe[i]:.2f}%")
        if not ok_enemigo:
            for i, m in enumerate(mediciones):
                if desv_enemigo[i] > TOLERANCIA_PORCENTAJE:
                    print(f"     • Enemigo a {m['fps']} FPS: desviación {desv_enemigo[i]:.2f}%")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
