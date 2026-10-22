import os
import math
import pygame


def cargar_sprite_seguro(ruta_imagen, tamano, color_fallback):
    """
    Carga una imagen de forma segura compatible con cualquier versión de Python/Pygame.
    Si la versión de Pygame no tiene soporte de PNG extendido (ej. Python 3.14 en macOS),
    intenta cargar la versión .bmp equivalente o genera una superficie visual por defecto.
    """
    if ruta_imagen:
        # 1. Intentar cargar la ruta directa
        try:
            img = pygame.image.load(ruta_imagen).convert_alpha()
            return pygame.transform.scale(img, (tamano, tamano))
        except Exception:
            pass

        # 2. Si falla y es .png, probar con el archivo .bmp equivalente
        if ruta_imagen.lower().endswith(".png"):
            ruta_bmp = ruta_imagen[:-4] + ".bmp"
            if os.path.exists(ruta_bmp):
                try:
                    img = pygame.image.load(ruta_bmp).convert_alpha()
                    return pygame.transform.scale(img, (tamano, tamano))
                except Exception:
                    pass

    # 3. Fallback en caso de que no haya imagen o formato no soportado
    surf = pygame.Surface((tamano, tamano), pygame.SRCALPHA)
    pygame.draw.circle(surf, color_fallback, (tamano // 2, tamano // 2), tamano // 2 - 2)
    pygame.draw.circle(surf, (255, 255, 255), (tamano // 2, tamano // 2), tamano // 2 - 2, width=2)
    return surf


class Personaje:
    TAMANO_SPRITE = 80  # Tamaño equilibrado para visibilidad y pasillos entre obstáculos

    def __init__(self, x, y, velocidad, ruta_imagen=None, color_fallback=(0, 150, 255)):
        self.x = float(x)
        self.y = float(y)
        self.velocidad = velocidad

        self.imagen = cargar_sprite_seguro(ruta_imagen, self.TAMANO_SPRITE, color_fallback)
        self.rect = self.imagen.get_rect()
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def actualizar_rect(self):
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


class Jugador(Personaje):
    def __init__(self, x, y, velocidad=240.0, ruta_imagen=None):
        super().__init__(x, y, velocidad, ruta_imagen, color_fallback=(0, 200, 100))
        # Sistema de economía e inventario
        self.monedas = 0
        self.pociones = {
            "retraso": 0,
            "salto": 0,
            "vision": 0
        }
        self.vivo = True
        self.ha_ganado = False
        self.colision_procesada = False

    def mover_con_obstaculos(self, teclas, ancho, alto, obstaculos, dt: float):
        """
        Mueve al jugador evaluando colisiones eje por eje contra los obstáculos,
        utilizando paso de integración basado en dt (unidades en px/s).
        """
        paso = self.velocidad * dt
        dx = 0.0
        dy = 0.0

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= paso
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += paso
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= paso
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += paso

        # Movimiento en eje X y resolución de colisión
        if dx != 0.0:
            self.x += dx
            self.x = max(0.0, min(self.x, float(ancho - self.rect.width)))
            self.actualizar_rect()
            for obs in obstaculos:
                if self.rect.colliderect(obs.rect):
                    if dx > 0:  # Moviendo a la derecha
                        self.rect.right = obs.rect.left
                    elif dx < 0:  # Moviendo a la izquierda
                        self.rect.left = obs.rect.right
                    self.x = float(self.rect.x)

        # Movimiento en eje Y y resolución de colisión
        if dy != 0.0:
            self.y += dy
            self.y = max(0.0, min(self.y, float(alto - self.rect.height)))
            self.actualizar_rect()
            for obs in obstaculos:
                if self.rect.colliderect(obs.rect):
                    if dy > 0:  # Moviendo hacia abajo
                        self.rect.bottom = obs.rect.top
                    elif dy < 0:  # Moviendo hacia arriba
                        self.rect.top = obs.rect.bottom
                    self.y = float(self.rect.y)


class Enemigo(Personaje):
    def __init__(self, x, y, velocidad=132.0, ruta_imagen=None):
        super().__init__(x, y, velocidad, ruta_imagen, color_fallback=(220, 50, 50))
        # Temporizador de retraso por Poción 1 (en segundos)
        self.tiempo_retraso: float = 0.0
        # Estado y temporizador de predicción por Poción 3 (en segundos)
        self.mostrar_prediccion: bool = False
        self.prediccion_pos = (float(x), float(y))
        self.tiempo_prediccion: float = 0.0

    def calcular_siguiente_posicion(self, objetivo_x, objetivo_y, horizon_seg: float = 1.5):
        """
        Calcula las coordenadas (x, y) donde estará el enemigo dentro de
        ``horizon_seg`` segundos si persigue al jugador sin obstáculos.

        Usa la velocidad real del enemigo para que la proyección sea
        proporcional al movimiento real, evitando el offset fijo de 30 px
        que quedaba solapado con el propio sprite (80×80 px).

        :param objetivo_x: Posición X actual del jugador.
        :param objetivo_y: Posición Y actual del jugador.
        :param horizon_seg: Segundos hacia el futuro que se proyectan.
        :return: Tupla (x, y) de la posición proyectada.
        """
        dx = objetivo_x - self.x
        dy = objetivo_y - self.y
        distancia = math.hypot(dx, dy)
        if distancia == 0:
            return self.x, self.y

        # Desplazamiento máximo posible en el horizonte de tiempo
        desplazamiento = min(distancia, self.velocidad * horizon_seg)
        step_x = (dx / distancia) * desplazamiento
        step_y = (dy / distancia) * desplazamiento
        return self.x + step_x, self.y + step_y

    def perseguir_con_retraso(self, objetivo_x, objetivo_y, ancho, alto, dt: float):
        """
        Persigue al jugador aplicando la lógica de retraso temporal (dt).
        Previene el sobrepaso (overshooting) si dt es grande.
        """
        # Si tiene retraso activo, consume tiempo y no se desplaza
        if self.tiempo_retraso > 0.0:
            self.tiempo_retraso -= dt
            if self.tiempo_retraso < 0.0:
                self.tiempo_retraso = 0.0
            return

        dx = objetivo_x - self.x
        dy = objetivo_y - self.y
        distancia = math.hypot(dx, dy)

        if distancia > 0.0:
            # Prevención de sobrepaso: el paso no puede superar la distancia directa
            paso = min(distancia, self.velocidad * dt)
            step_x = (dx / distancia) * paso
            step_y = (dy / distancia) * paso

            self.x += step_x
            self.y += step_y

            # Mantener dentro de los límites de la pantalla
            self.x = max(0.0, min(self.x, float(ancho - self.rect.width)))
            self.y = max(0.0, min(self.y, float(alto - self.rect.height)))
            self.actualizar_rect()
