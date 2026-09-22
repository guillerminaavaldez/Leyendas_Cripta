# MODULARIZADO: Módulo para la captura y procesamiento de eventos de entrada y teclado
import pygame
from pociones import usar_pocion_retraso, usar_pocion_salto, usar_pocion_vision
from config import ANCHO, ALTO


def procesar_eventos(estado_juego: str, estado_previo: str, jugador, enemigo,
                     tienda, gestor_niveles, obstaculos: list, avisar_hud_fn) -> tuple[bool, str, str, list]:
    """
    MODULARIZADO: Procesa todos los eventos de pygame de la iteración actual.
    Garantiza un único pygame.event.get() por frame y maneja la navegación y pociones
    exclusivamente mediante pygame.KEYDOWN.

    Retorna: (ejecutando, nuevo_estado_juego, nuevo_estado_previo, obstaculos_actuales)
    """
    ejecutando = True

    for evento in pygame.event.get():
        # Cierre de la ventana
        if evento.type == pygame.QUIT:
            return False, estado_juego, estado_previo, obstaculos

        # Eventos discretos de pulsación de tecla
        if evento.type == pygame.KEYDOWN:

            # --- NAVEGACIÓN HACIA LA TIENDA ([M]) ---
            if evento.key == pygame.K_m:
                if estado_juego == "tienda":
                    # Volver al estado previo al abrir la tienda
                    estado_juego = estado_previo
                else:
                    estado_previo = estado_juego
                    estado_juego = "tienda"

            # --- ESTADO: TIENDA ---
            elif estado_juego == "tienda":
                if evento.key == pygame.K_ESCAPE:
                    estado_juego = estado_previo
                elif evento.key == pygame.K_1:
                    tienda.comprar("retraso", jugador)
                elif evento.key == pygame.K_2:
                    tienda.comprar("salto", jugador)
                elif evento.key == pygame.K_3:
                    tienda.comprar("vision", jugador)

            # --- ESTADO: JUGANDO (USO DE POCIONES) ---
            elif estado_juego == "jugando":
                if evento.key == pygame.K_t:
                    ok, msg = usar_pocion_retraso(jugador, enemigo)
                    avisar_hud_fn(msg, (80, 200, 255) if ok else (255, 100, 100))

                elif evento.key == pygame.K_x:
                    ok, msg = usar_pocion_salto(jugador, enemigo, ANCHO, ALTO, obstaculos)
                    avisar_hud_fn(msg, (255, 200, 80) if ok else (255, 100, 100))

                elif evento.key == pygame.K_y:
                    ok, msg = usar_pocion_vision(jugador, enemigo)
                    avisar_hud_fn(msg, (200, 100, 255) if ok else (255, 100, 100))

            # --- ESTADO: VICTORIA DE NIVEL ---
            elif estado_juego == "victoria_nivel":
                if evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                    nuevo_nivel, nuevos_obstaculos, nuevo_estado = gestor_niveles.avanzar_nivel(jugador, enemigo)
                    estado_juego = nuevo_estado
                    estado_previo = nuevo_estado
                    if nuevo_estado == "jugando":
                        obstaculos = nuevos_obstaculos
                        avisar_hud_fn(f"¡Nivel {nuevo_nivel} Iniciado!", (100, 255, 150))

            # --- ESTADOS: DERROTA O JUEGO COMPLETADO ---
            elif estado_juego in ("derrota", "juego_completado"):
                if evento.key == pygame.K_r:
                    if estado_juego == "juego_completado":
                        obstaculos = gestor_niveles.reiniciar_partida(jugador, enemigo)
                    else:
                        obstaculos = gestor_niveles.iniciar_nivel(gestor_niveles.nivel_actual, jugador, enemigo)
                    estado_juego = "jugando"
                    estado_previo = "jugando"
                    avisar_hud_fn(f"¡Nivel {gestor_niveles.nivel_actual} Reiniciado!", (100, 255, 150))

                elif evento.key == pygame.K_ESCAPE:
                    ejecutando = False

    return ejecutando, estado_juego, estado_previo, obstaculos
