import math
import pygame
from config import DURACION_RETRASO_SEG, DURACION_PREDICCION_SEG

# Definición de información, costos y teclas de activación de pociones
DATOS_POCIONES = {
    "retraso": {
        "nombre": "Poción de Congelación",
        "descripcion": "Retrasa al enemigo durante 1 segundo.",
        "costo": 25,
        "tecla_uso": "T",  # MODIFICADO: Tecla asignada claramente
        "color": (80, 180, 255)
    },
    "salto": {
        "nombre": "Poción de Salto Táctico",
        "descripcion": "Salta al enemigo si está a 1 casillero de distancia.",
        "costo": 35,
        "tecla_uso": "X",  # MODIFICADO: Tecla asignada claramente
        "color": (255, 180, 50)
    },
    "vision": {
        "nombre": "Poción de Adivinación",
        "descripcion": "Muestra la siguiente posición del enemigo.",
        "costo": 15,
        "tecla_uso": "Y",  # MODIFICADO: Tecla asignada claramente
        "color": (190, 90, 255)
    }
}


def usar_pocion_retraso(jugador, enemigo) -> tuple[bool, str]:
    """
    MODIFICADO: Aplica retraso en segundos al enemigo basado en DURACION_RETRASO_SEG.
    Solo se consume si el jugador tiene al menos 1 unidad.
    """
    if jugador.pociones.get("retraso", 0) <= 0:
        return False, "¡No tienes Pociones de Retraso [T]! Cómpralas en la Tienda [M]"

    jugador.pociones["retraso"] -= 1
    # Duración en segundos acumulable
    enemigo.tiempo_retraso += DURACION_RETRASO_SEG
    return True, f"¡[T] Enemigo retrasado durante {DURACION_RETRASO_SEG}s!"


def usar_pocion_salto(jugador, enemigo, ancho_pantalla, alto_pantalla, obstaculos) -> tuple[bool, str]:
    """
    MODIFICADO: Permite saltar al enemigo únicamente si está a 1 casillero de distancia (~130 px).
    NO consume la poción si el enemigo no se encuentra en el rango válido.
    """
    if jugador.pociones.get("salto", 0) <= 0:
        return False, "¡No tienes Pociones de Salto [X]! Cómpralas en la Tienda [M]"

    # Comprobación de distancia (rango de 1 casillero)
    dx = enemigo.x - jugador.x
    dy = enemigo.y - jugador.y
    distancia = math.hypot(dx, dy)
    distancia_un_casillero = 130.0

    # Si NO está a 1 casillero de distancia, no se consume la poción
    if distancia > distancia_un_casillero or distancia == 0:
        return False, "¡El enemigo no está a 1 casillero! (Poción [X] NO consumida)"

    # Proyección del salto al otro lado del enemigo
    vector_x = (dx / distancia)
    vector_y = (dy / distancia)

    nuevo_x = jugador.x + vector_x * 160
    nuevo_y = jugador.y + vector_y * 160

    nuevo_x = max(0.0, min(nuevo_x, float(ancho_pantalla - jugador.rect.width)))
    nuevo_y = max(0.0, min(nuevo_y, float(alto_pantalla - jugador.rect.height)))

    # Evitar quedar atrapado dentro de un obstáculo al aterrizar
    temp_rect = pygame.Rect(int(nuevo_x), int(nuevo_y), jugador.rect.width, jugador.rect.height)
    for obs in obstaculos:
        if temp_rect.colliderect(obs.rect):
            nuevo_x = jugador.x - vector_y * 100
            nuevo_y = jugador.y + vector_x * 100
            break

    # Aplicar salto y descontar exactamente 1 unidad
    jugador.x = nuevo_x
    jugador.y = nuevo_y
    jugador.actualizar_rect()
    jugador.pociones["salto"] -= 1

    return True, "¡[X] Salto táctico exitoso sobre el enemigo!"


def usar_pocion_vision(jugador, enemigo) -> tuple[bool, str]:
    """
    MODIFICADO: Calcula y activa la visualización de la próxima posición del enemigo.
    Solo se consume si el jugador tiene unidades disponibles.
    """
    if jugador.pociones.get("vision", 0) <= 0:
        return False, "¡No tienes Pociones de Visión [Y]! Cómpralas en la Tienda [M]"

    jugador.pociones["vision"] -= 1
    enemigo.mostrar_prediccion = True
    enemigo.tiempo_prediccion = DURACION_PREDICCION_SEG  # Visible durante 3.0 segundos

    siguiente_x, siguiente_y = enemigo.calcular_siguiente_posicion(jugador.x, jugador.y)
    enemigo.prediccion_pos = (siguiente_x, siguiente_y)

    return True, f"¡[Y] Siguiente posición del enemigo revelada durante {DURACION_PREDICCION_SEG}s!"
