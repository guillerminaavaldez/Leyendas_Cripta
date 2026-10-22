import pygame
try:
    from src.pociones import DATOS_POCIONES
except ModuleNotFoundError:
    from pociones import DATOS_POCIONES


from config import DURACION_AVISO_SEG


class TiendaPociones:
    def __init__(self, ancho_pantalla, alto_pantalla):
        self.ancho = ancho_pantalla
        self.alto = alto_pantalla
        self.fuente_titulo = pygame.font.Font(None, 40)
        self.fuente_item = pygame.font.Font(None, 24)
        self.fuente_desc = pygame.font.Font(None, 20)
        self.fuente_pie = pygame.font.Font(None, 22)
        self.mensaje_feedback = ""
        self.color_feedback = (255, 255, 255)
        self.tiempo_feedback: float = 0.0

    def actualizar(self, dt: float) -> None:
        """
        Avanza el temporizador de feedback de la tienda.
        Garantiza que dibujar() permanezca como una función pura de renderizado.
        """
        if self.tiempo_feedback > 0.0:
            self.tiempo_feedback -= dt
            if self.tiempo_feedback < 0.0:
                self.tiempo_feedback = 0.0

    def comprar(self, tipo_pocion: str, jugador) -> bool:
        """
        Valida y efectúa la compra si el jugador posee suficientes monedas.
        """
        info = DATOS_POCIONES.get(tipo_pocion)
        if not info:
            return False

        costo = info["costo"]
        if jugador.monedas >= costo:
            jugador.monedas -= costo
            jugador.pociones[tipo_pocion] += 1
            self.mensaje_feedback = f"¡Compraste {info['nombre']}! (Se usa en juego con [{info['tecla_uso']}])"
            self.color_feedback = (100, 255, 100)
            self.tiempo_feedback = DURACION_AVISO_SEG
            return True
        else:
            self.mensaje_feedback = f"¡Monedas insuficientes! Requiere {costo} 🪙."
            self.color_feedback = (255, 100, 100)
            self.tiempo_feedback = DURACION_AVISO_SEG
            return False

    def dibujar(self, pantalla, jugador):
        """
        MODIFICADO: Renderiza la tienda indicando claramente las teclas de compra [1, 2, 3]
        y las teclas de activación en el juego [T, X, Y], junto con la tecla de retorno [M] / [ESC].
        """
        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 230))
        pantalla.blit(overlay, (0, 0))

        # Panel central
        panel_rect = pygame.Rect(80, 40, self.ancho - 160, self.alto - 80)
        pygame.draw.rect(pantalla, (25, 30, 45), panel_rect, border_radius=12)
        pygame.draw.rect(pantalla, (70, 90, 130), panel_rect, width=3, border_radius=12)

        # Encabezado
        surf_titulo = self.fuente_titulo.render("--- TIENDA MÍSTICA DE POCIONES ---", True, (240, 210, 100))
        pantalla.blit(surf_titulo, surf_titulo.get_rect(center=(self.ancho // 2, 80)))

        # Monedas disponibles
        surf_monedas = self.fuente_item.render(f"Monedas Disponibles: {jugador.monedas} 🪙", True, (255, 230, 80))
        pantalla.blit(surf_monedas, (110, 120))

        # Lista de pociones para comprar
        y_item = 160
        teclas_compra = {"retraso": "1", "salto": "2", "vision": "3"}

        for clave, info in DATOS_POCIONES.items():
            t_compra = teclas_compra[clave]
            t_uso = info["tecla_uso"]
            cant_actual = jugador.pociones.get(clave, 0)

            # Tarjeta de producto
            card_rect = pygame.Rect(110, y_item, self.ancho - 220, 75)
            puede_comprar = jugador.monedas >= info["costo"]
            color_borde = (100, 200, 100) if puede_comprar else (90, 90, 100)

            pygame.draw.rect(pantalla, (35, 42, 60), card_rect, border_radius=8)
            pygame.draw.rect(pantalla, color_borde, card_rect, width=2, border_radius=8)

            # MODIFICADO: Textos claros con tecla de compra y tecla de uso
            txt_linea1 = self.fuente_item.render(
                f"[{t_compra}] Comprar {info['nombre']} - Costo: {info['costo']} 🪙  |  Tienes: {cant_actual} en inventario",
                True, info["color"]
            )
            txt_linea2 = self.fuente_desc.render(
                f"{info['descripcion']}  →  (Tecla de uso en juego: [{t_uso}])",
                True, (210, 215, 225)
            )

            pantalla.blit(txt_linea1, (125, y_item + 12))
            pantalla.blit(txt_linea2, (125, y_item + 42))

            y_item += 90

        # Feedback de compra (solo lectura, sin mutación de estado)
        if self.tiempo_feedback > 0.0:
            surf_fb = self.fuente_item.render(self.mensaje_feedback, True, self.color_feedback)
            pantalla.blit(surf_fb, surf_fb.get_rect(center=(self.ancho // 2, y_item + 15)))

        # MODIFICADO: Instrucción de retorno al juego inequívoca
        surf_salir = self.fuente_pie.render("Presiona [M] o [ESC] para VOLVER AL JUEGO", True, (160, 220, 255))
        pantalla.blit(surf_salir, surf_salir.get_rect(center=(self.ancho // 2, self.alto - 65)))
