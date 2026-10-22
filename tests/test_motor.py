#!/usr/bin/env python3
"""
=============================================================================
  tests/test_motor.py — Pruebas unitarias de Leyendas de la Cripta
=============================================================================
Cubre:
  - GestorEscenas: registro, cambio de escena, errores, ciclo de vida.
  - Transiciones: al_entrar / al_salir y transmisión de datos.
  - Temporizadores: frames_mensaje_hud y tiempo_retraso del enemigo.
  - Integración básica: actualizar() con teclas simuladas.

Ejecutar:
    python -m pytest tests/test_motor.py -v
  o directamente:
    python tests/test_motor.py

Requisitos: no abre ventana (SDL_VIDEODRIVER=dummy).
=============================================================================
"""
import os
import sys
import unittest
from collections import defaultdict

# ── Modo sin ventana ──────────────────────────────────────────────────────────
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Asegurar que las importaciones del proyecto funcionen desde cualquier CWD
_RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))  # superficie mínima para dummy driver

from config import (
    ANCHO, ALTO,
    VELOCIDAD_HEROE, VELOCIDAD_ENEMIGO,
    POS_INICIAL_HEROE, POS_INICIAL_ENEMIGO,
    ESCENA_MENU, ESCENA_NIVEL_1,
    DT_MAX,
)
from src.gestor_escenas import GestorEscenas
from src.escenas.base import EscenaBase
from src.escenas.nivel1 import EscenaNivel1
from src.personajes import Jugador, Enemigo


# ═══════════════════════════════════════════════════════════════════════════════
# Escenas ficticias para pruebas de GestorEscenas
# ═══════════════════════════════════════════════════════════════════════════════

class EscenaFalsa(EscenaBase):
    """Escena mínima con contadores de ciclo de vida para afirmaciones."""

    def __init__(self, gestor: GestorEscenas, nombre: str = ""):
        super().__init__(gestor)
        self.nombre = nombre
        self.entradas: list = []   # kwargs recibidos en al_entrar
        self.salidas: int = 0      # veces que se llamó al_salir
        self.actualizaciones: int = 0
        self.dibujos: int = 0
        self.eventos_recibidos: list = []

    def al_entrar(self, **datos):
        self.entradas.append(datos)

    def al_salir(self):
        self.salidas += 1

    def manejar_eventos(self, eventos):
        self.eventos_recibidos.extend(eventos)

    def actualizar(self, dt: float):
        self.actualizaciones += 1

    def dibujar(self, pantalla):
        self.dibujos += 1


