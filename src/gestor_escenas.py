"""
Módulo del Gestor de Escenas (Scene Manager).
Implementa el patrón State/Mediator para desacoplar y orquestar las pantallas del juego.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

import pygame
from src.escenas.base import EscenaBase


class GestorEscenas:
    """
    Controlador central del flujo de navegación y del ciclo de vida de las escenas.

    Almacena las escenas registradas y delega los eventos, la actualización y
    el renderizado a la escena activa en cada iteración del bucle principal.
    """

    def __init__(self) -> None:
        """Inicializa el registro de escenas y el estado de ejecución."""
        self._escenas: Dict[str, EscenaBase] = {}
        self.escena_actual: Optional[EscenaBase] = None
        self.nombre_escena_actual: Optional[str] = None
        self.ejecutando: bool = True

    def registrar(self, nombre: str, escena: EscenaBase) -> None:
        """
        Registra una escena en el diccionario de estados bajo un identificador único.

        :param nombre: Clave identificadora de la escena (usualmente constante de config).
        :param escena: Instancia de EscenaBase a asociar.
        """
        self._escenas[nombre] = escena

    def cambiar_escena(self, nombre: str, **datos: Any) -> None:
        """
        Ejecuta la transición hacia una nueva escena previamente registrada.

        Invoca `al_salir()` en la escena saliente y `al_entrar(**datos)` en la entrante,
        permitiendo transferir información arbitraria entre escenas sin acoplarlas.

        :param nombre: Identificador de la escena destino.
        :param datos: Argumentos por palabra clave transmitidos a la escena destino.
        :raises KeyError: Si el nombre especificado no corresponde a ninguna escena registrada.
        """
        if nombre not in self._escenas:
            disponibles = ", ".join(repr(k) for k in self._escenas.keys()) or "ninguna"
            raise KeyError(
                f"No se puede cambiar a la escena '{nombre}'. "
                f"La escena no está registrada en el GestorEscenas. "
                f"Escenas registradas actualmente: [{disponibles}]."
            )

        # 1. Notificar salida de la escena saliente
        if self.escena_actual is not None:
            self.escena_actual.al_salir()

        # 2. Conmutar a la nueva escena
        self.nombre_escena_actual = nombre
        self.escena_actual = self._escenas[nombre]

        # 3. Notificar entrada transmitiendo datos de transición
        self.escena_actual.al_entrar(**datos)

    def salir(self) -> None:
        """Indica que el bucle principal de la aplicación debe detenerse."""
        self.ejecutando = False

    def manejar_eventos(self, eventos: List[pygame.event.Event]) -> None:
        """
        Delega el procesamiento de eventos a la escena activa.

        :param eventos: Colección de eventos de Pygame capturados en el frame.
        """
        if self.escena_actual is not None:
            self.escena_actual.manejar_eventos(eventos)

    def actualizar(self, dt: float) -> None:
        """
        Delega la actualización de la simulación a la escena activa.

        :param dt: Delta time transcurrido desde el último frame.
        """
        if self.escena_actual is not None:
            self.escena_actual.actualizar(dt)

    def dibujar(self, pantalla: pygame.Surface) -> None:
        """
        Delega la presentación gráfica a la escena activa.

        :param pantalla: Superficie de Pygame sobre la cual se renderiza.
        """
        if self.escena_actual is not None:
            self.escena_actual.dibujar(pantalla)
