# MODULARIZADO: Módulo de configuración y constantes generales del juego
import os
import pygame

# Dimensiones de la ventana de juego
ANCHO = 850
ALTO = 650
FPS = 60

# Título de la ventana
TITULO_VENTANA = "Leyendas de la Cripta - Edición Pociones y Niveles"

# Configuración de niveles y recompensas
NIVEL_INICIAL = 1
NIVEL_MAXIMO = 3
RECOMPENSA_POR_NIVEL = 50

# Configuración de la Meta (Posición Ganadora)
TAM_META = 80
RECT_META = pygame.Rect(ANCHO - TAM_META - 20, ALTO - TAM_META - 20, TAM_META, TAM_META)

# Paletas de color de fondo por nivel
COLORES_FONDO = {
    1: (20, 24, 35),   # Nivel 1: Azul Cripta
    2: (22, 34, 28),   # Nivel 2: Verde Profundo
    3: (38, 22, 22)    # Nivel 3: Carmesí Oscuro
}

# Rutas de recursos y assets
RUTA_BASE = os.path.dirname(__file__)
RUTA_ASSETS = os.path.join(RUTA_BASE, "assets")
RUTA_HEROE = os.path.join(RUTA_ASSETS, "heroe_pygame.png")
RUTA_ENEMIGO = os.path.join(RUTA_ASSETS, "enemigo_pygame.png")

# Configuración inicial de personajes
POS_INICIAL_HEROE = (40.0, 40.0)
VELOCIDAD_HEROE = 4.0

POS_INICIAL_ENEMIGO = (float(ANCHO - 120), 40.0)
VELOCIDAD_ENEMIGO = 2.2
