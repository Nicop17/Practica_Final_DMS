import pytest
import sys
import os
from pathlib import Path

# Configuración del path para encontrar el módulo víctima
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.duplication import DuplicationStrategy
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.duplication'.")

class TestDuplicationFix:
    """
    Suite de Pruebas de Calidad para DuplicationStrategy.
    
    Estado: VERDE. Verifica la robustez del cálculo de duplicados mediante shingles,
    la normalización de sintaxis moderna y el manejo de errores de sistema de archivos.
    """

    @pytest.fixture
    def strategy(self):
        return DuplicationStrategy()

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

    # --------------------------------------------------------------------------
    # 1. PRUEBAS DE ROBUSTEZ Y ENCODING
    # --------------------------------------------------------------------------

    def test_should_handle_encoding_errors_gracefully(self, strategy, create_file):
        """
        Valida que la estrategia gestione correctamente archivos con errores de codificación.
        Asegura que al encontrar archivos binarios o con formatos legacy (Latin-1), 
        el sistema no colapse con un UnicodeDecodeError y retorne un valor numérico seguro.
        """
        # Simulamos un archivo binario (ej. imagen) o texto legacy
        bin_file = create_file("data.bin", b"\x80\x81\x82_binary_garbage")
        
        try:
            result = strategy.compute(bin_file, window=3)
            # Verificamos que devuelva un float (0.0 o similar) sin lanzar excepciones
            assert isinstance(result, float)
        except UnicodeDecodeError:
            pytest.fail("ERROR: El sistema no gestionó el error de codificación y lanzó UnicodeDecodeError.")

    def test_should_handle_missing_files(self, strategy):
        """
        Verifica el manejo de excepciones ante archivos inexistentes.
        Valida que el sistema identifique la ausencia del recurso y lance una 
        excepción controlada o gestionada, evitando fallos crudos de sistema.
        """
        with pytest.raises((ValueError, FileNotFoundError)):
            # El sistema debe detectar que el archivo no existe antes de intentar procesarlo
            strategy.compute(Path("ghost_file.py"), window=3)

    # --------------------------------------------------------------------------
    # 2. PRUEBAS DE NORMALIZACIÓN DE SINTAXIS
    # --------------------------------------------------------------------------
    
    def test_async_def_handling(self, strategy, create_file):
        """
        Valida el soporte para programación asíncrona en la normalización.
        Asegura que el normalizador identifique y elimine correctamente las cabeceras 
        'async def' al igual que las síncronas, permitiendo una comparación de 
        duplicados basada exclusivamente en el cuerpo de la lógica.
        """
        from metrics.duplication import normalize_to_lines
        
        source = "async def my_process():\n    pass"
        # Se activa el filtrado de cabeceras de funciones y clases
        lines = normalize_to_lines(source, remove_def_class_header=True)
        
        # El normalizador debe ser capaz de "limpiar" la palabra clave async
        assert not any("async" in line for line in lines), \
            "ERROR: El normalizador ignoró la definición 'async def'."

    # --------------------------------------------------------------------------
    # 3. PRUEBAS DE LÓGICA MATEMÁTICA (SHINGLES)
    # --------------------------------------------------------------------------

    def test_window_larger_than_file(self, strategy, create_file):
        """
        Evalúa el comportamiento del algoritmo ante ventanas de tamaño excesivo.
        Cuando el parámetro 'window' es mayor que el número total de líneas útiles 
        del archivo, el ratio de duplicación debe ser 0.0 sin generar errores de índice.
        """
        f = create_file("short.py", "print(1)\nprint(2)")
        result = strategy.compute(f, window=5)
        assert result == 0.0

    def test_exact_duplication(self, strategy, create_file):
        """
        Validación del cálculo matemático del ratio de duplicación.
        Verifica mediante un caso de control (A, B, A, B) que la técnica de 
        shingles identifique correctamente las secuencias repetidas y calcule 
        el ratio exacto (Duplicados / Total).
        """
        # Contenido diseñado para generar shingles repetidos
        content = "lineA\nlineB\nlineA\nlineB"
        f = create_file("dup.py", content)
        
        result = strategy.compute(f, window=2)
        
        # Con ventana 2, shingles: [A,B], [B,A], [A,B]. Total=3, Repetidos=2. Ratio=0.666
        assert abs(result - 0.666) < 0.01