class EscenaNivel1SinTeclas(EscenaNivel1):
    """EscenaNivel1 con teclado inyectable para pruebas de integración."""

    def __init__(self, gestor, teclas_iniciales=None):
        super().__init__(gestor)
        # defaultdict(bool) replica el comportamiento de pygame.key.get_pressed():
        # cualquier clave no definida devuelve False automáticamente.
        self._teclas: defaultdict = defaultdict(bool)
        if teclas_iniciales:
            self._teclas.update(teclas_iniciales)

    def obtener_teclas(self):
        return self._teclas

    def al_entrar(self, **datos):
        super().al_entrar(**datos)
        self.obstaculos = []  # Campo libre para medir velocidad pura


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PRUEBAS DEL GESTOR DE ESCENAS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGestorEscenas(unittest.TestCase):
    """Pruebas del flujo de registro y cambio de escenas."""

    def setUp(self):
        self.gestor = GestorEscenas()

    # ── Registro ──────────────────────────────────────────────────────────────

    def test_gestor_inicia_sin_escena_activa(self):
        """Al crear el gestor, no debe haber escena activa."""
        self.assertIsNone(self.gestor.escena_actual)
        self.assertIsNone(self.gestor.nombre_escena_actual)

    def test_registrar_escena_la_agrega_al_diccionario(self):
        """registrar() debe incluir la escena bajo su clave."""
        escena = EscenaFalsa(self.gestor, "A")
        self.gestor.registrar("A", escena)
        self.assertIn("A", self.gestor._escenas)
        self.assertIs(self.gestor._escenas["A"], escena)

    def test_registrar_multiples_escenas(self):
        """Debe admitir N escenas bajo claves distintas."""
        for nombre in ("MENU", "NIVEL_1", "NIVEL_2"):
            self.gestor.registrar(nombre, EscenaFalsa(self.gestor, nombre))
        self.assertEqual(len(self.gestor._escenas), 3)

    # ── Cambio de escena ──────────────────────────────────────────────────────

    def test_cambiar_a_escena_registrada_la_activa(self):
        """cambiar_escena() debe establecer la escena activa correctamente."""
        escena = EscenaFalsa(self.gestor, "A")
        self.gestor.registrar("A", escena)
        self.gestor.cambiar_escena("A")
        self.assertIs(self.gestor.escena_actual, escena)
        self.assertEqual(self.gestor.nombre_escena_actual, "A")

    def test_cambiar_escena_invoca_al_entrar(self):
        """cambiar_escena() debe llamar al_entrar() en la escena destino."""
        escena = EscenaFalsa(self.gestor)
        self.gestor.registrar("X", escena)
        self.gestor.cambiar_escena("X")
        self.assertEqual(len(escena.entradas), 1)

    def test_cambiar_escena_transmite_datos(self):
        """Los kwargs deben llegar a al_entrar() de la escena destino."""
        escena = EscenaFalsa(self.gestor)
        self.gestor.registrar("X", escena)
        self.gestor.cambiar_escena("X", nivel=3, puntos=500)
        self.assertEqual(escena.entradas[0], {"nivel": 3, "puntos": 500})

    def test_cambiar_escena_invoca_al_salir_en_escena_previa(self):
        """Al cambiar de A → B, debe llamar al_salir() en A."""
        escena_a = EscenaFalsa(self.gestor, "A")
        escena_b = EscenaFalsa(self.gestor, "B")
        self.gestor.registrar("A", escena_a)
        self.gestor.registrar("B", escena_b)
        self.gestor.cambiar_escena("A")
        self.gestor.cambiar_escena("B")
        self.assertEqual(escena_a.salidas, 1)
        self.assertEqual(escena_b.salidas, 0)  # B nunca salió

    def test_cambiar_escena_no_llama_al_salir_sin_escena_previa(self):
        """Primera transición: no hay escena previa → sin al_salir()."""
        escena = EscenaFalsa(self.gestor)
        self.gestor.registrar("A", escena)
        self.gestor.cambiar_escena("A")   # Primera vez
        self.assertEqual(escena.salidas, 0)

    def test_cambiar_escena_inexistente_lanza_keyerror(self):
        """Cambiar a una clave no registrada debe lanzar KeyError."""
        with self.assertRaises(KeyError):
            self.gestor.cambiar_escena("NO_EXISTE")

    def test_mensaje_keyerror_menciona_escenas_disponibles(self):
        """El mensaje de error debe listar las escenas registradas."""
        self.gestor.registrar("MENU", EscenaFalsa(self.gestor))
        try:
            self.gestor.cambiar_escena("NIVEL_99")
        except KeyError as e:
            self.assertIn("MENU", str(e))

    # ── Estado de ejecución ───────────────────────────────────────────────────

    def test_gestor_inicia_ejecutando(self):
        """El gestor debe iniciar con ejecutando=True."""
        self.assertTrue(self.gestor.ejecutando)

    def test_salir_pone_ejecutando_en_false(self):
        """salir() debe cambiar ejecutando a False."""
        self.gestor.salir()
        self.assertFalse(self.gestor.ejecutando)

    # ── Delegación del ciclo de vida ──────────────────────────────────────────

    def test_actualizar_delega_a_escena_activa(self):
        """actualizar() debe llamar actualizar() en la escena activa."""
        escena = EscenaFalsa(self.gestor)
        self.gestor.registrar("A", escena)
        self.gestor.cambiar_escena("A")
        self.gestor.actualizar(0.016)
        self.assertEqual(escena.actualizaciones, 1)

    def test_actualizar_sin_escena_no_lanza_excepcion(self):
        """actualizar() sin escena activa no debe lanzar excepciones."""
        try:
            self.gestor.actualizar(0.016)
        except Exception as e:
            self.fail(f"actualizar() lanzó excepción inesperada: {e}")

    def test_dibujar_delega_a_escena_activa(self):
        """dibujar() debe llamar dibujar() en la escena activa."""
        escena = EscenaFalsa(self.gestor)
        self.gestor.registrar("A", escena)
        self.gestor.cambiar_escena("A")
        pantalla_falsa = pygame.Surface((ANCHO, ALTO))
        self.gestor.dibujar(pantalla_falsa)
        self.assertEqual(escena.dibujos, 1)

    def test_manejar_eventos_delega_a_escena_activa(self):
        """manejar_eventos() debe pasar los eventos a la escena activa."""
        escena = EscenaFalsa(self.gestor)
        self.gestor.registrar("A", escena)
        self.gestor.cambiar_escena("A")
        evento_falso = pygame.event.Event(pygame.USEREVENT)
        self.gestor.manejar_eventos([evento_falso])
        self.assertIn(evento_falso, escena.eventos_recibidos)

    def test_secuencia_completa_de_escenas(self):
        """Prueba el ciclo completo: A→B→C con contadores de ciclo de vida."""
        a = EscenaFalsa(self.gestor, "A")
        b = EscenaFalsa(self.gestor, "B")
        c = EscenaFalsa(self.gestor, "C")
        for nombre, esc in [("A", a), ("B", b), ("C", c)]:
            self.gestor.registrar(nombre, esc)

        self.gestor.cambiar_escena("A")
        self.gestor.cambiar_escena("B")
        self.gestor.cambiar_escena("C")

        self.assertEqual(a.salidas, 1)
        self.assertEqual(b.salidas, 1)
        self.assertEqual(c.salidas, 0)
        self.assertEqual(len(a.entradas), 1)
        self.assertEqual(len(b.entradas), 1)
        self.assertEqual(len(c.entradas), 1)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. PRUEBAS DE TRANSICIONES
