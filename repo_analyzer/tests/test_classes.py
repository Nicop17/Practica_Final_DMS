import pytest
import sys
import os
import ast

# Configuración del entorno de pruebas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.classes import ClassesStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.classes'. Verifique __init__.py")

class TestClassesStrategyAudit:
    """
    Auditoría de Calidad para ClassesStrategy.
    
    Vectores de Ataque:
    1. Soporte de Modern Python (Async/Await)
    2. Integridad de Datos (Clases anidadas/Colisiones)
    3. Conformidad con Estándares (Métodos dunder/privados)
    4. Robustez (Entradas inválidas)
    """

    @pytest.fixture
    def strategy(self):
        return ClassesStrategy()

    # --------------------------------------------------------------------------
    # 1. PRUEBA DE CONFORMIDAD BÁSICA (Debe pasar)
    # --------------------------------------------------------------------------
    def test_basic_public_method_counting(self, strategy):
        """
        Verifica el filtrado básico de métodos privados y dunder.
        """
        code = """
class UserManager:
    def __init__(self):         # Dunder (Ignorar)
        pass
    def _internal_check(self):  # Privado (Ignorar)
        pass
    def get_user(self):         # Público (Contar)
        pass
    def save_user(self):        # Público (Contar)
        pass
"""
        result = strategy.compute(code)
        assert result == {"UserManager": 2}

    # --------------------------------------------------------------------------
    # 2. PRUEBA DE OBSOLESCENCIA TÉCNICA (FALLO CRÍTICO ESPERADO)
    # --------------------------------------------------------------------------
    def test_support_for_async_methods(self, strategy):
        """
        ATACAMOS: Definiciones 'async def'.
        FALLO ACTUAL: El código usa solo ast.FunctionDef, ignorando ast.AsyncFunctionDef.
        IMPACTO: APIs modernas (FastAPI/Django Async) reportarán 0 métodos.
        """
        code = """
class AsyncProcessor:
    async def connect(self):    # Público asíncrono
        await something()
    async def _internal(self):  # Privado asíncrono
        pass
    def sync_fallback(self):    # Público síncrono
        pass
"""
        result = strategy.compute(code)
        
        # El código actual probablemente devolverá 1 (solo el síncrono).
        # Esperamos 2 (connect + sync_fallback).
        assert result.get("AsyncProcessor") == 2, \
            "FALLO CRÍTICO: La estrategia es ciega a métodos asíncronos (async def)."

    # --------------------------------------------------------------------------
    # 3. PRUEBA DE INTEGRIDAD DE DATOS (Data Loss)
    # --------------------------------------------------------------------------
    def test_nested_classes_collision(self, strategy):
        """
        ATACAMOS: Clases con el mismo nombre en diferentes scopes.
        FALLO ACTUAL: El dict usa 'node.name' como clave única.
        IMPACTO: La última clase visitada sobrescribe los datos de la anterior.
        """
        code = """
class Handler:                  # Clase externa (2 métodos)
    def handle(self): pass
    def stop(self): pass

def factory():
    class Handler:              # Clase anidada (1 método)
        def run(self): pass
    return Handler
"""
        result = strategy.compute(code)
        
        # El diccionario plano no puede representar esto correctamente.
        # Opción A: Devolver nombres cualificados (Handler, factory.<locals>.Handler)
        # Opción B: Sumar métodos (incorrecto pero mejor que perder datos)
        # Opción C: Lista de resultados.
        
        # Como QA, demuestro que hay pérdida de información.
        # Si el dict tiene solo 1 entrada para "Handler", hemos perdido datos de una de las dos.
        # Verificamos si detectó AMBAS instancias o si diferenció los nombres.
        
        # Este test fallará si el sistema simplemente sobrescribe.
        # Una solución aceptable sería que las claves fueran únicas (hash o line number) o nombres completos.
        
        # Verificamos al menos que no reporte ciegamente solo la anidada (1 método) o solo la padre (2).
        # Esto es ambiguo, pero forzamos al dev a pensar en la arquitectura.
        assert len(result) > 1 or "Handler" not in result, \
            "FALLO DE ARQUITECTURA: Colisión de nombres. Una clase anidada sobrescribió a la clase principal."

    # --------------------------------------------------------------------------
    # 4. PRUEBA DE ROBUSTEZ Y TIPOS
    # --------------------------------------------------------------------------
    def test_crash_on_none_input(self, strategy):
        """
        ATACAMOS: Input None.
        ESPERAMOS: Manejo limpio, no AttributeError.
        """
        # ast.parse(None) lanza TypeError o AttributeError dependiendo de la versión.
        # El código captura SyntaxError, pero NO TypeError.
        with pytest.raises((ValueError, TypeError)):
             strategy.compute(None)

    def test_decorators_handling(self, strategy):
        """
        Verifica que los decoradores (@property, @classmethod) se cuenten como métodos.
        """
        code = """
class Config:
    @property
    def is_valid(self):
        return True
    
    @classmethod
    def load(cls):
        pass
    
    @staticmethod
    def help():
        pass
"""
        # Todos estos son FunctionDef en el AST, deberían contar como 3.
        result = strategy.compute(code)
        assert result == {"Config": 3}
