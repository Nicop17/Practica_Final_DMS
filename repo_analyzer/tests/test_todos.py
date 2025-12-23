import pytest
import sys
import os

# Configuración del path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.todos import TodosStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.todos'.")

class TestTodosStrategyAudit:
    """
    Auditoría de TodosStrategy.
    
    Vectores de Ataque:
    1. Falsos Positivos en Strings (El error más común en parsers de texto).
    2. Case Sensitivity (¿Se ignoran los 'todo' en minúsculas?).
    3. Robustez ante tipos incorrectos.
    """

    @pytest.fixture
    def strategy(self):
        return TodosStrategy()

    # --------------------------------------------------------------------------
    # 1. PRUEBA DE CONFORMIDAD (Happy Path)
    # --------------------------------------------------------------------------
    def test_basic_detection(self, strategy):
        """
        Verifica que detecte los casos obvios.
        """
        code = """
# TODO: Refactorizar esto
x = 1
y = 2  # FIXME: Esto es lento
"""
        # Esperamos 2 (uno por línea detectada)
        assert strategy.compute(code) == 2

    # --------------------------------------------------------------------------
    # 2. PRUEBA DE FALSOS POSITIVOS (Contexto de String)
    # --------------------------------------------------------------------------
    def test_ignore_todos_inside_strings(self, strategy):
        """
        ATACAMOS: 'TODO' dentro de una cadena de texto (print, variable, etc).
        FALLO ACTUAL: Busca "#" y "TODO" en la línea sin importar si es código o string.
        RESULTADO ESPERADO: 0 (No son deuda técnica, son datos).
        """
        # Caso 1: Un string que contiene un hash y la palabra TODO.
        # El parser actual verá '#' y 'TODO' en la misma línea -> +1 error.
        code_print = 'print("Error: El usuario no tiene permisos # TODO revisar logs")'
        
        # Caso 2: URL o configuración
        code_url = 'endpoint = "https://api.com/v1/#/TODOs"'

        combined_code = f"{code_print}\n{code_url}"
        
        count = strategy.compute(combined_code)
        
        assert count == 0, \
            f"FALSO POSITIVO: Se detectaron {count} TODOs dentro de strings literales. " \
            "El analizador debe distinguir entre comentarios reales y cadenas de texto."

    # --------------------------------------------------------------------------
    # 3. PRUEBA DE CASE SENSITIVITY (Regla de Negocio)
    # --------------------------------------------------------------------------
    def test_case_insensitive_detection(self, strategy):
        """
        ATACAMOS: Desarrolladores que escriben 'todo' en minúsculas.
        FALLO ACTUAL: Solo busca 'TODO' mayúsculas.
        IMPACTO: Se pierden métricas reales.
        """
        code = "# todo: arreglar esto mañana"
        
        # Generalmente, las herramientas de QA (SonarQube, etc) son case-insensitive.
        # Si devuelve 0, es técnicamente correcto según el código, pero inútil para el negocio.
        # Forzamos al dev a hacerlo robusto.
        assert strategy.compute(code) == 1, \
            "PÉRDIDA DE MÉTRICAS: No se detectan comentarios 'todo' en minúsculas."

    # --------------------------------------------------------------------------
    # 4. PRUEBA DE ROBUSTEZ (Crash Test)
    # --------------------------------------------------------------------------
    def test_crash_on_none_input(self, strategy):
        """
        ATACAMOS: Input None.
        """
        with pytest.raises((ValueError, TypeError)):
            strategy.compute(None)

    def test_no_hash_collision(self, strategy):
        """
        Verifica que no cuente TODOs si no hay hash (esto el código actual lo hace bien,
        pero es bueno asegurar que no rompan esa guardia).
        """
        code = "TODO_LIST = []"
        assert strategy.compute(code) == 0
