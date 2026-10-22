# MODULARIZADO: Punto de entrada principal y orquestador del juego "Leyendas de la Cripta"
import os
import sys

# Ocultar mensaje promocional de pygame en consola
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Asegurar compatibilidad de importación para módulos en src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pygame
from config import (
    ANCHO,
    ALTO,
    FPS,
    DT_MAX,
    TITULO_VENTANA,
    ESCENA_MENU,
    ESCENA_NIVEL_1,
)
from src.gestor_escenas import GestorEscenas
from src.escenas.menu import EscenaMenu
from src.escenas.nivel1 import EscenaNivel1


def cargar_archivo_env() -> None:
    """Carga variables desde el archivo .env si existe y no están definidas en el sistema."""
    for nombre in [".env", ".venv"]:
        ruta = os.path.join(os.path.dirname(__file__), nombre)
        if os.path.isfile(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea or linea.startswith("#"):
                        continue
                    if "=" in linea:
                        clave, valor = linea.split("=", 1)
                        clave = clave.strip()
                        valor = valor.strip().strip("\"'")
                        if clave and clave not in os.environ:
                            os.environ[clave] = valor
            break


# Carga preliminar de variables de entorno
cargar_archivo_env()

# Variables de entorno para credenciales de base de datos
DB_USUARIO = os.getenv("DB_USUARIO")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def main() -> None:
    # 1. Validación de credenciales desde variables de entorno
    global DB_USUARIO, DB_PASSWORD
    DB_USUARIO = os.getenv("DB_USUARIO")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not DB_USUARIO or not DB_PASSWORD:
        print("Error: Las variables de entorno DB_USUARIO y DB_PASSWORD son obligatorias.")
        sys.exit(1)

    print(f"Conectando usuario: {DB_USUARIO}")

    # 2. Inicialización de Pygame y ventana principal
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption(TITULO_VENTANA)
    reloj = pygame.time.Clock()

    # 3. Inicialización del Gestor de Escenas y registro de pantallas
    gestor = GestorEscenas()
    gestor.registrar(ESCENA_MENU, EscenaMenu(gestor))
    gestor.registrar(ESCENA_NIVEL_1, EscenaNivel1(gestor))

    # 4. Estado inicial: comenzar en el Menú Principal
    gestor.cambiar_escena(ESCENA_MENU)

    # ==================== BUCLE PRINCIPAL ====================
    while gestor.ejecutando:
        # A. Control de tasa de cuadros y cálculo de Delta Time (en segundos)
        # Tope de seguridad (DT_MAX = 0.05s / máx 20 FPS equivalentes):
        # Si la ventana se congela, se arrastra o sufre una caída abrupta de rendimiento,
        # un dt sin límite provocaría un paso de integración física gigantesco en un único frame.
        # Ese salto desmedido haría que el héroe o enemigo 'atraviesen' paredes y obstáculos
        # por falta de colisión intermedia (fenómeno conocido como tunneling o efecto túnel).
        dt_real = reloj.tick(FPS) / 1000.0
        dt = min(dt_real, DT_MAX)

        # B. Captura única de eventos por cuadro
        eventos = pygame.event.get()

        # C. Delegación del ciclo de vida a la escena activa
        gestor.manejar_eventos(eventos)
        gestor.actualizar(dt)
        gestor.dibujar(pantalla)

        # D. Refresco de pantalla
        pygame.display.flip()

    # 5. Salida limpia de recursos
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
