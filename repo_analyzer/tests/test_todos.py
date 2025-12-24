import pytest
import sys
import os

# Configuración del path para localizar el módulo de métricas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.todos import TodosStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.todos'. Verifique la estructura de paquetes.")

class TestTodosStrategyAudit:
    """
    Suite de validación para TodosStrategy.
    
    Evalúa la capacidad del analizador para identificar marcadores de deuda técnica 
    (TODO, FIXME) dentro de los comentarios, asegurando la distinción entre 
    código ejecutable, cadenas de texto y metadatos de desarrollo.
    """

    @pytest.fixture
    def strategy(self):
        return TodosStrategy()

    # --------------------------------------------------------------------------
    # 1. VALIDACIÓN DE DETECCIÓN ESTÁNDAR
    # --------------------------------------------------------------------------
    def test_basic_detection(self, strategy):
        """
        Verifica la detección de marcadores estándar en comentarios.
        Valida que el sistema identifique correctamente tanto 'TODO' como 'FIXME' 
        cuando se encuentran en líneas de comentario o comentarios de fin de línea.
        """
        code = """
# TODO: Refactorizar esto
x = 1
y = 2  # FIXME: Esto es lento
"""
        # Se esperan 2 marcadores detectados.
        assert strategy.compute(code) == 2

    # --------------------------------------------------------------------------
    # 2. VALIDACIÓN DE CONTEXTO (Evitar Falsos Positivos)
    # --------------------------------------------------------------------------
    def test_ignore_todos_inside_strings(self, strategy):
        """
        Garantiza que no se contabilicen términos dentro de literales de cadena.
        Asegura que el analizador distinga gramaticalmente entre un comentario 
        real y una cadena de texto (como un print o una URL) que contenga 
        casualmente las palabras clave o el símbolo '#'.
        """
        # Caso 1: String con hash y palabra clave
        code_print = 'print("Error: El usuario no tiene permisos # TODO revisar logs")'
        
        # Caso 2: URL con fragmento
        code_url = 'endpoint = "https://api.com/v1/#/TODOs"'

        combined_code = f"{code_print}\n{code_url}"
        
        # El resultado debe ser 0, ya que no son comentarios de desarrollador.
        count = strategy.compute(combined_code)
        
        assert count == 0, \
            f"ERROR: Se detectaron {count} falsos positivos dentro de cadenas de texto."

    # --------------------------------------------------------------------------
    # 3. VALIDACIÓN DE SENSIBILIDAD A MAYÚSCULAS (Case Insensitivity)
    # --------------------------------------------------------------------------
    def test_case_insensitive_detection(self, strategy):
        """
        Valida la detección exhaustiva sin importar el uso de mayúsculas.
        Asegura que las variaciones del marcador (ej. 'todo', 'ToDo', 'TODO') 
        sean capturadas por el sistema, garantizando métricas de deuda técnica íntegras.
        """
        code = "# todo: arreglar esto mañana"
        
        # Se verifica que el buscador sea insensible a la caja de las letras.
        assert strategy.compute(code) == 1, \
            "ERROR: La estrategia no detectó el marcador en minúsculas."

    # --------------------------------------------------------------------------
    # 4. VALIDACIÓN DE ROBUSTEZ (Input Handling)
    # --------------------------------------------------------------------------
    def test_crash_on_none_input(self, strategy):
        """
        Verifica la estabilidad del componente ante entradas nulas (None).
        Valida que el sistema realice un 'Type Check' preventivo y lance
        excepciones controladas en lugar de permitir fallos de atributo.
        """
        with pytest.raises((ValueError, TypeError)):
            strategy.compute(None)

    # --------------------------------------------------------------------------
    # 5. VALIDACIÓN DE ÁMBITO (Código vs Comentario)
    # --------------------------------------------------------------------------
    def test_no_hash_collision(self, strategy):
        """
        Asegura que las palabras clave en identificadores de código sean ignoradas.
        Verifica que el sistema solo cuente marcadores precedidos por el token 
        de comentario (#), evitando falsas alarmas en nombres de variables o listas.
        """
        code = "TODO_LIST = []"
        assert strategy.compute(code) == 0