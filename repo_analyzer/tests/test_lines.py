import pytest
import sys
import os

# --- PREPARACIÓN DEL TERRENO (BOILERPLATE) ---
# Truco de QA Experto: Añadimos la raíz al path para que Python encuentre los módulos
# sin importar desde dónde lancemos el test.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.lines import LinesStrategy
except ImportError:
    # Si falla aquí, es culpa de la estructura del dev, no nuestra.
    pytest.fail("CRÍTICO: No se puede importar 'metrics.lines'. ¿Falta un __init__.py en la carpeta metrics?")

# --- INICIO DE LA BATERÍA DE PRUEBAS ---

class TestLinesStrategyAudit:

    @pytest.fixture
    def strategy(self):
        return LinesStrategy()

    # 1. PRUEBA DE HIGIENE BÁSICA (Debe pasar sí o sí)
    def test_basic_compliance(self, strategy):
        """Verifica si la clase cumple su función mínima vital."""
        assert strategy.compute("print('hello')") == 1

    # 2. PRUEBA DE ROBUSTEZ ANTE NULOS (The Null Pointer Crash)
    def test_fail_gracefully_on_none(self, strategy):
        """
        ATACAMOS: Pasamos None.
        ESPERAMOS: TypeError o ValueError (Manejo correcto).
        REALIDAD (BUG): AttributeError (Manejo sucio).
        """
        # Nota para el reporte: Si este test pasa con AttributeError, márcalo como FAIL manual
        # porque un AttributeError no es una validación aceptable en Enterprise.
        with pytest.raises((TypeError, ValueError), match="Debe ser string"):
            strategy.compute(None)

    # 3. PRUEBA DE TIPADO FUERTE
    @pytest.mark.parametrize("garbage_input", [
        100,                # int
        ["linea1"],         # list
        b"archivo binario", # bytes
        {"k": "v"}          # dict
    ])
    def test_input_type_validation(self, strategy, garbage_input):
        """
        ATACAMOS: Tipos de datos incorrectos.
        OBJETIVO: Demostrar que el método no tiene 'Type Guards'.
        """
        with pytest.raises(TypeError):
            strategy.compute(garbage_input)

    # 4. PRUEBA DE LÓGICA DE NEGOCIO (Ambigüedad)
    @pytest.mark.parametrize("content, expected_lines", [
        ("", 0),             # Archivo vacío
        ("\n", 0),           # Archivo con solo un enter (splitlines suele dar [], count=0)
        ("   ", 1),          # Espacios (¿Es código? La herramienta dice sí)
        ("# solo comentario", 1) 
    ])
    def test_business_logic_edge_cases(self, strategy, content, expected_lines):
        """Busca inconsistencias en qué se considera una 'línea'."""
        assert strategy.compute(content) == expected_lines

    # 5. EL MARTILLO: TEST DE ESTRÉS DE MEMORIA (Stress Test)
    @pytest.mark.slow
    def test_memory_stress_large_input(self, strategy):
        """
        ATACAMOS: Generamos un string sintético masivo.
        OBJETIVO: Ver si splitlines() duplica la memoria y causa un MemoryError o ralentización extrema.
        ESCENARIO: Un archivo de log de 50MB que alguien intenta analizar por error.
        """
        # Generamos 1 millón de líneas. Esto creará un string pesado.
        # Al hacer splitlines, Python crea una lista con 1 millón de objetos string.
        massive_input = "a\n" * 1_000_000 
        
        try:
            result = strategy.compute(massive_input)
            assert result == 1_000_000
        except MemoryError:
            pytest.fail("CRÍTICO: La estrategia no es eficiente en memoria (MemoryError). Usar generadores.")
        except Exception as e:
            pytest.fail(f"CRÍTICO: El sistema colapsó con input grande: {e}")
