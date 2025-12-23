import pytest
import sys
import os

# Configuración del path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.imports import NumImportsStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.imports'.")

class TestImportsStrategyAudit:
    """
    Auditoría de imports.py.
    
    Vectores de Ataque:
    1. Falsos Positivos en Docstrings y Strings Multilínea.
    2. Imports anidados (indentación).
    3. Falsos imports comentados (aunque el .strip() ayuda, verificaremos).
    """

    @pytest.fixture
    def strategy(self):
        return NumImportsStrategy()

    # --------------------------------------------------------------------------
    # 1. PRUEBA DE CONFORMIDAD (Happy Path)
    # --------------------------------------------------------------------------
    def test_basic_import_counting(self, strategy):
        """
        Verifica que cuente imports normales.
        """
        code = """
import os
import sys
from pathlib import Path
x = 1
"""
        assert strategy.compute(code) == 3

    # --------------------------------------------------------------------------
    # 2. PRUEBA DE FALSOS POSITIVOS (El talón de Aquiles)
    # --------------------------------------------------------------------------
    def test_ignore_imports_inside_strings_and_docstrings(self, strategy):
        """
        ATACAMOS: Código fuente dentro de strings.
        FALLO ACTUAL: La estrategia lee línea a línea sin contexto.
        RESULTADO ESPERADO: 0 imports (porque son texto, no código).
        RESULTADO REAL (BUG): Contará imports dentro de los strings.
        """
        code = '''
def help():
    """
    Uso:
    import os  <-- Esto NO es un import
    from sys import version <-- Esto TAMPOCO
    """
    msg = """
    ATENCION:
    import shutil <-- Falso positivo
    """
    return msg
'''
        # El código actual verá las líneas dentro de las comillas, hará strip(),
        # verá que empiezan por "import " y sumará.
        # Esperamos 0 imports reales.
        
        count = strategy.compute(code)
        
        assert count == 0, \
            f"FALLO DE CONTEXTO: Se detectaron {count} imports dentro de cadenas de texto/docstrings. " \
            "Se debe usar AST, no string parsing."

    # --------------------------------------------------------------------------
    # 3. PRUEBA DE INDENTACIÓN (Scope Local)
    # --------------------------------------------------------------------------
    def test_local_scope_imports(self, strategy):
        """
        Verifica imports dentro de funciones (indentados).
        El uso de .strip() debería salvar este caso, pero comprobamos.
        """
        code = """
def func():
    import json  # Indentado
    if True:
        from datetime import datetime # Más indentado
"""
        assert strategy.compute(code) == 2

    # --------------------------------------------------------------------------
    # 4. PRUEBA DE ROBUSTEZ (Imports inválidos pero textuales)
    # --------------------------------------------------------------------------
    def test_invalid_syntax_handling(self, strategy):
        """
        ATACAMOS: Líneas que parecen imports pero son sintaxis inválida.
        Si usamos string parsing, esto cuenta. Si usamos AST, esto explota o se ignora.
        """
        # Esto empieza por "import " pero no es válido en Python
        code = "import 1234_invalid_module" 
        
        # Un parser textual contará 1. Un parser AST lanzará SyntaxError o lo ignorará.
        # Si queremos ser estrictos, una herramienta de métricas debería validar sintaxis.
        # Si el objetivo es solo contar "declaraciones", aceptamos 1, 
        # pero es bueno saber que cuenta basura.
        assert strategy.compute(code) == 1

    # --------------------------------------------------------------------------
    # 5. PRUEBA DE TIPOS
    # --------------------------------------------------------------------------
    def test_crash_on_none(self, strategy):
        with pytest.raises((ValueError, AttributeError, TypeError)):
            strategy.compute(None)
