import pytest
import sys
import os
import ast

# Configuración del path para la importación del módulo de métricas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.functions import FunctionsStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.functions'.")

class TestFunctionsStrategyAudit:
    """
    Suite de validación para FunctionsStrategy.
    
    Verifica la precisión de las métricas extraídas a nivel de función:
    - Conteo de parámetros (diferenciando funciones de métodos).
    - Profundidad de anidamiento (Nesting Depth).
    - Líneas de código (LOC) por función.
    - Complejidad Ciclomática (CC).
    """

    @pytest.fixture
    def strategy(self):
        return FunctionsStrategy()

    # --------------------------------------------------------------------------
    # 1. VALIDACIÓN DE PARÁMETROS (Contexto de Métodos)
    # --------------------------------------------------------------------------
    def test_method_parameter_counting(self, strategy):
        """
        Comprueba que el conteo de parámetros identifique correctamente los métodos.
        Asegura que en contextos de clase, los parámetros implícitos como 'self' 
        o 'cls' sean ignorados para reflejar únicamente la firma real de la función
        desde el punto de vista del usuario de la API.
        """
        code = """
class User:
    def update(self, data, force=False):
        pass
"""
        # Se esperan 2 parámetros: 'data' y 'force'. 'self' es omitido.
        results = strategy.compute(code)
        metrics = results.get("update")
        
        assert metrics is not None, "No se encontró la función 'update' en el análisis."
        assert metrics["params"] == 2, \
            f"Error: Se detectaron {metrics['params']} parámetros. Debe ignorar 'self'."

    # --------------------------------------------------------------------------
    # 2. VALIDACIÓN DE ANIDAMIENTO (Nesting Depth)
    # --------------------------------------------------------------------------
    def test_max_nesting_calculation(self, strategy):
        """
        Verifica el cálculo de la profundidad máxima de anidamiento.
        Valida que el analizador recorra el árbol AST e identifique correctamente
        el nivel de profundidad de estructuras como 'if', 'for' y bloques 'try',
        que impactan en la legibilidad del código.
        """
        code = """
def deep_function():
    if True:                # Nivel 1
        for x in range(10): # Nivel 2
            try:            # Nivel 3
                pass
            except:
                pass
"""
        results = strategy.compute(code)
        nesting = results["deep_function"]["max_nesting"]
        
        # El nivel más profundo alcanzado es el bloque 'try' (3).
        assert nesting == 3, f"Cálculo de anidamiento incorrecto. Esperado: 3, Obtenido: {nesting}"

    # --------------------------------------------------------------------------
    # 3. VALIDACIÓN DE LOC (Líneas de Código)
    # --------------------------------------------------------------------------
    def test_loc_calculation(self, strategy):
        """
        Verifica la precisión del cálculo de Líneas de Código (LOC) por función.
        Asegura que el rango calculado cubra desde la definición de la cabecera
        hasta el final del cuerpo de la función, permitiendo identificar
        bloques de código excesivamente largos.
        """
        code = """
def my_func():
    # linea 1
    # linea 2
    return True
"""
        results = strategy.compute(code)
        loc = results["my_func"]["loc"]
        
        # La función abarca 4 líneas físicas según el parseo del AST en este bloque.
        assert loc == 4, f"Error en cálculo de LOC. Obtenido: {loc}"