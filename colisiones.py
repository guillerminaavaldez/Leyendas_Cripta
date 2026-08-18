import pygame
from typing import Optional


def detectar_colision(jugador, enemigo, screen_rect: Optional[pygame.Rect] = None) -> Optional[str]:
    """
    Detecta colisión entre `jugador` y `enemigo` y aplica la lógica de victoria/derrota.

    Devuelve:
      - 'derrota' si el jugador colisiona con el enemigo (procesado una sola vez),
      - 'victoria' si el jugador alcanza la esquina inferior derecha sin haber sido tocado,
      - None si no ocurre ningún evento de fin de juego.

    Parámetros:
      - jugador, enemigo: instancias que contienen `rect` (pygame.Rect).
      - screen_rect (opcional): pygame.Rect del área de juego; si es None se intentará
        obtenerlo con la superficie de display.

    Notas:
      - La función añade/usa los atributos dinámicos `colision_procesada` y `ha_ganado`
        en la instancia `jugador` para evitar procesar el mismo evento varias veces.
      - No modifica las clases `Jugador` ni `Enemigo`, sólo establece atributos en
        las instancias cuando es necesario.
    """

    # Inicializar flags en la instancia si aún no existen
    if not hasattr(jugador, "colision_procesada"):
        jugador.colision_procesada = False
    if not hasattr(jugador, "ha_ganado"):
        jugador.ha_ganado = False

    # 1) Comprobar colisión (prioritaria)
    if jugador.rect.colliderect(enemigo.rect):
        # Solo procesar la primera vez que se detecta la colisión
        if not jugador.colision_procesada:
            jugador.colision_procesada = True
            # Marcar estado de vida en el jugador (atributo dinámico mínimo)
            jugador.vivo = False
            return "derrota"
        # Si ya se procesó, no repetir la acción
        return None

    # 2) Si no hay colisión, comprobar victoria (si aún no ganó)
    if not jugador.ha_ganado:
        # Obtener rectángulo de pantalla si no fue provisto
        if screen_rect is None:
            surface = pygame.display.get_surface()
            if surface:
                screen_rect = surface.get_rect()
        # Si tenemos rectángulo de pantalla, validar esquina inferior derecha
        if screen_rect:
            reached_right = jugador.rect.right >= screen_rect.right
            reached_bottom = jugador.rect.bottom >= screen_rect.bottom
            if reached_right and reached_bottom:
                jugador.ha_ganado = True
                # Asegurar estado coherente
                jugador.vivo = True
                return "victoria"

    # No ocurrió nada relevante
    return None
