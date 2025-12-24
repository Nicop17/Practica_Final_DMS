import pytest
import sys
import os
import math
from pathlib import Path

# Configuración del entorno de pruebas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.maintainability import MaintainabilityStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.maintainability'.")

class TestMaintainabilityFix:
    """
    Suite de Pruebas de Calidad para MaintainabilityStrategy.
    
    Verifica la robustez del cálculo del Índice de Mantenibilidad ante fallos de 
    sintaxis, codificaciones de archivos legacy y la correcta detección de 
    complejidad en scopes globales y sintaxis moderna.
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

    # 1. PRUEBA DE TOLERANCIA A FALLOS DE SINTAXIS
    def test_should_handle_syntax_errors_gracefully(self, strategy, create_file):
        """
        Valida que el analizador no se detenga ante archivos con errores de sintaxis.
        En lugar de lanzar un SyntaxError que rompa la ejecución, debe capturar el fallo
        y devolver un valor por defecto (0.0), garantizando la continuidad del análisis.
        """
        bad_file = create_file("bad.py", "def funcion_rota(: print('error')")
        
        try:
            result = strategy.compute(bad_file)
            # Verificamos que se devuelva un valor numérico seguro en lugar de explotar
            assert isinstance(result, (int, float))
        except SyntaxError:
            pytest.fail("ERROR: El analizador no capturó el SyntaxError. La ejecución se rompió.")

    # 2. PRUEBA DE COMPATIBILIDAD DE CODIFICACIÓN (Encoding)
    def test_should_handle_latin1_encoding(self, strategy, create_file):
        """
        Verifica la capacidad de procesar archivos con codificaciones distintas a UTF-8.
        Asegura que archivos legacy (codificados en Latin-1/ISO-8859-1) con caracteres
        especiales no provoquen un crash por UnicodeDecodeError.
        """
        # Archivo con tildes en ISO-8859-1 (Latin-1)
        content_bytes = b"# C\xf3digo viejo" 
        legacy_file = create_file("legacy.py", content_bytes)
        
        try:
            result = strategy.compute(legacy_file)
            assert isinstance(result, float)
        except UnicodeDecodeError:
            pytest.fail("ERROR: El analizador falló al leer un archivo no UTF-8 (UnicodeDecodeError).")

    # 3. PRUEBA DE COBERTURA DE SCOPE GLOBAL
    def test_should_detect_global_scope_complexity(self, strategy, create_file):
        """
        Valida que el cálculo de mantenibilidad incluya el código fuera de funciones.
        Asegura que el análisis del AST recorra todo el módulo, detectando la 
        complejidad ciclomática y líneas de código en scripts planos o variables globales.
        """
        # Script con lógica compleja directamente en el scope global
        complex_script = """
import random
x = 0
for i in range(100):
    if i % 2 == 0:
        x += 1
    else:
        x -= 1
""" * 10 
        script_file = create_file("script.py", complex_script)
        
        mi = strategy.compute(script_file)
        
        # Un MI inferior a 99 indica que se ha detectado la complejidad del bucle e ifs
        assert mi < 99.0, f"Aviso: El MI es {mi}. ¿Se está ignorando la complejidad global?"

    # 4. PRUEBA DE SOPORTE PARA PYTHON MODERNO (Match/Case)
    def test_should_support_match_case(self, strategy, create_file):
        """
        Verifica que el cálculo de complejidad incluya las nuevas sentencias de Python 3.10+.
        Asegura que los nodos 'match' y 'case' se contabilicen como puntos de decisión,
        afectando correctamente al Índice de Mantenibilidad final.
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
        
        mi = strategy.compute(file_path)
        
        # La presencia de 4 ramas 'case' debe reducir el índice de mantenibilidad
        assert mi < 85.0, "ERROR: El sistema no detectó la complejidad de la sentencia match/case."