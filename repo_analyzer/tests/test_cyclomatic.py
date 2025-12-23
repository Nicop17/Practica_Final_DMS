import pytest
import sys
import os
import math
from pathlib import Path

# Configuración del path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.maintainability import MaintainabilityStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.maintainability'.")

class TestMaintainabilityFix:
    """
    Suite de Pruebas de Desarrollo (TDD).
    Objetivo: Estos tests fallarán hasta que el código sea robusto.
    """

    @pytest.fixture
    def strategy(self):
        return MaintainabilityStrategy()

    @pytest.fixture
    def create_file(self, tmp_path):
        def _create(name, content, encoding="utf-8"):
            p = tmp_path / name
            if isinstance(content, str):
                p.write_text(content, encoding=encoding)
            else:
                p.write_bytes(content)
            return p
        return _create

    # 1. PRUEBA DE ESTABILIDAD (Debe manejar errores de sintaxis sin explotar)
    def test_should_handle_syntax_errors_gracefully(self, strategy, create_file):
        """
        FALLA ACTUALMENTE: Lanza SyntaxError.
        CORRECCIÓN REQUERIDA: Capturar SyntaxError y devolver un valor por defecto (ej. 0.0)
        o lanzar una excepción de dominio controlada (ej. AnalysisError).
        """
        bad_file = create_file("bad.py", "def funcion_rota(: print('error')")
        
        try:
            result = strategy.compute(bad_file)
            # Si llegamos aquí, debe ser un valor seguro, no un crash
            assert isinstance(result, (int, float))
        except SyntaxError:
            pytest.fail("El analizador explotó con un SyntaxError. Debe capturarse y manejarse.")

    # 2. PRUEBA DE ENCODING (Debe manejar archivos legacy)
    def test_should_handle_latin1_encoding(self, strategy, create_file):
        """
        FALLA ACTUALMENTE: Lanza UnicodeDecodeError.
        CORRECCIÓN REQUERIDA: Intentar leer con 'utf-8', si falla probar 'latin-1' o ignorar errores.
        """
        # Archivo con tildes en ISO-8859-1 (Latin-1)
        content_bytes = b"# C\xf3digo viejo" 
        legacy_file = create_file("legacy.py", content_bytes)
        
        try:
            result = strategy.compute(legacy_file)
            assert isinstance(result, float)
        except UnicodeDecodeError:
            pytest.fail("El analizador no soporta archivos no UTF-8 (Crash por UnicodeDecodeError).")

    # 3. PRUEBA DE LÓGICA (Debe ver código fuera de funciones)
    def test_should_detect_global_scope_complexity(self, strategy, create_file):
        """
        FALLA ACTUALMENTE: Detecta LOC=0/CC=1 en scripts planos.
        CORRECCIÓN REQUERIDA: El visitor del AST debe recorrer el módulo, no solo FunctionDef.
        """
        # Script espagueti con mucha complejidad pero sin funciones
        complex_script = """
import random
x = 0
# Un bucle en el scope global
for i in range(100):
    if i % 2 == 0:
        x += 1
    else:
        x -= 1
""" * 10 
        script_file = create_file("script.py", complex_script)
        
        mi = strategy.compute(script_file)
        
        # El índice de mantenibilidad debería ser bajo (< 100) porque el código es complejo.
        # Actualmente devuelve 100 (Perfecto) porque ignora el código.
        # Exigimos que detecte algo de complejidad.
        assert mi < 99.0, f"El MI es sospechosamente perfecto ({mi}). ¿Está ignorando el código global?"

    # 4. PRUEBA DE OBSOLESCENCIA (Soporte Python 3.10+)
    def test_should_support_match_case(self, strategy, create_file):
        """
        FALLA ACTUALMENTE: match/case cuenta como complejidad 0.
        CORRECCIÓN REQUERIDA: Añadir ast.Match a la lista de nodos complejos.
        """
        modern_code = """
def router(status):
    match status:
        case 200: return "OK"
        case 400: return "Bad"
        case 404: return "Not Found"
        case 500: return "Error"
"""
        file_path = create_file("modern.py", modern_code)
        
        # Calculamos MI. Con 4 ramas, la complejidad debería bajar el MI.
        # Si ignora el match, el MI será alto.
        mi = strategy.compute(file_path)
        
        # Un MI de 100 significa que no vio complejidad.
        assert mi < 85.0, "El sistema ignora la complejidad de las sentencias match/case."
