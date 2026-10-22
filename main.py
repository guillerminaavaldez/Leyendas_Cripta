# MODULARIZADO: Punto de entrada principal y orquestador del juego "Leyendas de la Cripta"
import os
import sys

# Ocultar mensaje promocional de pygame en consola
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Asegurar compatibilidad de importación para módulos en src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pygame
from config import (
    ANCHO, ALTO, FPS, TITULO_VENTANA, RECT_META,
    RUTA_HEROE, RUTA_ENEMIGO, VELOCIDAD_HEROE, VELOCIDAD_ENEMIGO,
    POS_INICIAL_HEROE, POS_INICIAL_ENEMIGO, RECOMPENSA_POR_NIVEL, NIVEL_MAXIMO
)
from src.personajes import Jugador, Enemigo
from src.colisiones import detectar_colision
from src.tienda import TiendaPociones
from src.niveles import GestorNiveles
from src.eventos import procesar_eventos
from src.renderizado import Renderizador

def cargar_archivo_env():
    """Carga variables desde el archivo .env o .venv si existe y no están definidas en el sistema."""
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

cargar_archivo_env()

# Variables de entorno para credenciales de base de datos
DB_USUARIO = os.getenv("DB_USUARIO")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def main():
    # Validación de credenciales desde variables de entorno
    global DB_USUARIO, DB_PASSWORD
    DB_USUARIO = os.getenv("DB_USUARIO")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not DB_USUARIO or not DB_PASSWORD:
        print("Error: Las variables de entorno DB_USUARIO y DB_PASSWORD son obligatorias.")
        sys.exit(1)

    print(f"Conectando usuario: {DB_USUARIO}")

    # 1. Inicialización de pygame y ventana
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption(TITULO_VENTANA)
    reloj = pygame.time.Clock()

    # 2. Creación de componentes principales
    jugador = Jugador(x=POS_INICIAL_HEROE[0], y=POS_INICIAL_HEROE[1], velocidad=VELOCIDAD_HEROE, ruta_imagen=RUTA_HEROE)
    enemigo = Enemigo(x=POS_INICIAL_ENEMIGO[0], y=POS_INICIAL_ENEMIGO[1], velocidad=VELOCIDAD_ENEMIGO, ruta_imagen=RUTA_ENEMIGO)

    gestor_niveles = GestorNiveles(RECT_META)
    obstaculos = gestor_niveles.iniciar_nivel(gestor_niveles.nivel_actual, jugador, enemigo)

    tienda = TiendaPociones(ANCHO, ALTO)
    renderizador = Renderizador()

    # 3. Control de estados y mensajes temporales
    estado_juego = "jugando"  # Estados: "jugando", "tienda", "victoria_nivel", "derrota", "juego_completado"
    estado_previo = "jugando"

    mensaje_hud = ""
    frames_mensaje_hud = 0
    color_mensaje_hud = (255, 255, 255)

    def mostrar_aviso_hud(texto: str, color: tuple = (255, 255, 200)):
        nonlocal mensaje_hud, frames_mensaje_hud, color_mensaje_hud
        mensaje_hud = texto
        color_mensaje_hud = color
        frames_mensaje_hud = 120

    ejecutando = True

    # ==================== BUCLE PRINCIPAL ====================
    while ejecutando:
        # --- A. Procesamiento de Eventos ---
        ejecutando, estado_juego, estado_previo, obstaculos = procesar_eventos(
            estado_juego,
            estado_previo,
            jugador,
            enemigo,
            tienda,
            gestor_niveles,
            obstaculos,
            mostrar_aviso_hud
        )

        # --- B. Actualización Lógica ---
        if estado_juego == "jugando":
            # Movimiento continuo del héroe
            teclas = pygame.key.get_pressed()
            jugador.mover_con_obstaculos(teclas, ANCHO, ALTO, obstaculos)

            # Persecución del enemigo con soporte de retraso
            enemigo.perseguir_con_retraso(jugador.x, jugador.y, ANCHO, ALTO)

            # Actualización de predicción si está activa
            if enemigo.mostrar_prediccion:
                enemigo.frames_prediccion -= 1
                if enemigo.frames_prediccion <= 0:
                    enemigo.mostrar_prediccion = False
                else:
                    enemigo.prediccion_pos = enemigo.calcular_siguiente_posicion(jugador.x, jugador.y)

            # Detección de colisiones y meta
            resultado = detectar_colision(jugador, enemigo, RECT_META)
            if resultado == "derrota":
                estado_juego = "derrota"
            elif resultado == "victoria":
                jugador.monedas += RECOMPENSA_POR_NIVEL
                if gestor_niveles.nivel_actual >= NIVEL_MAXIMO:
                    estado_juego = "juego_completado"
                else:
                    estado_juego = "victoria_nivel"

        # --- C. Renderizado Gráfico ---
        renderizador.dibujar_escenario(pantalla, gestor_niveles.nivel_actual, RECT_META, obstaculos)
        renderizador.dibujar_actores(pantalla, jugador, enemigo)
        renderizador.dibujar_hud(pantalla, gestor_niveles.nivel_actual, jugador, mensaje_hud, frames_mensaje_hud, color_mensaje_hud)
        renderizador.dibujar_overlays(pantalla, estado_juego, gestor_niveles.nivel_actual, jugador, tienda)

        if frames_mensaje_hud > 0:
            frames_mensaje_hud -= 1

        # --- D. Actualización de Pantalla y Temporización ---
        pygame.display.flip()
        reloj.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
