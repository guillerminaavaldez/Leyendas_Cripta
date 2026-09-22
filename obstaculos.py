import pygame
import random


class Obstaculo:
    def __init__(self, x, y, ancho=60, alto=60, color=(100, 110, 130)):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.color = color

    def dibujar(self, pantalla):
        # Dibujo con borde decorativo
        pygame.draw.rect(pantalla, self.color, self.rect, border_radius=6)
        pygame.draw.rect(pantalla, (40, 45, 55), self.rect, width=2, border_radius=6)


def generar_obstaculos_nivel(nivel: int, ancho_pantalla: int, alto_pantalla: int, 
                             pos_jugador: tuple, pos_enemigo: tuple, rect_meta: pygame.Rect):
    """
    Genera una lista de obstáculos aumentando según el nivel y garantizando caminos transitables.
    """
    base_obstaculos = 4
    incremento_por_nivel = 3
    cantidad = base_obstaculos + (nivel - 1) * incremento_por_nivel

    obstaculos = []
    margen_seguridad = 110  # Radio libre alrededor de spawns y meta

    spawn_jugador_rect = pygame.Rect(pos_jugador[0] - 20, pos_jugador[1] - 20, margen_seguridad, margen_seguridad)
    spawn_enemigo_rect = pygame.Rect(pos_enemigo[0] - 20, pos_enemigo[1] - 20, margen_seguridad, margen_seguridad)
    meta_segura_rect = rect_meta.inflate(40, 40)

    # Variación de color según el nivel
    colores_por_nivel = {
        1: (90, 105, 120),   # Piedra clásica
        2: (70, 110, 85),    # Musgoso
        3: (130, 75, 75)     # Roca volcánica
    }
    color_obs = colores_por_nivel.get(nivel, (100, 100, 100))

    intentos = 0
    max_intentos = 250

    while len(obstaculos) < cantidad and intentos < max_intentos:
        intentos += 1
        ancho_obs = random.randint(50, 75)
        alto_obs = random.randint(50, 75)
        x = random.randint(80, ancho_pantalla - ancho_obs - 80)
        y = random.randint(80, alto_pantalla - alto_obs - 80)

        nuevo_rect = pygame.Rect(x, y, ancho_obs, alto_obs)

        # Evitar zonas críticas
        if nuevo_rect.colliderect(spawn_jugador_rect) or \
           nuevo_rect.colliderect(spawn_enemigo_rect) or \
           nuevo_rect.colliderect(meta_segura_rect):
            continue

        # Evitar superposición excesiva con otros obstáculos
        solapado = False
        for obs in obstaculos:
            if nuevo_rect.colliderect(obs.rect.inflate(20, 20)):
                solapado = True
                break

        if not solapado:
            obstaculos.append(Obstaculo(x, y, ancho_obs, alto_obs, color=color_obs))

    return obstaculos
