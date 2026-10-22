# MODULARIZADO: Módulo encargado de todo el renderizado gráfico, HUD y overlays de pantalla
import pygame
from config import ANCHO, ALTO, NIVEL_MAXIMO, RECOMPENSA_POR_NIVEL, COLORES_FONDO


class Renderizador:
    def __init__(self):
        # Fuentes tipográficas
        self.fuente_hud = pygame.font.Font(None, 24)
        self.fuente_titulo = pygame.font.Font(None, 64)
        self.fuente_sub = pygame.font.Font(None, 30)

    def dibujar_escenario(self, pantalla, nivel_actual: int, rect_meta: pygame.Rect, obstaculos: list):
        """
        MODULARIZADO: Dibuja el color de fondo temático, la zona de meta y los obstáculos.
        """
        color_fondo = COLORES_FONDO.get(nivel_actual, (20, 20, 30))
        pantalla.fill(color_fondo)

        # Zona Ganadora (Meta)
        pygame.draw.rect(pantalla, (255, 215, 0), rect_meta, border_radius=10)
        pygame.draw.rect(pantalla, (255, 255, 200), rect_meta.inflate(-10, -10), width=3, border_radius=8)
        surf_meta_txt = self.fuente_hud.render("META", True, (60, 40, 0))
        pantalla.blit(surf_meta_txt, surf_meta_txt.get_rect(center=rect_meta.center))

        # Obstáculos
        for obs in obstaculos:
            obs.dibujar(pantalla)

    def dibujar_actores(self, pantalla, jugador, enemigo):
        """
        MODULARIZADO: Dibuja los sprites del jugador, enemigo, auras y predicción de la Poción Y.
        """
        # Predicción de la siguiente posición del enemigo (Poción Y)
        if enemigo.mostrar_prediccion:
            px = int(enemigo.prediccion_pos[0])
            py = int(enemigo.prediccion_pos[1])
            pred_rect = pygame.Rect(px, py, enemigo.TAMANO_SPRITE, enemigo.TAMANO_SPRITE)

            # Flecha punteada desde el enemigo hasta la posición predicha
            origen_x = enemigo.rect.centerx
            origen_y = enemigo.rect.centery
            destino_x = pred_rect.centerx
            destino_y = pred_rect.centery
            dx = destino_x - origen_x
            dy = destino_y - origen_y
            longitud = max(1, (dx ** 2 + dy ** 2) ** 0.5)
            segmentos = max(2, int(longitud // 20))
            for i in range(segmentos):
                t0 = i / segmentos
                t1 = (i + 0.5) / segmentos
                sx0 = int(origen_x + dx * t0)
                sy0 = int(origen_y + dy * t0)
                sx1 = int(origen_x + dx * t1)
                sy1 = int(origen_y + dy * t1)
                pygame.draw.line(pantalla, (230, 160, 255), (sx0, sy0), (sx1, sy1), 2)

            # Marcador semitransparente en la posición predicha
            sombra = pygame.Surface((enemigo.TAMANO_SPRITE, enemigo.TAMANO_SPRITE), pygame.SRCALPHA)
            sombra.fill((190, 90, 255, 90))
            pantalla.blit(sombra, pred_rect)
            pygame.draw.rect(pantalla, (230, 160, 255), pred_rect, width=2, border_radius=6)

            # Etiqueta con horizonte de tiempo
            txt_pred = self.fuente_hud.render("Posición en ~1.5s", True, (240, 180, 255))
            pantalla.blit(txt_pred, (pred_rect.x, pred_rect.y - 20))

        # Enemigo (con tinte azul si está retrasado/congelado)
        pantalla.blit(enemigo.imagen, enemigo.rect)
        if getattr(enemigo, "tiempo_retraso", 0.0) > 0.0:
            congelado_surf = pygame.Surface((enemigo.rect.width, enemigo.rect.height), pygame.SRCALPHA)
            congelado_surf.fill((100, 200, 255, 120))
            pantalla.blit(congelado_surf, enemigo.rect)

        # Héroe
        pantalla.blit(jugador.imagen, jugador.rect)

    def dibujar_hud(self, pantalla, nivel_actual: int, jugador, mensaje_hud: str, tiempo_hud: float, color_hud: tuple):
        """
        MODULARIZADO: Dibuja la barra superior de información y los mensajes flotantes de feedback.
        """
        # Barra superior semi-transparente
        hud_bar = pygame.Surface((ANCHO, 44), pygame.SRCALPHA)
        hud_bar.fill((10, 15, 25, 210))
        pantalla.blit(hud_bar, (0, 0))

        # Textos informativos
        txt_nivel = self.fuente_hud.render(f"NIVEL: {nivel_actual}/{NIVEL_MAXIMO}", True, (240, 240, 240))
        txt_monedas = self.fuente_hud.render(f"Monedas: {jugador.monedas} 🪙", True, (255, 215, 0))
        txt_pociones = self.fuente_hud.render(
            f"POCIONES: [T] Retrasar: {jugador.pociones['retraso']} | [X] Saltar: {jugador.pociones['salto']} | [Y] Visión: {jugador.pociones['vision']}",
            True, (180, 220, 255)
        )
        txt_tienda_btn = self.fuente_hud.render("[M] Tienda", True, (255, 200, 100))

        pantalla.blit(txt_nivel, (15, 13))
        pantalla.blit(txt_monedas, (120, 13))
        pantalla.blit(txt_pociones, (245, 13))
        pantalla.blit(txt_tienda_btn, (ANCHO - 105, 13))

        # Mensaje flotante de feedback
        if tiempo_hud > 0:
            surf_aviso = self.fuente_sub.render(mensaje_hud, True, color_hud)
            rect_aviso = surf_aviso.get_rect(center=(ANCHO // 2, 68))
            bg_aviso = pygame.Surface((rect_aviso.width + 20, rect_aviso.height + 8), pygame.SRCALPHA)
            bg_aviso.fill((0, 0, 0, 190))
            pantalla.blit(bg_aviso, (rect_aviso.x - 10, rect_aviso.y - 4))
            pantalla.blit(surf_aviso, rect_aviso)

    def dibujar_overlays(self, pantalla, estado_juego: str, nivel_actual: int, jugador, tienda):
        """
        MODULARIZADO: Renderiza las pantallas emergentes según el estado actual del juego.
        """
        if estado_juego == "tienda":
            tienda.dibujar(pantalla, jugador)

        elif estado_juego == "victoria_nivel":
            overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            overlay.fill((10, 40, 20, 215))
            pantalla.blit(overlay, (0, 0))

            t1 = self.fuente_titulo.render(f"¡NIVEL {nivel_actual} COMPLETADO!", True, (120, 255, 150))
            t2 = self.fuente_sub.render(
                f"+{RECOMPENSA_POR_NIVEL} Monedas obtenidas (Total: {jugador.monedas} 🪙)",
                True, (255, 230, 80)
            )
            t3 = self.fuente_hud.render(
                "Presiona [ESPACIO] para siguiente nivel  |  [M] para abrir la Tienda",
                True, (220, 220, 220)
            )

            pantalla.blit(t1, t1.get_rect(center=(ANCHO // 2, ALTO // 2 - 50)))
            pantalla.blit(t2, t2.get_rect(center=(ANCHO // 2, ALTO // 2 + 10)))
            pantalla.blit(t3, t3.get_rect(center=(ANCHO // 2, ALTO // 2 + 60)))

        elif estado_juego == "derrota":
            overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            overlay.fill((40, 10, 10, 220))
            pantalla.blit(overlay, (0, 0))

            t1 = self.fuente_titulo.render("HAS SIDO INTERCEPTADO", True, (255, 80, 80))
            t2 = self.fuente_sub.render("Presiona [R] para reiniciar el nivel o [ESC] para salir", True, (220, 220, 220))

            pantalla.blit(t1, t1.get_rect(center=(ANCHO // 2, ALTO // 2 - 30)))
            pantalla.blit(t2, t2.get_rect(center=(ANCHO // 2, ALTO // 2 + 30)))

        elif estado_juego == "juego_completado":
            overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            overlay.fill((20, 15, 45, 230))
            pantalla.blit(overlay, (0, 0))

            t1 = self.fuente_titulo.render("¡VICTORIA TOTAL!", True, (255, 215, 0))
            t2 = self.fuente_sub.render(
                f"Superaste todas las criptas con {jugador.monedas} monedas.",
                True, (180, 240, 255)
            )
            t3 = self.fuente_hud.render("Presiona [R] para jugar de nuevo o [ESC] para salir", True, (200, 200, 200))

            pantalla.blit(t1, t1.get_rect(center=(ANCHO // 2, ALTO // 2 - 50)))
            pantalla.blit(t2, t2.get_rect(center=(ANCHO // 2, ALTO // 2 + 10)))
            pantalla.blit(t3, t3.get_rect(center=(ANCHO // 2, ALTO // 2 + 60)))
