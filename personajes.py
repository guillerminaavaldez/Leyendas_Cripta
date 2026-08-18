import pygame
import math


class Personaje:
    # Tamaño objetivo del sprite en pantalla. Los archivos .png originales
    # vienen a 256x256px, demasiado grandes para una ventana de 800x600:
    # dejaban un hitbox tan enorme que colisionaba con casi cualquier
    # posición cercana a la meta. Los reescalamos a algo manejable.
    TAMANO_SPRITE = 150

    def __init__(self, x, y, velocidad, ruta_imagen):
        # Usar floats para la posición para movimientos suaves
        self.x = float(x)
        self.y = float(y)
        self.velocidad = velocidad

        imagen_original = pygame.image.load(ruta_imagen).convert_alpha()
        self.imagen = pygame.transform.scale(
            imagen_original, (self.TAMANO_SPRITE, self.TAMANO_SPRITE)
        )

        self.rect = self.imagen.get_rect()
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def cargar_imagen(self, ruta_imagen):
        imagen_original = pygame.image.load(ruta_imagen).convert_alpha()
        self.imagen = pygame.transform.scale(
            imagen_original, (self.TAMANO_SPRITE, self.TAMANO_SPRITE)
        )
        self.rect = self.imagen.get_rect()
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

class Jugador(Personaje):
    def __init__(self, x, y, velocidad, ruta_imagen):
        super().__init__(x, y, velocidad, ruta_imagen)

    def mover(self, teclas, ancho, alto):
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.x -= self.velocidad
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.x += self.velocidad
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            self.y -= self.velocidad
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            self.y += self.velocidad

        # Mantener dentro de los límites (usar floats, luego actualizar rect como ints)
        self.x = max(0.0, min(self.x, float(ancho - self.rect.width)))
        self.y = max(0.0, min(self.y, float(alto - self.rect.height)))

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

class Enemigo(Personaje):
    def __init__(self, x, y, velocidad, ruta_imagen):
        super().__init__(x, y, velocidad, ruta_imagen)

    def perseguir(self, objetivo_x, objetivo_y, pasos, ancho, alto, jugador=None):
        """
        Mueve al enemigo hacia (objetivo_x, objetivo_y) replicando el número de pasos
        recibidos. Cada paso mueve al enemigo en la dirección hacia el objetivo una
        distancia igual a `self.velocidad`.

        Si se pasa la instancia `jugador`, la función comprueba colisión en cada
        subpaso y devuelve True inmediatamente si ocurre una colisión.
        """
        for _ in range(max(0, int(pasos))):
            dx = objetivo_x - self.x
            dy = objetivo_y - self.y
            if dx == 0 and dy == 0:
                break
            distancia = math.hypot(dx, dy)
            if distancia == 0:
                break
            # Movimiento proporcional normalizado por la distancia
            step_x = (dx / distancia) * self.velocidad
            step_y = (dy / distancia) * self.velocidad

            self.x += step_x
            self.y += step_y

            # Mantener dentro de los límites
            self.x = max(0.0, min(self.x, float(ancho - self.rect.width)))
            self.y = max(0.0, min(self.y, float(alto - self.rect.height)))

            self.rect.x = int(self.x)
            self.rect.y = int(self.y)

            # Si se pasó la instancia del jugador, comprobar colisión en este subpaso
            if jugador is not None:
                if self.rect.colliderect(jugador.rect):
                    # Marcar en el jugador que la colisión fue procesada para evitar
                    # re-procesos y mantener consistencia con detectar_colision
                    try:
                        jugador.colision_procesada = True
                    except Exception:
                        pass
                    try:
                        jugador.vivo = False
                    except Exception:
                        pass
                    return True

        return False

    # --- nueva lógica para procesar pasos con retraso ---
    def añadir_pasos(self, pasos: int, delay_frames: int = 0, threshold: int = 1):
        """Añade pasos pendientes que el enemigo ejecutará.

        - `delay_frames`: frames de espera antes de empezar a procesar (puede ser 0).
        - `threshold`: número mínimo de pasos acumulados necesario para que el enemigo
          comience a ejecutar movimientos.
        """
        try:
            self.pending_steps += int(pasos)
        except AttributeError:
            self.pending_steps = max(0, int(pasos))
        # establecer al menos el retraso solicitado
        try:
            self.wait_frames = max(self.wait_frames, int(delay_frames))
        except AttributeError:
            self.wait_frames = int(delay_frames)
        # establecer el umbral de activación
        try:
            self.chase_threshold = max(self.chase_threshold, int(threshold))
        except AttributeError:
            self.chase_threshold = max(1, int(threshold))

    def procesar_pasos(self, ancho, alto, jugador=None, max_steps_per_frame: int = 1):
        """
        Procesa hasta `max_steps_per_frame` pasos pendientes. Si `wait_frames` > 0,
        decrementa y no procesa en este frame. Devuelve True si durante el procesamiento
        ocurrió una colisión con `jugador`.
        """
        if getattr(self, "wait_frames", 0) > 0:
            self.wait_frames -= 1
            return False

        pasos_pend = getattr(self, "pending_steps", 0)
        if pasos_pend <= 0:
            return False

        # No procesar hasta que se alcance el umbral de pasos acumulados
        threshold = getattr(self, "chase_threshold", 1)
        if pasos_pend < threshold:
            return False

        pasos_a_ejecutar = min(pasos_pend, max(0, int(max_steps_per_frame)))
        collided = False
        if pasos_a_ejecutar > 0:
            # usar la posición actual del jugador como objetivo si se provee
            if jugador is not None:
                objetivo_x, objetivo_y = jugador.x, jugador.y
            else:
                objetivo_x = self.x
                objetivo_y = self.y

            collided = self.perseguir(objetivo_x, objetivo_y, pasos_a_ejecutar, ancho, alto, jugador=jugador)
            self.pending_steps = max(0, pasos_pend - pasos_a_ejecutar)

        return bool(collided)
