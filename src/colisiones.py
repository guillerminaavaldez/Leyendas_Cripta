import pygame
from typing import Optional


def detectar_colision(jugador, enemigo, rect_meta: pygame.Rect) -> Optional[str]:
    """
    Evalúa colisión con el enemigo (Derrota) o con la Meta (Victoria).
    """
    # 1. Colisión con enemigo (Prioritaria)
    if jugador.rect.colliderect(enemigo.rect):
        if not jugador.colision_procesada:
            jugador.colision_procesada = True
            jugador.vivo = False
            return "derrota"
        return None

    # 2. Llegada a la meta
    if not jugador.ha_ganado:
        if jugador.rect.colliderect(rect_meta):
            jugador.ha_ganado = True
            return "victoria"

    return None
