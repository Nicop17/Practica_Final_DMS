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
    Suite de Pruebas TDD (Test Driven Development) para DuplicationStrategy.
    Estado: ROJO (Esperando correcciones del desarrollador).
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
    # 1. PRUEBAS DE ROBUSTEZ (CRASH TESTING)
    # --------------------------------------------------------------------------

    def test_should_handle_encoding_errors_gracefully(self, strategy, create_file):
        """
        FALLA ACTUALMENTE: Lanza UnicodeDecodeError.
        CORRECCIÓN REQUERIDA: Manejar archivos binarios o legacy (Latin-1) sin detener la ejecución.
        """
        # Simulamos un archivo binario (ej. imagen) o texto legacy
        bin_file = create_file("data.bin", b"\x80\x81\x82_binary_garbage")
        
        try:
            # Una ventana de 3 es estándar
            result = strategy.compute(bin_file, window=3)
            # Debe devolver 0.0 o similar, pero NO explotar
            assert isinstance(result, float)
        except UnicodeDecodeError:
            pytest.fail("CRÍTICO: La estrategia colapsó al leer un archivo no UTF-8.")

    def test_should_handle_missing_files(self, strategy):
        """
        FALLA ACTUALMENTE: Lanza FileNotFoundError.
        """
        with pytest.raises((ValueError, FileNotFoundError)):
            # Dependiendo de la política, puede relanzar error controlado o devolver 0.0
            # Pero el código actual lanza la excepción cruda del sistema operativo.
            # Asumiremos que queremos robustez:
            try:
                strategy.compute(Path("ghost_file.py"), window=3)
            except FileNotFoundError:
                pytest.fail("Excepción de sistema no controlada (FileNotFoundError).")

    # --------------------------------------------------------------------------
    # 2. PRUEBAS DE LÓGICA DE NORMALIZACIÓN (THE LOGIC KILLERS)
    # --------------------------------------------------------------------------

    def test_should_not_strip_hashes_inside_strings(self, strategy, create_file):
        """
        FALLA ACTUALMENTE: El código hace split('#') ciegamente.
        BUG: Transforma 'x = "#fff"' en 'x = "'.
        IMPACTO: Cambia el hash del código válido, rompiendo la detección de duplicados real.
        """
        code_with_hash = """
def hex_color():
    return "#FFFFFF"  # Este comentario sí debe irse, pero el string no.
"""
        # El código actual dejará: return "
        # Esperamos que el normalizador sea lo bastante listo para distinguir strings de comentarios.
        # Si esto es muy difícil de parsear sin librerías complejas, al menos documentar el fallo.
        # Pero como QA, exijo que el código funcional no se rompa.
        
        f = create_file("colors.py", code_with_hash)
        
        # Para verificar esto indirectamente sin acceder a funciones privadas,
        # creamos dos archivos que SOLO difieren en el contenido del string tras el #.
        # Si el normalizador corta todo tras el #, los verá como duplicados (1.0).
        # Si funciona bien, los verá diferentes (0.0).
        
        code_a = 'x = "#AAAAAA"'
        code_b = 'x = "#BBBBBB"'
        
        # Si el código corta en #, ambos quedan como 'x = "', ergo son idénticos.
        # Truco: Usamos la función compute interna o verificamos comportamiento.
        # Dado que no podemos acceder fácil al normalizador interno desde aquí sin importar,
        # usaremos un caso de prueba de "Falso Positivo".
        
        # Inyectamos el bug:
        from metrics.duplication import normalize_to_lines
        
        lines = normalize_to_lines('x = "#123"', remove_comments=True)
        # El código actual devuelve ['x = "']
        assert 'x = "#123"' in lines[0], \
            f"BUG CRÍTICO: El normalizador destruyó el string que contenía un '#'. Resultado: {lines}"

    def test_async_def_handling(self, strategy, create_file):
        """
        FALLA ACTUALMENTE: Solo elimina 'def ' y 'class '.
        CORRECCIÓN: Debe eliminar también 'async def '.
        """
        # Si normalizamos, las cabeceras se van.
        # Archivo 1: Función síncrona
        # Archivo 2: Función asíncrona con mismo cuerpo
        # Si la cabecera se ignora correctamente, deberían ser duplicados (100%).
        
        from metrics.duplication import normalize_to_lines
        
        source = "async def my_process():\n    pass"
        lines = normalize_to_lines(source, remove_def_class_header=True)
        
        # Si 'async def' no se elimina, aparecerá en lines.
        # Si se elimina correctamente (como 'def'), lines debería estar vacío o solo tener 'pass'.
        assert not any("async" in line for line in lines), \
            "El normalizador ignora las definiciones 'async def', afectando al ratio de duplicación."

    # --------------------------------------------------------------------------
    # 3. PRUEBAS MATEMÁTICAS Y DE VENTANA
    # --------------------------------------------------------------------------

    def test_window_larger_than_file(self, strategy, create_file):
        """
        Verifica comportamiento cuando la ventana es mayor que el nº de líneas.
        Debe devolver 0.0, no error.
        """
        f = create_file("short.py", "print(1)\nprint(2)")
        result = strategy.compute(f, window=5)
        assert result == 0.0

    def test_exact_duplication(self, strategy, create_file):
        """
        Prueba de control positivo.
        Archivo: A, B, A, B. Window: 2.
        Shingles: [A,B], [B,A], [A,B].
        Total shingles: 3.
        Duplicados: [A,B] aparece 2 veces.
        Cálculo esperado: El código actual suma todas las ocurrencias duplicadas.
        Duplicates count: 2 (del primer [A,B] y del último [A,B]).
        Ratio: 2/3 = 0.666...
        """
        content = "lineA\nlineB\nlineA\nlineB"
        f = create_file("dup.py", content)
        
        result = strategy.compute(f, window=2)
        assert abs(result - 0.666) < 0.01
