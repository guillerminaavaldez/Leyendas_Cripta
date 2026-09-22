import os
import pygame
from personajes import Jugador, Enemigo
from obstaculos import generar_obstaculos_nivel
from colisiones import detectar_colision
from tienda import TiendaPociones
from pociones import usar_pocion_retraso, usar_pocion_salto, usar_pocion_vision


def main():
    pygame.init()

    ANCHO = 850
    ALTO = 650
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Leyendas de la Cripta - Edición Pociones y Niveles ")

    reloj = pygame.time.Clock()

    # Carga de recursos / assets
    ruta_assets = os.path.join(os.path.dirname(__file__), "assets")
    ruta_heroe = os.path.join(ruta_assets, "heroe_pygame.png")
    ruta_enemigo = os.path.join(ruta_assets, "enemigo_pygame.png")

    # Inicialización de actores
    jugador = Jugador(x=40, y=40, velocidad=4.0, ruta_imagen=ruta_heroe)
    enemigo = Enemigo(x=ANCHO - 120, y=40, velocidad=2.2, ruta_imagen=ruta_enemigo)

    # Posición Ganadora (Meta) en la esquina inferior derecha
    TAM_META = 80
    rect_meta = pygame.Rect(ANCHO - TAM_META - 20, ALTO - TAM_META - 20, TAM_META, TAM_META)

    # Sistema de niveles
    NIVEL_MAXIMO = 3
    nivel_actual = 1
    RECOMPENSA_POR_NIVEL = 50

    # Generar obstáculos iniciales
    obstaculos = generar_obstaculos_nivel(nivel_actual, ANCHO, ALTO, (jugador.x, jugador.y), (enemigo.x, enemigo.y), rect_meta)

    # Tienda y Estados
    tienda = TiendaPociones(ANCHO, ALTO)
    # MODIFICADO: Registro de estado previo para volver fluidamente desde la tienda
    estado_juego = "jugando"  # Estados: "jugando", "tienda", "victoria_nivel", "derrota", "juego_completado"
    estado_previo = "jugando"

    # Fuentes
    fuente_hud = pygame.font.Font(None, 24)
    fuente_titulo = pygame.font.Font(None, 64)
    fuente_sub = pygame.font.Font(None, 30)

    # Feedback temporal en HUD
    mensaje_hud = ""
    frames_mensaje_hud = 0
    color_mensaje_hud = (255, 255, 255)

    def mostrar_aviso_hud(texto, color=(255, 255, 200)):
        nonlocal mensaje_hud, frames_mensaje_hud, color_mensaje_hud
        mensaje_hud = texto
        color_mensaje_hud = color
        frames_mensaje_hud = 120

    def iniciar_nivel(num_nivel):
        nonlocal obstaculos, estado_juego, estado_previo
        jugador.x, jugador.y = 40.0, 40.0
        jugador.actualizar_rect()
        jugador.colision_procesada = False
        jugador.ha_ganado = False
        jugador.vivo = True

        enemigo.x, enemigo.y = float(ANCHO - 120), 40.0
        enemigo.actualizar_rect()
        enemigo.movimientos_retraso = 0
        enemigo.mostrar_prediccion = False

        obstaculos = generar_obstaculos_nivel(num_nivel, ANCHO, ALTO, (jugador.x, jugador.y), (enemigo.x, enemigo.y), rect_meta)
        estado_juego = "jugando"
        estado_previo = "jugando"
        mostrar_aviso_hud(f"¡Nivel {num_nivel} Iniciado!", (100, 255, 150))

    # Paletas de fondo por nivel para cambio de pantalla
    colores_fondo = {
        1: (20, 24, 35),   # Azul Cripta
        2: (22, 34, 28),   # Verde Profundo
        3: (38, 22, 22)    # Carmesí Oscuro
    }

    ejecutando = True

    while ejecutando:
        # ==================== 1. MANEJO DE EVENTOS (ÚNICO BUCLE POR FRAME) ====================
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            # MODIFICADO: Todos los cambios de pantalla y activaciones de pociones se procesan
            # estrictamente con pygame.KEYDOWN para garantizar que se ejecuten una única vez
            if evento.type == pygame.KEYDOWN:

                # --- NAVEGACIÓN HACIA LA TIENDA ---
                # MODIFICADO: La Tienda se abre con [M] (Mercado/Tienda) liberando la tecla [T] para la poción
                if evento.key == pygame.K_m:
                    if estado_juego == "tienda":
                        # Volver al estado en el que nos encontrábamos
                        estado_juego = estado_previo
                    else:
                        estado_previo = estado_juego
                        estado_juego = "tienda"

                # --- ESTADO: TIENDA ---
                elif estado_juego == "tienda":
                    # MODIFICADO: Salir de la tienda y volver al juego con [ESC]
                    if evento.key == pygame.K_ESCAPE:
                        estado_juego = estado_previo
                    # Compras en la tienda
                    elif evento.key == pygame.K_1:
                        tienda.comprar("retraso", jugador)
                    elif evento.key == pygame.K_2:
                        tienda.comprar("salto", jugador)
                    elif evento.key == pygame.K_3:
                        tienda.comprar("vision", jugador)

                # --- ESTADO: JUGANDO (ACTIVACIÓN DE POCIONES) ---
                elif estado_juego == "jugando":
                    # MODIFICADO: Tecla [T] asignada a la Poción de Retraso x2
                    if evento.key == pygame.K_t:
                        ok, msg = usar_pocion_retraso(jugador, enemigo)
                        mostrar_aviso_hud(msg, (80, 200, 255) if ok else (255, 100, 100))

                    # MODIFICADO: Tecla [X] asignada a la Poción de Salto sobre enemigo
                    elif evento.key == pygame.K_x:
                        ok, msg = usar_pocion_salto(jugador, enemigo, ANCHO, ALTO, obstaculos)
                        mostrar_aviso_hud(msg, (255, 200, 80) if ok else (255, 100, 100))

                    # MODIFICADO: Tecla [Y] asignada a la Poción de Visión de Movimiento
                    elif evento.key == pygame.K_y:
                        ok, msg = usar_pocion_vision(jugador, enemigo)
                        mostrar_aviso_hud(msg, (200, 100, 255) if ok else (255, 100, 100))

                # --- ESTADO: VICTORIA DE NIVEL ---
                elif estado_juego == "victoria_nivel":
                    # MODIFICADO: Avanzar de nivel con [ESPACIO] o [ENTER]
                    if evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if nivel_actual < NIVEL_MAXIMO:
                            nivel_actual += 1
                            iniciar_nivel(nivel_actual)
                        else:
                            estado_juego = "juego_completado"

                # --- ESTADOS: DERROTA O JUEGO COMPLETADO ---
                elif estado_juego in ("derrota", "juego_completado"):
                    # MODIFICADO: Reiniciar con [R] o Salir con [ESC]
                    if evento.key == pygame.K_r:
                        if estado_juego == "juego_completado":
                            nivel_actual = 1
                            jugador.monedas = 0
                            jugador.pociones = {"retraso": 0, "salto": 0, "vision": 0}
                        iniciar_nivel(nivel_actual)
                    elif evento.key == pygame.K_ESCAPE:
                        ejecutando = False

        # ==================== 2. ACTUALIZACIÓN LÓGICA ====================
        if estado_juego == "jugando":
            # El movimiento continuo del héroe utiliza get_pressed() (apropiado para física continua)
            teclas = pygame.key.get_pressed()
            jugador.mover_con_obstaculos(teclas, ANCHO, ALTO, obstaculos)

            # Persecución del enemigo
            enemigo.perseguir_con_retraso(jugador.x, jugador.y, ANCHO, ALTO)

            # Actualizar predicción si está activa
            if enemigo.mostrar_prediccion:
                enemigo.frames_prediccion -= 1
                if enemigo.frames_prediccion <= 0:
                    enemigo.mostrar_prediccion = False
                else:
                    enemigo.prediccion_pos = enemigo.calcular_siguiente_posicion(jugador.x, jugador.y)

            # Detección de colisiones y metas
            resultado = detectar_colision(jugador, enemigo, rect_meta)
            if resultado == "derrota":
                estado_juego = "derrota"
            elif resultado == "victoria":
                jugador.monedas += RECOMPENSA_POR_NIVEL
                if nivel_actual >= NIVEL_MAXIMO:
                    estado_juego = "juego_completado"
                else:
                    estado_juego = "victoria_nivel"

        # ==================== 3. RENDERIZADO ====================
        # Fondo según nivel
        color_fondo = colores_fondo.get(nivel_actual, (20, 20, 30))
        pantalla.fill(color_fondo)

        # Dibujar Zona Ganadora (Meta)
        pygame.draw.rect(pantalla, (255, 215, 0), rect_meta, border_radius=10)
        pygame.draw.rect(pantalla, (255, 255, 200), rect_meta.inflate(-10, -10), width=3, border_radius=8)
        surf_meta_txt = fuente_hud.render("META", True, (60, 40, 0))
        pantalla.blit(surf_meta_txt, surf_meta_txt.get_rect(center=rect_meta.center))

        # Dibujar Obstáculos
        for obs in obstaculos:
            obs.dibujar(pantalla)

        # Dibujar predicción de posición del enemigo (Poción Y)
        if enemigo.mostrar_prediccion:
            pred_rect = pygame.Rect(int(enemigo.prediccion_pos[0]), int(enemigo.prediccion_pos[1]), enemigo.TAMANO_SPRITE, enemigo.TAMANO_SPRITE)
            sombra = pygame.Surface((enemigo.TAMANO_SPRITE, enemigo.TAMANO_SPRITE), pygame.SRCALPHA)
            sombra.fill((190, 90, 255, 110))
            pantalla.blit(sombra, pred_rect)
            pygame.draw.rect(pantalla, (230, 160, 255), pred_rect, width=2, border_radius=6)
            txt_pred = fuente_hud.render("Siguiente Posición", True, (240, 180, 255))
            pantalla.blit(txt_pred, (pred_rect.x - 10, pred_rect.y - 18))

        # Dibujar Enemigo con efecto visual si está congelado/retrasado
        pantalla.blit(enemigo.imagen, enemigo.rect)
        if enemigo.movimientos_retraso > 0:
            congelado_surf = pygame.Surface((enemigo.rect.width, enemigo.rect.height), pygame.SRCALPHA)
            congelado_surf.fill((100, 200, 255, 120))  # Tinte azul
            pantalla.blit(congelado_surf, enemigo.rect)

        # Dibujar Héroe
        pantalla.blit(jugador.imagen, jugador.rect)

        # ----------------- HUD SUPERIOR (MODIFICADO) -----------------
        # Barra superior con fondo legible
        hud_bar = pygame.Surface((ANCHO, 44), pygame.SRCALPHA)
        hud_bar.fill((10, 15, 25, 210))
        pantalla.blit(hud_bar, (0, 0))

        # MODIFICADO: Textos claros indicando teclas exactas [T], [X], [Y] y [M] Tienda
        txt_nivel = fuente_hud.render(f"NIVEL: {nivel_actual}/{NIVEL_MAXIMO}", True, (240, 240, 240))
        txt_monedas = fuente_hud.render(f"Monedas: {jugador.monedas} 🪙", True, (255, 215, 0))
        txt_pociones = fuente_hud.render(
            f"POCIONES: [T] Retrasar: {jugador.pociones['retraso']} | [X] Saltar: {jugador.pociones['salto']} | [Y] Visión: {jugador.pociones['vision']}",
            True, (180, 220, 255)
        )
        txt_tienda_btn = fuente_hud.render("[M] Tienda", True, (255, 200, 100))

        pantalla.blit(txt_nivel, (15, 13))
        pantalla.blit(txt_monedas, (120, 13))
        pantalla.blit(txt_pociones, (245, 13))
        pantalla.blit(txt_tienda_btn, (ANCHO - 105, 13))

        # Mensajes flotantes de feedback en HUD
        if frames_mensaje_hud > 0:
            surf_aviso = fuente_sub.render(mensaje_hud, True, color_mensaje_hud)
            rect_aviso = surf_aviso.get_rect(center=(ANCHO // 2, 68))
            bg_aviso = pygame.Surface((rect_aviso.width + 20, rect_aviso.height + 8), pygame.SRCALPHA)
            bg_aviso.fill((0, 0, 0, 190))
            pantalla.blit(bg_aviso, (rect_aviso.x - 10, rect_aviso.y - 4))
            pantalla.blit(surf_aviso, rect_aviso)
            frames_mensaje_hud -= 1


        # ==================== 4. OVERLAYS DE ESTADOS ====================
        if estado_juego == "tienda":
            tienda.dibujar(pantalla, jugador)

        elif estado_juego == "victoria_nivel":
            overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            overlay.fill((10, 40, 20, 215))
            pantalla.blit(overlay, (0, 0))

            t1 = fuente_titulo.render(f"¡NIVEL {nivel_actual} COMPLETADO!", True, (120, 255, 150))
            t2 = fuente_sub.render(f"+{RECOMPENSA_POR_NIVEL} Monedas obtenidas (Total: {jugador.monedas} 🪙)", True, (255, 230, 80))
            # MODIFICADO: Instrucciones claras con teclas exactas
            t3 = fuente_hud.render("Presiona [ESPACIO] para siguiente nivel  |  [M] para abrir la Tienda", True, (220, 220, 220))

            pantalla.blit(t1, t1.get_rect(center=(ANCHO // 2, ALTO // 2 - 50)))
            pantalla.blit(t2, t2.get_rect(center=(ANCHO // 2, ALTO // 2 + 10)))
            pantalla.blit(t3, t3.get_rect(center=(ANCHO // 2, ALTO // 2 + 60)))

        elif estado_juego == "derrota":
            overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            overlay.fill((40, 10, 10, 220))
            pantalla.blit(overlay, (0, 0))

            t1 = fuente_titulo.render("HAS SIDO INTERCEPTADO", True, (255, 80, 80))
            t2 = fuente_sub.render("Presiona [R] para reiniciar el nivel o [ESC] para salir", True, (220, 220, 220))

            pantalla.blit(t1, t1.get_rect(center=(ANCHO // 2, ALTO // 2 - 30)))
            pantalla.blit(t2, t2.get_rect(center=(ANCHO // 2, ALTO // 2 + 30)))

        elif estado_juego == "juego_completado":
            overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            overlay.fill((20, 15, 45, 230))
            pantalla.blit(overlay, (0, 0))

            t1 = fuente_titulo.render("¡VICTORIA TOTAL!", True, (255, 215, 0))
            t2 = fuente_sub.render(f"Superaste todas las criptas con {jugador.monedas} monedas.", True, (180, 240, 255))
            t3 = fuente_hud.render("Presiona [R] para jugar de nuevo o [ESC] para salir", True, (200, 200, 200))

            pantalla.blit(t1, t1.get_rect(center=(ANCHO // 2, ALTO // 2 - 50)))
            pantalla.blit(t2, t2.get_rect(center=(ANCHO // 2, ALTO // 2 + 10)))
            pantalla.blit(t3, t3.get_rect(center=(ANCHO // 2, ALTO // 2 + 60)))

        pygame.display.flip()
        reloj.tick(60)

    pygame.quit()



if __name__ == "__main__":
    main()
