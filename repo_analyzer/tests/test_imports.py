import pytest
import sys
import os

# Configuración del path para la importación del módulo de métricas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.imports import NumImportsStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.imports'.")

class TestImportsStrategyAudit:
    """
    Suite de validación para NumImportsStrategy.
    
    Asegura la correcta identificación de dependencias externas en el código fuente,
    validando la detección de imports en diferentes niveles de indentación,
    ámbitos locales y la estabilidad ante entradas no válidas.
    """

    @pytest.fixture
    def strategy(self):
        return NumImportsStrategy()

    # --------------------------------------------------------------------------
    # 1. VALIDACIÓN DE DECLARACIONES ESTÁNDAR
    # --------------------------------------------------------------------------
    def test_basic_import_counting(self, strategy):
        """
        Verifica la detección de declaraciones de importación estándar.
        Valida que el analizador identifique correctamente tanto el patrón 
        'import' como el patrón 'from ... import' en el ámbito global del módulo.
        """
        code = """
import os
import sys
from pathlib import Path
x = 1
"""
        assert strategy.compute(code) == 3

    # --------------------------------------------------------------------------
    # 2. VALIDACIÓN DE SCOPE LOCAL (Indentación)
    # --------------------------------------------------------------------------
    def test_local_scope_imports(self, strategy):
        """
        Valida la detección de dependencias en ámbitos locales.
        Asegura que los imports realizados dentro de funciones o estructuras
        de control (indentados) sean contabilizados correctamente, garantizando
        que la indentación no interfiera en el análisis.
        """
        code = """
def func():
    import json  # Import indentado en función
    if True:
        from datetime import datetime # Import indentado en bloque lógico
"""
        assert strategy.compute(code) == 2

    # --------------------------------------------------------------------------
    # 3. VALIDACIÓN DE PATRONES TEXTUALES
    # --------------------------------------------------------------------------
    def test_invalid_syntax_handling(self, strategy):
        """
        Verifica el comportamiento ante declaraciones con sintaxis inválida.
        Comprueba si el analizador identifica líneas que siguen el patrón de
        importación aunque el nombre del módulo no sea válido en Python, 
        evaluando la flexibilidad del parser frente a la validación estricta.
        """
        # Identifica la intención de importar un recurso aunque el nombre sea inválido
        code = "import 1234_invalid_module" 
        
        # Se verifica que el analizador reconozca la declaración de importación
        assert strategy.compute(code) == 1

    # --------------------------------------------------------------------------
    # 4. PRUEBA DE ESTABILIDAD (Robustez)
    # --------------------------------------------------------------------------
    def test_crash_on_none(self, strategy):
        """
        Garantiza la robustez del sistema ante entradas nulas (None).
        Valida que el componente gestione el error de tipo de forma segura,
        evitando fallos de ejecución inesperados mediante la validación de entrada.
        """
        with pytest.raises((ValueError, AttributeError, TypeError)):
            strategy.compute(None)