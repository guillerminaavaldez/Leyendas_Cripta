# MODULARIZADO: Módulo de gestión y control del flujo de niveles
import pygame
try:
    from src.obstaculos import generar_obstaculos_nivel
except ModuleNotFoundError:
    from obstaculos import generar_obstaculos_nivel
from config import (
    ANCHO, ALTO, NIVEL_INICIAL, NIVEL_MAXIMO,
    POS_INICIAL_HEROE, POS_INICIAL_ENEMIGO
)


class GestorNiveles:
    def __init__(self, rect_meta: pygame.Rect):
        self.nivel_actual = NIVEL_INICIAL
        self.nivel_maximo = NIVEL_MAXIMO
        self.rect_meta = rect_meta

    def iniciar_nivel(self, num_nivel: int, jugador, enemigo) -> list:
        """
        MODULARIZADO: Configura las posiciones, estados y genera los obstáculos del nivel indicado.
        """
        self.nivel_actual = num_nivel

        # Restablecer estado y posición del jugador
        jugador.x, jugador.y = POS_INICIAL_HEROE
        jugador.actualizar_rect()
        jugador.colision_procesada = False
        jugador.ha_ganado = False
        jugador.vivo = True

        # Restablecer estado y posición del enemigo
        enemigo.x, enemigo.y = POS_INICIAL_ENEMIGO
        enemigo.actualizar_rect()
        enemigo.movimientos_retraso = 0
        enemigo.mostrar_prediccion = False

        # Generar obstáculos acordes al nivel
        obstaculos = generar_obstaculos_nivel(
            self.nivel_actual,
            ANCHO,
            ALTO,
            (jugador.x, jugador.y),
            (enemigo.x, enemigo.y),
            self.rect_meta
        )

        return obstaculos

    def avanzar_nivel(self, jugador, enemigo) -> tuple[int, list, str]:
        """
        MODULARIZADO: Avanza al siguiente nivel o pasa al estado de juego completado.
        Devuelve (nuevo_nivel, nuevos_obstaculos, nuevo_estado).
        """
        if self.nivel_actual < self.nivel_maximo:
            self.nivel_actual += 1
            obstaculos = self.iniciar_nivel(self.nivel_actual, jugador, enemigo)
            return self.nivel_actual, obstaculos, "jugando"
        else:
            return self.nivel_actual, [], "juego_completado"

    def reiniciar_partida(self, jugador, enemigo) -> list:
        """
        MODULARIZADO: Reinicia la partida desde el nivel 1 reseteando monedas e inventario.
        """
        self.nivel_actual = NIVEL_INICIAL
        jugador.monedas = 0
        jugador.pociones = {"retraso": 0, "salto": 0, "vision": 0}
        return self.iniciar_nivel(self.nivel_actual, jugador, enemigo)
