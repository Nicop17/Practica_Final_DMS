import pytest
import sys
import os

# --- PREPARACIÓN DEL ENTORNO ---
# Aseguramos que la raíz del proyecto esté en el path para la correcta
# localización de los módulos de métricas.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.lines import LinesStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.lines'. Verifique la estructura de paquetes.")

# --- BATERÍA DE PRUEBAS DE CALIDAD ---

class TestLinesStrategyAudit:
    """
    Suite de validación para LinesStrategy.
    
    Garantiza que el conteo de líneas de código sea preciso, eficiente y 
    seguro ante entradas inesperadas o volúmenes masivos de datos.
    """

    @pytest.fixture
    def strategy(self):
        return LinesStrategy()

    # 1. VALIDACIÓN DE FUNCIONAMIENTO BÁSICO
    def test_basic_compliance(self, strategy):
        """
        Verifica que la estrategia realice un conteo exacto en casos estándar.
        Garantiza que una línea de código simple sea contabilizada correctamente.
        """
        assert strategy.compute("print('hello')") == 1

    # 2. VALIDACIÓN DE SEGURIDAD ANTE NULOS
    def test_fail_gracefully_on_none(self, strategy):
        """
        Verifica el manejo de excepciones ante entradas nulas (None).
        Asegura que el sistema realice una validación de tipo previa y lance
        un TypeError descriptivo, evitando fallos de atributo internos.
        """
        with pytest.raises((TypeError, ValueError), match="Debe ser string"):
            strategy.compute(None)

    # 3. VALIDACIÓN DE TIPADO (Type Guards)
    @pytest.mark.parametrize("garbage_input", [
        100,                 # int
        ["linea1"],          # list
        b"archivo binario", # bytes
        {"k": "v"}          # dict
    ])
    def test_input_type_validation(self, strategy, garbage_input):
        """
        Valida la integridad del sistema ante tipos de datos no soportados.
        Confirma la existencia de 'Type Guards' que protegen la lógica de negocio
        frente a entradas que no sean cadenas de texto.
        """
        with pytest.raises(TypeError):
            strategy.compute(garbage_input)

    # 4. VALIDACIÓN DE CASOS LÍMITE (Lógica de Negocio)
    @pytest.mark.parametrize("content, expected_lines", [
        ("", 0),             # Archivo vacío
        ("\n", 0),           # Salto de línea solitario (no se considera línea de código)
        ("   ", 0),          # Líneas compuestas solo por espacios (no se consideran código)
        ("# solo comentario", 1) # Líneas de comentario (se consideran líneas físicas)
    ])
    def test_business_logic_edge_cases(self, strategy, content, expected_lines):
        """
        Evalúa la consistencia de la métrica en casos de borde.
        Define qué elementos se consideran 'líneas' para el reporte final, 
        asegurando criterios uniformes en el análisis.
        """
        assert strategy.compute(content) == expected_lines

    # 5. VALIDACIÓN DE EFICIENCIA Y ESCALABILIDAD
    @pytest.mark.slow
    def test_memory_stress_large_input(self, strategy):
        """
        Prueba de rendimiento ante volúmenes masivos de datos.
        Asegura que el procesamiento de archivos de gran tamaño (ej. logs de 1M de líneas)
        se realice de forma estable, sin provocar desbordamientos de memoria 
        o degradación crítica del rendimiento.
        """
        # Generamos un entorno sintético de 1 millón de líneas.
        massive_input = "a\n" * 1_000_000 
        
        try:
            result = strategy.compute(massive_input)
            assert result == 1_000_000
        except MemoryError:
            pytest.fail("ERROR DE ESCALABILIDAD: El sistema no gestionó eficientemente la memoria.")
        except Exception as e:
            pytest.fail(f"FALLO DE SISTEMA: El análisis de gran volumen colapsó: {e}")