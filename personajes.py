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
    def __init__(self, x, y, velocidad=4, ruta_imagen=None):
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

    def mover_con_obstaculos(self, teclas, ancho, alto, obstaculos):
        """
        Mueve al jugador evaluando colisiones eje por eje contra los obstáculos.
        """
        dx = 0
        dy = 0

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= self.velocidad
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += self.velocidad
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= self.velocidad
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += self.velocidad

        # Movimiento en eje X y resolución de colisión
        if dx != 0:
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
        if dy != 0:
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
    def __init__(self, x, y, velocidad=2.2, ruta_imagen=None):
        super().__init__(x, y, velocidad, ruta_imagen, color_fallback=(220, 50, 50))
        # Contador de retrasos por Poción 1
        self.movimientos_retraso = 0
        # Estado de predicción para Poción 3
        self.mostrar_prediccion = False
        self.prediccion_pos = (x, y)
        self.frames_prediccion = 0

    def calcular_siguiente_posicion(self, objetivo_x, objetivo_y):
        """Calcula las coordenadas (x, y) del próximo paso sin modificar la posición actual."""
        dx = objetivo_x - self.x
        dy = objetivo_y - self.y
        distancia = math.hypot(dx, dy)
        if distancia == 0:
            return self.x, self.y

        step_x = (dx / distancia) * self.velocidad * 10  # Proyección visible
        step_y = (dy / distancia) * self.velocidad * 10
        return self.x + step_x, self.y + step_y

    def perseguir_con_retraso(self, objetivo_x, objetivo_y, ancho, alto):
        """
        Persigue al jugador aplicando la lógica de retraso por poción.
        """
        # Si tiene retraso activo, consume un frame/ciclo y no se mueve
        if self.movimientos_retraso > 0:
            self.movimientos_retraso -= 1
            return

        dx = objetivo_x - self.x
        dy = objetivo_y - self.y
        distancia = math.hypot(dx, dy)

        if distancia > 0:
            step_x = (dx / distancia) * self.velocidad
            step_y = (dy / distancia) * self.velocidad

            self.x += step_x
            self.y += step_y

            # Mantener dentro de los límites
            self.x = max(0.0, min(self.x, float(ancho - self.rect.width)))
            self.y = max(0.0, min(self.y, float(alto - self.rect.height)))
            self.actualizar_rect()
