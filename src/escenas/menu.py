"""
Módulo de la Escena del Menú Principal.
Presenta la pantalla de bienvenida y los accesos iniciales del juego.
"""
from __future__ import annotations
import math
from typing import TYPE_CHECKING, List

import pygame

from config import ANCHO, ALTO, ESCENA_NIVEL_1
from src.escenas.base import EscenaBase

if TYPE_CHECKING:
    from src.gestor_escenas import GestorEscenas


class EscenaMenu(EscenaBase):
    """
    Pantalla de inicio del videojuego.

    Muestra el título de la obra, una invitación a comenzar con efecto de parpadeo
    basado en tiempo real (dt), y las instrucciones básicas de salida.
    """

    # Paleta de colores acorde a la estética oscura de la cripta
    COLOR_FONDO: tuple[int, int, int] = (14, 18, 26)
    COLOR_TITULO: tuple[int, int, int] = (255, 215, 0)          # Dorado antiguo
    COLOR_SOMBRA_TITULO: tuple[int, int, int] = (40, 20, 10)     # Sombra profunda
    COLOR_TEXTO_COMBATIR: tuple[int, int, int] = (230, 240, 255) # Blanco frío
    COLOR_CONTROLES: tuple[int, int, int] = (140, 150, 175)      # Gris azulado tenue
    COLOR_BORDE_DECORATIVO: tuple[int, int, int] = (45, 55, 75)

    def __init__(self, gestor: GestorEscenas) -> None:
        """
        Inicializa las fuentes tipográficas y los acumuladores de tiempo de la escena.

        :param gestor: Referencia al GestorEscenas que controla el flujo de ejecución.
        """
        super().__init__(gestor)

        # Tipografías del menú
        self.fuente_titulo = pygame.font.Font(None, 64)
        self.fuente_prompt = pygame.font.Font(None, 34)
        self.fuente_ayuda = pygame.font.Font(None, 24)

        # Control de parpadeo basado en acumulación de tiempo (delta time)
        self.tiempo_acumulado: float = 0.0
        self.velocidad_parpadeo: float = 3.5  # Oscilaciones por segundo
        self.mostrar_prompt: bool = True

    def al_entrar(self, **datos) -> None:
        """Reinicia el temporizador de parpadeo al ingresar a la escena."""
        self.tiempo_acumulado = 0.0
        self.mostrar_prompt = True

    def manejar_eventos(self, eventos: List[pygame.event.Event]) -> None:
        """
        Gestiona la entrada del jugador para iniciar la partida o salir.

        :param eventos: Colección de eventos de Pygame en el frame actual.
        """
        for evento in eventos:
            if evento.type == pygame.QUIT:
                self.gestor.salir()

            elif evento.type == pygame.KEYDOWN:
                # [ESC] Finaliza la ejecución del juego
                if evento.key == pygame.K_ESCAPE:
                    self.gestor.salir()

                # [ENTER] Transiciona al primer nivel de la cripta
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.gestor.cambiar_escena(ESCENA_NIVEL_1, nivel=1)

    def actualizar(self, dt: float) -> None:
        """
        Acumula el tiempo transcurrido (dt) y calcula la visibilidad del llamado a la acción.

        Soporta dt tanto en segundos (convención estándar, ej. 0.016s) como en milisegundos.

        :param dt: Delta time entregado por el reloj de Pygame.
        """
        # Normalizar a segundos en caso de recibir milisegundos (dt > 1.0)
        dt_segundos = dt / 1000.0 if dt > 1.0 else dt
        self.tiempo_acumulado += dt_segundos

        # Función seno para determinar el estado de visibilidad sin depender de los FPS
        self.mostrar_prompt = math.sin(self.tiempo_acumulado * self.velocidad_parpadeo) > 0.0

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """
        Renderiza la composición visual del menú principal.

        :param pantalla: Superficie principal de renderizado de Pygame.
        """
        # 1. Fondo oscuro
        pantalla.fill(self.COLOR_FONDO)

        # 2. Marco decorativo sutil
        rect_marco = pygame.Rect(30, 30, ANCHO - 60, ALTO - 60)
        pygame.draw.rect(pantalla, self.COLOR_BORDE_DECORATIVO, rect_marco, width=2, border_radius=8)

        # 3. Título con efecto de sombra
        texto_titulo = "LEYENDAS DE LA CRIPTA"
        pos_y_titulo = ALTO // 3

        # Sombra proyectada
        surf_sombra = self.fuente_titulo.render(texto_titulo, True, self.COLOR_SOMBRA_TITULO)
        rect_sombra = surf_sombra.get_rect(center=(ANCHO // 2 + 3, pos_y_titulo + 3))
        pantalla.blit(surf_sombra, rect_sombra)

        # Texto frontal del título
        surf_titulo = self.fuente_titulo.render(texto_titulo, True, self.COLOR_TITULO)
        rect_titulo = surf_titulo.get_rect(center=(ANCHO // 2, pos_y_titulo))
        pantalla.blit(surf_titulo, rect_titulo)

        # 4. Texto interactivo con parpadeo basado en dt
        if self.mostrar_prompt:
            surf_prompt = self.fuente_prompt.render(
                "Presiona ENTER para combatir", True, self.COLOR_TEXTO_COMBATIR
            )
            rect_prompt = surf_prompt.get_rect(center=(ANCHO // 2, ALTO // 2 + 40))
            pantalla.blit(surf_prompt, rect_prompt)

        # 5. Línea de ayuda de controles
        surf_ayuda = self.fuente_ayuda.render(
            "[ENTER] Iniciar partida   |   [ESC] Salir", True, self.COLOR_CONTROLES
        )
        rect_ayuda = surf_ayuda.get_rect(center=(ANCHO // 2, ALTO - 70))
        pantalla.blit(surf_ayuda, rect_ayuda)