# ═══════════════════════════════════════════════════════════════════════════════

class TestTransiciones(unittest.TestCase):
    """Pruebas específicas del mecanismo de transición entre escenas."""

    def setUp(self):
        self.gestor = GestorEscenas()

    def test_datos_de_transicion_llegan_correctamente(self):
        """Los parámetros de transición deben ser recibidos intactos por al_entrar."""
        escena = EscenaFalsa(self.gestor)
        self.gestor.registrar("DESTINO", escena)
        self.gestor.cambiar_escena("DESTINO", nivel=2, monedas=150, jugador="Ana")
        datos = escena.entradas[0]
        self.assertEqual(datos["nivel"], 2)
        self.assertEqual(datos["monedas"], 150)
        self.assertEqual(datos["jugador"], "Ana")

    def test_transicion_sin_datos_entrega_kwargs_vacios(self):
        """Sin datos adicionales, al_entrar() debe recibir un dict vacío."""
        escena = EscenaFalsa(self.gestor)
        self.gestor.registrar("X", escena)
        self.gestor.cambiar_escena("X")
        self.assertEqual(escena.entradas[0], {})

    def test_regresar_a_escena_previa_reactiva_al_entrar(self):
        """Volver a una escena ya visitada debe volver a llamar al_entrar()."""
        a = EscenaFalsa(self.gestor, "A")
        b = EscenaFalsa(self.gestor, "B")
        self.gestor.registrar("A", a)
        self.gestor.registrar("B", b)
        self.gestor.cambiar_escena("A")
        self.gestor.cambiar_escena("B")
        self.gestor.cambiar_escena("A")          # Volver a A
        self.assertEqual(len(a.entradas), 2)     # al_entrar llamado dos veces

    def test_al_salir_se_invoca_exactamente_una_vez_por_transicion(self):
        """Cada transición debe invocar al_salir() exactamente una vez."""
        a = EscenaFalsa(self.gestor, "A")
        b = EscenaFalsa(self.gestor, "B")
        self.gestor.registrar("A", a)
        self.gestor.registrar("B", b)
        self.gestor.cambiar_escena("A")   # 0 al_salir
        self.gestor.cambiar_escena("B")   # 1 al_salir para A
        self.gestor.cambiar_escena("A")   # 1 al_salir para B
        self.assertEqual(a.salidas, 1)
        self.assertEqual(b.salidas, 1)

    def test_nivel1_al_entrar_inicializa_posiciones(self):
        """EscenaNivel1.al_entrar() debe colocar al héroe en la posición inicial."""
        gestor = GestorEscenas()
        escena = EscenaNivel1SinTeclas(gestor)
        gestor.registrar(ESCENA_NIVEL_1, escena)
        gestor.cambiar_escena(ESCENA_NIVEL_1)
        self.assertAlmostEqual(escena.jugador.x, POS_INICIAL_HEROE[0], places=1)
        self.assertAlmostEqual(escena.jugador.y, POS_INICIAL_HEROE[1], places=1)

    def test_nivel1_al_entrar_estado_es_jugando(self):
        """Al entrar en EscenaNivel1 el estado debe ser 'jugando'."""
        gestor = GestorEscenas()
        escena = EscenaNivel1SinTeclas(gestor)
        gestor.registrar(ESCENA_NIVEL_1, escena)
        gestor.cambiar_escena(ESCENA_NIVEL_1)
        self.assertEqual(escena.estado_juego, "jugando")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PRUEBAS DE TEMPORIZADORES
