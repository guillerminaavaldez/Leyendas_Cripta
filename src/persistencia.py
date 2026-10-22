import os
import sqlite3
from typing import Optional, Tuple


def _ruta_db() -> str:
    """Devuelve la ruta absoluta del archivo de base de datos dentro de la carpeta data/."""
    carpeta_data = os.path.join(os.path.dirname(__file__), "data")
    return os.path.join(carpeta_data, "partidas.db")


def inicializar_db() -> None:
    """
    Crea la carpeta `data/` si no existe y crea la tabla `partidas`.
    La tabla usa `id` como PRIMARY KEY para permitir `INSERT OR REPLACE`.
    """
    carpeta_data = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(carpeta_data, exist_ok=True)

    conn = sqlite3.connect(_ruta_db())
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS partidas (
                id INTEGER PRIMARY KEY,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def guardar_partida(x: int, y: int) -> None:
    """
    Guarda la posición del jugador usando `id = 1` fijo.
    Se usa `INSERT OR REPLACE` para sobrescribir la partida anterior en la misma fila.
    Cada llamada abre y cierra su propia conexión.
    """
    # Asegurar que la DB y la tabla existen
    inicializar_db()

    conn = sqlite3.connect(_ruta_db())
    try:
        conn.execute(
            "INSERT OR REPLACE INTO partidas (id, x, y) VALUES (1, ?, ?)",
            (int(x), int(y)),
        )
        conn.commit()
    finally:
        conn.close()

    # Confirmación visible en consola: si presionás G y no ves esta línea,
    # el problema es que esta función nunca se está llamando desde main.py.
    print(f"[Partida guardada] x={int(x)}, y={int(y)}")


def cargar_partida() -> Optional[Tuple[int, int]]:
    inicializar_db()

    conn = sqlite3.connect(_ruta_db())
    try:
        cur = conn.execute("SELECT x, y FROM partidas WHERE id = 1 LIMIT 1")
        fila = cur.fetchone()
        if fila is None:
            return None
        return int(fila[0]), int(fila[1])
    finally:
        conn.close()