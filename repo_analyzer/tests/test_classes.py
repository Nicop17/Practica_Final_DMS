import pytest
import sys
import os
import ast

# Configuración del entorno de pruebas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.classes import ClassesStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.classes'. Verifique la estructura de carpetas.")

class TestClassesStrategyAudit:
    """
    Suite de pruebas de calidad para la estrategia de análisis de clases.
    
    Verifica que el sistema identifique correctamente la interfaz pública de las clases
    siguiendo las convenciones de nomenclatura de Python y soportando sintaxis moderna.
    """

    @pytest.fixture
    def strategy(self):
        return ClassesStrategy()

    # --------------------------------------------------------------------------
    # 1. PRUEBA DE FILTRADO DE MÉTODOS
    # --------------------------------------------------------------------------
    def test_basic_public_method_counting(self, strategy):
        """
        Valida que la estrategia diferencie métodos públicos de privados.
        - Ignora métodos 'dunder' (__init__, etc.)
        - Ignora métodos privados (que comienzan con _)
        - Cuenta únicamente métodos de la interfaz pública.
        """
        code = """
class UserManager:
    def __init__(self):         # Constructor (Ignorar)
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
    # 2. PRUEBA DE COMPATIBILIDAD ASÍNCRONA (Python 3.5+)
    # --------------------------------------------------------------------------
    def test_support_for_async_methods(self, strategy):
        """
        Verifica el soporte para programación asíncrona (Modern Python).
        Asegura que los métodos definidos con 'async def' sean detectados y
        procesados con las mismas reglas de visibilidad que los métodos síncronos.
        """
        code = """
class AsyncProcessor:
    async def connect(self):    # Público asíncrono (Contar)
        await something()
    async def _internal(self):  # Privado asíncrono (Ignorar)
        pass
    def sync_fallback(self):    # Público síncrono (Contar)
        pass
"""
        result = strategy.compute(code)
        
        # Se esperan 2 métodos: 'connect' y 'sync_fallback'
        assert result.get("AsyncProcessor") == 2, \
            "La estrategia debe reconocer métodos definidos con 'async def'."

    # --------------------------------------------------------------------------
    # 3. PRUEBA DE VALIDACIÓN Y ROBUSTEZ
    # --------------------------------------------------------------------------
    def test_crash_on_none_input(self, strategy):
        """
        Verifica la estabilidad del sistema ante entradas nulas.
        El componente debe validar el tipo de entrada y lanzar excepciones 
        controladas (TypeError/ValueError) en lugar de permitir fallos de ejecución.
        """
        with pytest.raises((ValueError, TypeError)):
             strategy.compute(None)

    # --------------------------------------------------------------------------
    # 4. PRUEBA DE DECORADORES
    # --------------------------------------------------------------------------
    def test_decorators_handling(self, strategy):
        """
        Valida que el uso de decoradores no interfiera en la detección de métodos.
        Propiedades (@property), métodos de clase (@classmethod) y métodos estáticos
        (@staticmethod) deben ser contabilizados si su nombre es público.
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
        result = strategy.compute(code)
        assert result == {"Config": 3}