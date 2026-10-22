"""
Módulo de la Escena del Nivel 1 (y juego principal) de Leyendas de la Cripta.
Encapsula la lógica de juego, ciclo de eventos, simulación física y renderizado.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Optional

import pygame

from config import (
    ANCHO,
    ALTO,
    RECT_META,
    RUTA_HEROE,
    RUTA_ENEMIGO,
    VELOCIDAD_HEROE,
    VELOCIDAD_ENEMIGO,
    POS_INICIAL_HEROE,
    POS_INICIAL_ENEMIGO,
    RECOMPENSA_POR_NIVEL,
    NIVEL_MAXIMO,
    NIVEL_INICIAL,
)
from src.escenas.base import EscenaBase
from src.personajes import Jugador, Enemigo
from src.colisiones import detectar_colision
from src.tienda import TiendaPociones
from src.niveles import GestorNiveles
from src.renderizado import Renderizador
from src.pociones import (
    usar_pocion_retraso,
    usar_pocion_salto,
    usar_pocion_vision,
)

if TYPE_CHECKING:
    from src.gestor_escenas import GestorEscenas


class EscenaNivel1(EscenaBase):
    """
    Escena principal de juego para los niveles de la cripta.

    Controla los actores (Héroe y Enemigo), la generación de obstáculos,
    el inventario/tienda de pociones y la transición entre sub-estados internos
    ("jugando", "tienda", "victoria_nivel", "derrota", "juego_completado").
    """

    def __init__(self, gestor: GestorEscenas) -> None:
        """
        Inicializa la escena instanciando los sistemas fijos (tienda y renderizador).

        :param gestor: Referencia al GestorEscenas central.
        """
        super().__init__(gestor)

        self.tienda: TiendaPociones = TiendaPociones(ANCHO, ALTO)
        self.renderizador: Renderizador = Renderizador()

        # Actores, niveles y obstáculos (configurados en al_entrar)
        self.gestor_niveles: GestorNiveles
        self.jugador: Jugador
        self.enemigo: Enemigo
        self.obstaculos: list = []

        # Sub-estados internos de la escena
        self.estado_juego: str = "jugando"
        self.estado_previo: str = "jugando"

        # Mensajería temporal del HUD
        self.mensaje_hud: str = ""
        self.frames_mensaje_hud: int = 0
        self.color_mensaje_hud: tuple[int, int, int] = (255, 255, 255)

    def al_entrar(self, **datos: Any) -> None:
        """
        Prepara una partida nueva o reanudada según los parámetros recibidos.

        :param datos: Diccionario opcional de datos. Acepta 'nivel' (int) para
                      especificar el nivel inicial de la partida.
        """
        nivel_inicial = int(datos.get("nivel", NIVEL_INICIAL))

        self.gestor_niveles = GestorNiveles(RECT_META)
        self.gestor_niveles.nivel_actual = nivel_inicial

        self.jugador = Jugador(
            x=POS_INICIAL_HEROE[0],
            y=POS_INICIAL_HEROE[1],
            velocidad=VELOCIDAD_HEROE,
            ruta_imagen=RUTA_HEROE,
        )
        self.enemigo = Enemigo(
            x=POS_INICIAL_ENEMIGO[0],
            y=POS_INICIAL_ENEMIGO[1],
            velocidad=VELOCIDAD_ENEMIGO,
            ruta_imagen=RUTA_ENEMIGO,
        )

        self.obstaculos = self.gestor_niveles.iniciar_nivel(
            self.gestor_niveles.nivel_actual, self.jugador, self.enemigo
        )

        self.estado_juego = "jugando"
        self.estado_previo = "jugando"

        self.mensaje_hud = ""
        self.frames_mensaje_hud = 0
        self.color_mensaje_hud = (255, 255, 255)

    def mostrar_aviso_hud(
        self, texto: str, color: tuple[int, int, int] = (255, 255, 200)
    ) -> None:
        """
        Publica un mensaje temporal con duración prefijada en el HUD.

        :param texto: Contenido del mensaje a presentar.
        :param color: Tupla RGB con el color de renderizado del texto.
        """
        self.mensaje_hud = texto
        self.color_mensaje_hud = color
        self.frames_mensaje_hud = 120

    def manejar_eventos(self, eventos: List[pygame.event.Event]) -> None:
        """
        Procesa las entradas de teclado discretas y comandos según el sub-estado activo.

        :param eventos: Lista de eventos de Pygame del frame actual.
        """
        for evento in eventos:
            if evento.type == pygame.QUIT:
                self.gestor.salir()
                return

            if evento.type == pygame.KEYDOWN:
                # --- NAVEGACIÓN HACIA LA TIENDA ([M]) ---
                if evento.key == pygame.K_m:
                    if self.estado_juego == "tienda":
                        self.estado_juego = self.estado_previo
                    else:
                        self.estado_previo = self.estado_juego
                        self.estado_juego = "tienda"

                # --- SUB-ESTADO: TIENDA ---
                elif self.estado_juego == "tienda":
                    if evento.key == pygame.K_ESCAPE:
                        self.estado_juego = self.estado_previo
                    elif evento.key == pygame.K_1:
                        self.tienda.comprar("retraso", self.jugador)
                    elif evento.key == pygame.K_2:
                        self.tienda.comprar("salto", self.jugador)
                    elif evento.key == pygame.K_3:
                        self.tienda.comprar("vision", self.jugador)

                # --- SUB-ESTADO: JUGANDO (USO DE POCIONES Y SALIDA) ---
                elif self.estado_juego == "jugando":
                    if evento.key == pygame.K_ESCAPE:
                        self.gestor.salir()
                    elif evento.key == pygame.K_t:
                        ok, msg = usar_pocion_retraso(self.jugador, self.enemigo)
                        self.mostrar_aviso_hud(msg, (80, 200, 255) if ok else (255, 100, 100))
                    elif evento.key == pygame.K_x:
                        ok, msg = usar_pocion_salto(
                            self.jugador, self.enemigo, ANCHO, ALTO, self.obstaculos
                        )
                        self.mostrar_aviso_hud(msg, (255, 200, 80) if ok else (255, 100, 100))
                    elif evento.key == pygame.K_y:
                        ok, msg = usar_pocion_vision(self.jugador, self.enemigo)
                        self.mostrar_aviso_hud(msg, (200, 100, 255) if ok else (255, 100, 100))

                # --- SUB-ESTADO: VICTORIA DE NIVEL ---
                elif self.estado_juego == "victoria_nivel":
                    if evento.key in (pygame.K_SPACE, pygame.K_RETURN):
                        nuevo_nivel, nuevos_obstaculos, nuevo_estado = self.gestor_niveles.avanzar_nivel(
                            self.jugador, self.enemigo
                        )
                        self.estado_juego = nuevo_estado
                        self.estado_previo = nuevo_estado
                        if nuevo_estado == "jugando":
                            self.obstaculos = nuevos_obstaculos
                            self.mostrar_aviso_hud(f"¡Nivel {nuevo_nivel} Iniciado!", (100, 255, 150))

                # --- SUB-ESTADOS: DERROTA O JUEGO COMPLETADO ---
                elif self.estado_juego in ("derrota", "juego_completado"):
                    if evento.key == pygame.K_r:
                        if self.estado_juego == "juego_completado":
                            self.obstaculos = self.gestor_niveles.reiniciar_partida(
                                self.jugador, self.enemigo
                            )
                        else:
                            self.obstaculos = self.gestor_niveles.iniciar_nivel(
                                self.gestor_niveles.nivel_actual, self.jugador, self.enemigo
                            )
                        self.estado_juego = "jugando"
                        self.estado_previo = "jugando"
                        self.mostrar_aviso_hud(
                            f"¡Nivel {self.gestor_niveles.nivel_actual} Reiniciado!", (100, 255, 150)
                        )
                    elif evento.key == pygame.K_ESCAPE:
                        self.gestor.salir()

    def obtener_teclas(self):
        """
        Devuelve el estado actual del teclado.

        Método de punto de extensión (seam) diseñado para facilitar las
        pruebas automatizadas: las subclases o mocks pueden sobreescribirlo
        para inyectar un mapa de teclas simuladas sin necesidad de abrir
        una ventana real de Pygame.

        :return: Secuencia compatible con pygame.key.get_pressed().
        """
        return pygame.key.get_pressed()

    def actualizar(self, dt: float) -> None:
        """
        Avanza la simulación del mundo del juego cuando el sub-estado es 'jugando'.

        :param dt: Delta time transcurrido desde el frame anterior.
        """
        if self.estado_juego == "jugando":
            # 1. Movimiento continuo del héroe según entrada analógica/teclado
            teclas = self.obtener_teclas()
            self.jugador.mover_con_obstaculos(teclas, ANCHO, ALTO, self.obstaculos, dt)

            # 2. Persecución del enemigo con soporte para estado de retraso
            self.enemigo.perseguir_con_retraso(self.jugador.x, self.jugador.y, ANCHO, ALTO,dt)

            # 3. Temporizador de predicción de ruta (Poción Y)
            # La posición ya se calcula al activar la poción; aquí solo
            # se consume el tiempo restante y se apaga al expirar.
            if self.enemigo.mostrar_prediccion:
                self.enemigo.tiempo_prediccion -= dt
                if self.enemigo.tiempo_prediccion <= 0:
                    self.enemigo.mostrar_prediccion = False
                    self.enemigo.tiempo_prediccion = 0.0

            # 4. Evaluación de colisiones con el enemigo y llegada a la meta
            resultado = detectar_colision(self.jugador, self.enemigo, RECT_META)
            if resultado == "derrota":
                self.estado_juego = "derrota"
            elif resultado == "victoria":
                self.jugador.monedas += RECOMPENSA_POR_NIVEL
                if self.gestor_niveles.nivel_actual >= NIVEL_MAXIMO:
                    self.estado_juego = "juego_completado"
                else:
                    self.estado_juego = "victoria_nivel"

        # Decremento del contador de visualización de avisos en HUD
        if self.frames_mensaje_hud > 0:
            self.frames_mensaje_hud -= 1

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """
        Renderiza el escenario, los actores, el HUD y las interfaces superpuestas.

        :param pantalla: Superficie principal de renderizado de Pygame.
        """
        # 1. Capa de fondo y obstáculos del nivel
        self.renderizador.dibujar_escenario(
            pantalla, self.gestor_niveles.nivel_actual, RECT_META, self.obstaculos
        )

        # 2. Capa de actores (Héroe y Enemigo con efectos de pociones)
        self.renderizador.dibujar_actores(pantalla, self.jugador, self.enemigo)

        # 3. Capa de HUD superior e información de estado
        self.renderizador.dibujar_hud(
            pantalla,
            self.gestor_niveles.nivel_actual,
            self.jugador,
            self.mensaje_hud,
            self.frames_mensaje_hud,
            self.color_mensaje_hud,
        )

        # 4. Capa de overlays (Tienda, Victoria, Derrota, Fin del Juego)
        self.renderizador.dibujar_overlays(
            pantalla,
            self.estado_juego,
            self.gestor_niveles.nivel_actual,
            self.jugador,
            self.tienda,
        )
