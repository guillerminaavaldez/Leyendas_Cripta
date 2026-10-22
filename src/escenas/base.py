"""
Módulo base para la jerarquía de escenas de Leyendas de la Cripta.
Define el contrato abstracto que toda escena debe implementar.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List

import pygame

if TYPE_CHECKING:
    from src.gestor_escenas import GestorEscenas


class EscenaBase(ABC):
    """
    Clase base abstracta que representa el ciclo de vida de una escena o pantalla.

    Cada escena encapsula su propio manejo de eventos, actualización lógica y renderizado,
    eliminando la necesidad de condicionales anidados en el bucle principal.
    """

    def __init__(self, gestor: GestorEscenas) -> None:
        """
        Inicializa la escena vinculándola a su gestor de escenas.

        :param gestor: Referencia al GestorEscenas que controla la navegación.
        """
        self.gestor: GestorEscenas = gestor

    def al_entrar(self, **datos: Any) -> None:
        """
        Gancho (hook) opcional invocado al realizar la transición hacia esta escena.

        :param datos: Argumentos por palabra clave transmitidos desde la escena previa
                      (por ejemplo: salud restante, puntaje acumulado, inventario).
        """
        pass

    def al_salir(self) -> None:
        """
        Gancho (hook) opcional invocado inmediatamente antes de abandonar esta escena.
        Útil para detener música, persistir estados temporales o liberar memoria.
        """
        pass

    @abstractmethod
    def manejar_eventos(self, eventos: List[pygame.event.Event]) -> None:
        """
        Procesa la lista de eventos de entrada capturados en el frame actual.

        :param eventos: Colección de eventos provistos por pygame.event.get().
        """
        pass

    @abstractmethod
    def actualizar(self, dt: float) -> None:
        """
        Avanza la lógica de simulación y el estado interno de la escena.

        :param dt: Tiempo transcurrido (delta time) desde el frame anterior.
        """
        pass

    @abstractmethod
    def dibujar(self, pantalla: pygame.Surface) -> None:
        """
        Renderiza los elementos gráficos de la escena sobre la superficie de destino.

        :param pantalla: Superficie principal de Pygame sobre la cual dibujar.
        """
        pass
