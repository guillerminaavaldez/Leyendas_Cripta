import os
import pygame
from personajes import Jugador, Enemigo
from colisiones import detectar_colision
import persistencia


def main():
    pygame.init()

    ancho = 800
    alto = 600
    pantalla = pygame.display.set_mode((ancho, alto))
    pygame.display.set_caption("Proyecto Leyendas Cripta")

    ruta_assets = os.path.join(os.path.dirname(__file__), "assets")
    ruta_heroe = os.path.join(ruta_assets, "heroe_pygame.png")
    ruta_enemigo = os.path.join(ruta_assets, "enemigo_pygame.png")

    jugador = Jugador(x=0, y=0, velocidad=5, ruta_imagen=ruta_heroe)
    enemigo = Enemigo(x=544, y=0, velocidad=3, ruta_imagen=ruta_enemigo)

    posicion_inicial_jugador = (jugador.x, jugador.y)
    posicion_inicial_enemigo = (enemigo.x, enemigo.y)

    partida_guardada = persistencia.cargar_partida()
    if partida_guardada is not None:
        jugador.x, jugador.y = partida_guardada
        jugador.rect.x, jugador.rect.y = int(jugador.x), int(jugador.y)

    reloj = pygame.time.Clock()
    ejecutando = True

    estado_juego = "jugando"

    fuente_mensaje = pygame.font.Font(None, 72)
    fuente_instruccion = pygame.font.Font(None, 28)

    frames_aviso_guardado = 0

    def reiniciar_partida():
        nonlocal estado_juego

        jugador.x, jugador.y = posicion_inicial_jugador
        jugador.rect.x, jugador.rect.y = int(jugador.x), int(jugador.y)

        enemigo.x, enemigo.y = posicion_inicial_enemigo
        enemigo.rect.topleft = (int(posicion_inicial_enemigo[0]), int(posicion_inicial_enemigo[1]))

        if hasattr(jugador, "colision_procesada"):
            jugador.colision_procesada = False
        if hasattr(jugador, "ha_ganado"):
            jugador.ha_ganado = False
        jugador.vivo = True

        estado_juego = "jugando"

    while ejecutando:

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            if evento.type == pygame.KEYDOWN:
                if estado_juego == "jugando" and evento.key == pygame.K_g:
                    persistencia.guardar_partida(jugador.x, jugador.y)
                    frames_aviso_guardado = 90  # ~1.5 segundos a 60 FPS

                if evento.key == pygame.K_r:
                    reiniciar_partida()

                if estado_juego in ("victoria", "derrota") and evento.key == pygame.K_ESCAPE:
                    ejecutando = False

        # ----------------- UPDATE -----------------
        if estado_juego == "jugando":
            teclas = pygame.key.get_pressed()

            prev_x, prev_y = jugador.x, jugador.y
            jugador.mover(teclas, ancho, alto)

            dx = jugador.x - prev_x
            dy = jugador.y - prev_y
            pasos = int(max(abs(dx) / float(jugador.velocidad) if jugador.velocidad else 0,
                            abs(dy) / float(jugador.velocidad) if jugador.velocidad else 0))

            if pasos > 0:
                enemigo.añadir_pasos(pasos, delay_frames=0, threshold=3)

            colision_en_persecucion = enemigo.procesar_pasos(ancho, alto, jugador=jugador, max_steps_per_frame=1)
            if colision_en_persecucion:
                estado_juego = "derrota"
                if hasattr(jugador, "colision_procesada"):
                    jugador.colision_procesada = True
                else:
                    jugador.colision_procesada = True
                jugador.vivo = False

            resultado = detectar_colision(jugador, enemigo)
            if resultado == "derrota":
                estado_juego = "derrota"
            elif resultado == "victoria":
                estado_juego = "victoria"

        pantalla.fill((20, 20, 30))
        pantalla.blit(jugador.imagen, jugador.rect)
        pantalla.blit(enemigo.imagen, enemigo.rect)

        if frames_aviso_guardado > 0:
            surf_aviso = fuente_instruccion.render("Partida guardada", True, (120, 255, 120))
            pantalla.blit(surf_aviso, (10, 10))
            frames_aviso_guardado -= 1

        if estado_juego in ("victoria", "derrota"):
            overlay = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))  # negro con alfa
            pantalla.blit(overlay, (0, 0))

            mensaje_texto = "¡GANASTE!" if estado_juego == "victoria" else "PERDISTE"
            surf_mensaje = fuente_mensaje.render(mensaje_texto, True, (255, 255, 255))
            rect_mensaje = surf_mensaje.get_rect(center=(ancho // 2, alto // 2 - 30))
            pantalla.blit(surf_mensaje, rect_mensaje)

            instr = "Presiona R para reiniciar, ESC para salir"
            surf_instr = fuente_instruccion.render(instr, True, (200, 200, 200))
            rect_instr = surf_instr.get_rect(center=(ancho // 2, alto // 2 + 30))
            pantalla.blit(surf_instr, rect_instr)

        pygame.display.flip()
        reloj.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()