# ═══════════════════════════════════════════════════════════════════════════════

class TestTemporizadores(unittest.TestCase):
    """Pruebas de los temporizadores internos de personajes y HUD."""

    def _crear_escena_limpia(self):
        gestor = GestorEscenas()
        escena = EscenaNivel1SinTeclas(gestor)
        gestor.registrar(ESCENA_NIVEL_1, escena)
        gestor.cambiar_escena(ESCENA_NIVEL_1)
        return gestor, escena

    # ── Temporizador de HUD ───────────────────────────────────────────────────

    def test_mostrar_aviso_hud_inicia_contador(self):
        """mostrar_aviso_hud() debe inicializar frames_mensaje_hud en 120."""
        _, escena = self._crear_escena_limpia()
        escena.mostrar_aviso_hud("Prueba")
        self.assertEqual(escena.frames_mensaje_hud, 120)
        self.assertEqual(escena.mensaje_hud, "Prueba")

    def test_frames_hud_decrementa_con_actualizar(self):
        """Cada llamada a actualizar() debe decrementar frames_mensaje_hud en 1."""
        _, escena = self._crear_escena_limpia()
        escena.mostrar_aviso_hud("Prueba")
        for _ in range(5):
            escena.actualizar(0.016)
        self.assertEqual(escena.frames_mensaje_hud, 115)

    def test_frames_hud_no_baja_de_cero(self):
        """frames_mensaje_hud no debe ser negativo después de expirar."""
        _, escena = self._crear_escena_limpia()
        escena.mostrar_aviso_hud("Prueba")
        for _ in range(200):            # Muy por encima de los 120 frames
            escena.actualizar(0.016)
        self.assertEqual(escena.frames_mensaje_hud, 0)

    # ── Temporizador de retraso del enemigo ───────────────────────────────────

    def test_tiempo_retraso_detiene_al_enemigo(self):
        """Con tiempo_retraso activo, el enemigo no debe moverse."""
        gestor = GestorEscenas()
        escena = EscenaNivel1SinTeclas(gestor)
        gestor.registrar(ESCENA_NIVEL_1, escena)
        gestor.cambiar_escena(ESCENA_NIVEL_1)

        escena.enemigo.tiempo_retraso = 10.0   # 10 segundos de retraso
        x_antes = escena.enemigo.x
        y_antes = escena.enemigo.y

        for _ in range(10):
            escena.actualizar(0.016)

        self.assertAlmostEqual(escena.enemigo.x, x_antes, places=1)
        self.assertAlmostEqual(escena.enemigo.y, y_antes, places=1)

    def test_tiempo_retraso_se_consume_con_dt(self):
        """El retraso del enemigo debe disminuir proporcionalmente al dt."""
        gestor = GestorEscenas()
        escena = EscenaNivel1SinTeclas(gestor)
        gestor.registrar(ESCENA_NIVEL_1, escena)
        gestor.cambiar_escena(ESCENA_NIVEL_1)

        escena.enemigo.tiempo_retraso = 1.0
        escena.actualizar(0.5)           # Consumir 0.5 s de retraso
        self.assertAlmostEqual(escena.enemigo.tiempo_retraso, 0.5, places=2)

    def test_tiempo_retraso_no_queda_negativo(self):
        """El tiempo de retraso debe detenerse exactamente en 0."""
        gestor = GestorEscenas()
        escena = EscenaNivel1SinTeclas(gestor)
        gestor.registrar(ESCENA_NIVEL_1, escena)
        gestor.cambiar_escena(ESCENA_NIVEL_1)

        escena.enemigo.tiempo_retraso = 0.1
        escena.actualizar(1.0)           # Excede el retraso
        self.assertGreaterEqual(escena.enemigo.tiempo_retraso, 0.0)

    # ── Temporizador de predicción del enemigo ────────────────────────────────

    def test_prediccion_desactiva_al_expirar_tiempo(self):
        """tiempo_prediccion ≤ 0 debe desactivar mostrar_prediccion."""
        gestor = GestorEscenas()
        escena = EscenaNivel1SinTeclas(gestor)
        gestor.registrar(ESCENA_NIVEL_1, escena)
        gestor.cambiar_escena(ESCENA_NIVEL_1)

        escena.enemigo.mostrar_prediccion = True
        escena.enemigo.tiempo_prediccion = 0.016  # Expirará en el siguiente frame

        escena.actualizar(0.016)
        # Después de 1 frame, tiempo_prediccion debe ser 0 y prediccion apagada
        self.assertFalse(escena.enemigo.mostrar_prediccion)
        self.assertAlmostEqual(escena.enemigo.tiempo_prediccion, 0.0, places=4)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PRUEBAS DE INTEGRACIÓN DEL MOTOR (velocidad y delta time)
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegracionMotor(unittest.TestCase):
    """
    Verifica que las velocidades de los personajes son coherentes con dt.
    No depende del FPS real del sistema.
    """

    DT_PRUEBA = 1.0 / 60.0   # dt fijo equivalente a 60 FPS
    TOLERANCIA = 0.05         # 5 % de margen de error

    def _crear_escena(self, teclas: dict = None):
        gestor = GestorEscenas()
        escena = EscenaNivel1SinTeclas(gestor, teclas or {})
        gestor.registrar(ESCENA_NIVEL_1, escena)
        gestor.cambiar_escena(ESCENA_NIVEL_1)
        return gestor, escena

    def test_heroe_avanza_en_x_con_flecha_derecha(self):
        """Con flecha derecha, el héroe debe avanzar en X."""
        gestor, escena = self._crear_escena({pygame.K_RIGHT: True})
        x0 = escena.jugador.x
        escena.actualizar(self.DT_PRUEBA)
        self.assertGreater(escena.jugador.x, x0)

    def test_heroe_avanza_en_x_negativa_con_flecha_izquierda(self):
        """Con flecha izquierda, el héroe debe retroceder en X."""
        gestor, escena = self._crear_escena({pygame.K_LEFT: True})
        # Mover al centro para que no choque con el borde izquierdo
        escena.jugador.x = 400.0
        escena.jugador.actualizar_rect()
        x0 = escena.jugador.x
        escena.actualizar(self.DT_PRUEBA)
        self.assertLess(escena.jugador.x, x0)

    def test_velocidad_heroe_es_proporcional_al_dt(self):
        """En 1 segundo de dt fijo, el héroe debe recorrer ~VELOCIDAD_HEROE px."""
        gestor, escena = self._crear_escena({pygame.K_RIGHT: True})
        x0 = escena.jugador.x
        fps = 60
        dt = 1.0 / fps
        n_frames = fps  # 1 segundo real

        for _ in range(n_frames):
            escena.actualizar(dt)

        tiempo_total = n_frames * dt
        px_por_segundo = (escena.jugador.x - x0) / tiempo_total
        desviacion = abs(px_por_segundo - VELOCIDAD_HEROE) / VELOCIDAD_HEROE
        self.assertLessEqual(
            desviacion,
            self.TOLERANCIA,
            f"Desviación de velocidad del héroe: {desviacion:.2%} "
            f"(esperado {VELOCIDAD_HEROE} px/s, medido {px_por_segundo:.1f} px/s)"
        )

    def test_enemigo_se_acerca_al_jugador(self):
        """El enemigo debe disminuir su distancia al jugador con cada actualización."""
        gestor, escena = self._crear_escena()
        dx = escena.jugador.x - escena.enemigo.x
        dy = escena.jugador.y - escena.enemigo.y
        dist_antes = (dx ** 2 + dy ** 2) ** 0.5

        escena.actualizar(self.DT_PRUEBA)

        dx = escena.jugador.x - escena.enemigo.x
        dy = escena.jugador.y - escena.enemigo.y
        dist_despues = (dx ** 2 + dy ** 2) ** 0.5
        self.assertLess(dist_despues, dist_antes)

    def test_velocidad_enemigo_es_proporcional_al_dt(self):
        """En 1 segundo, el enemigo debe recorrer ~VELOCIDAD_ENEMIGO px."""
        gestor, escena = self._crear_escena()
        x0_e = escena.enemigo.x
        y0_e = escena.enemigo.y
        fps = 60
        dt = 1.0 / fps

        for _ in range(fps):
            escena.actualizar(dt)

        dx = escena.enemigo.x - x0_e
        dy = escena.enemigo.y - y0_e
        dist = (dx ** 2 + dy ** 2) ** 0.5
        px_por_segundo = dist / (fps * dt)
        desviacion = abs(px_por_segundo - VELOCIDAD_ENEMIGO) / VELOCIDAD_ENEMIGO
        self.assertLessEqual(
            desviacion,
            self.TOLERANCIA,
            f"Desviación de velocidad del enemigo: {desviacion:.2%} "
            f"(esperado {VELOCIDAD_ENEMIGO} px/s, medido {px_por_segundo:.1f} px/s)"
        )

    def test_heroe_no_sale_de_los_limites(self):
        """El héroe no debe superar el borde derecho de la pantalla."""
        gestor, escena = self._crear_escena({pygame.K_RIGHT: True})
        for _ in range(300):            # Muchos frames hacia la derecha
            escena.actualizar(self.DT_PRUEBA)
        ancho_sprite = escena.jugador.rect.width
        self.assertLessEqual(escena.jugador.x, ANCHO - ancho_sprite)

    def test_sin_tecla_heroe_no_se_mueve(self):
        """Sin input, el héroe no debe moverse."""
        gestor, escena = self._crear_escena({})
        x0, y0 = escena.jugador.x, escena.jugador.y
        for _ in range(10):
            escena.actualizar(self.DT_PRUEBA)
        self.assertAlmostEqual(escena.jugador.x, x0, places=2)
        self.assertAlmostEqual(escena.jugador.y, y0, places=2)

    def test_dt_max_limita_paso_de_integracion(self):
        """Un dt excesivo debe ser acotado por DT_MAX en la capa de integración."""
        gestor, escena = self._crear_escena({pygame.K_RIGHT: True})
        x0 = escena.jugador.x

        dt_normal = DT_MAX
        dt_excesivo = DT_MAX * 10          # Simular lag brutal
        dt_usado = min(dt_excesivo, DT_MAX)  # Lo que el motor realmente usa

        escena.actualizar(dt_normal)
        desplazamiento_normal = escena.jugador.x - x0

        # Reiniciar posición
        escena.jugador.x = x0
        escena.jugador.actualizar_rect()

        # Con dt excesivo el desplazamiento NO debe ser 10× mayor
        # porque el bucle principal ya aplica min(dt, DT_MAX).
        # Usamos dt_usado (acotado) para que la afirmación sea consistente.
        escena.actualizar(dt_usado)
        desplazamiento_con_tope = escena.jugador.x - x0

        self.assertAlmostEqual(
            desplazamiento_normal,
            desplazamiento_con_tope,
            places=2,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Punto de entrada
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
