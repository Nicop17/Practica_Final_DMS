import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Configuración del path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from metrics.facade import MetricsFacade, list_py_files
except ImportError:
    pytest.fail("CRÍTICO: No se puede importar 'metrics.facade'.")

class TestMetricsFacadeAudit:
    """
    Auditoría de Integración para MetricsFacade.
    
    Estado: CRÍTICO (El código contiene errores de sintaxis lógica que impiden la ejecución).
    """

    @pytest.fixture
    def mock_strategies(self):
        """
        Mockeamos TODAS las estrategias internas.
        No queremos testear si LinesStrategy funciona (ya lo hicimos),
        queremos testear si la Fachada sabe coordinarlas.
        """
        with patch("metrics.facade.LinesStrategy") as MockLines, \
             patch("metrics.facade.NumImportsStrategy") as MockImports, \
             patch("metrics.facade.FunctionsStrategy") as MockFunctions, \
             patch("metrics.facade.DuplicationStrategy") as MockDuplication, \
             patch("metrics.facade.MaintainabilityStrategy") as MockMaintainability, \
             patch("metrics.facade.TodosStrategy") as MockTodos, \
             patch("metrics.facade.ClassesStrategy") as MockClasses:
            
            # Configuramos retornos por defecto para evitar errores de tipo
            instance_funcs = MockFunctions.return_value
            instance_funcs.compute.return_value = {} # Dict vacío para funciones
            
            instance_todos = MockTodos.return_value
            instance_todos.compute.return_value = 0

            instance_lines = MockLines.return_value
            instance_lines.compute.return_value = 10
            
            yield {
                "lines": MockLines,
                "todos": MockTodos
            }

    @pytest.fixture
    def repo_structure(self, tmp_path):
        """Crea una estructura de repositorio falsa."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / ".git").mkdir()
        
        # Archivos válidos
        (tmp_path / "src" / "main.py").write_text("print('main')")
        (tmp_path / "utils.py").write_text("print('utils')")
        
        # Archivos ignorados
        (tmp_path / "tests" / "test_main.py").write_text("print('test')")
        (tmp_path / ".git" / "config.py").write_text("config")
        
        return tmp_path

    # --------------------------------------------------------------------------
    # 1. LA PRUEBA MORTAL (UnboundLocalError)
    # --------------------------------------------------------------------------
    def test_crash_on_undefined_variable(self, mock_strategies, repo_structure):
        """
        FALLO GARANTIZADO.
        El desarrollador usa 'source_code' en el diccionario 'summary' ANTES
        de entrar al bucle que define 'source_code'.
        
        Esto lanzará UnboundLocalError o NameError.
        """
        facade = MetricsFacade()
        
        # Ejecutamos el análisis
        try:
            facade.compute_all(repo_structure, options={})
        except UnboundLocalError:
            pytest.fail("CRÍTICO: Variable 'source_code' usada antes de asignación (Línea ~55). El código está roto.")
        except NameError:
            pytest.fail("CRÍTICO: Variable 'source_code' no definida en el scope del resumen.")
        except Exception as e:
            # Si explota por otra cosa, también lo reportamos
            pytest.fail(f"CRÍTICO: Excepción no controlada al iniciar compute_all: {e}")

    # --------------------------------------------------------------------------
    # 2. PRUEBA DE FILTRADO DE ARCHIVOS
    # --------------------------------------------------------------------------
    def test_ignore_directories_logic(self, repo_structure):
        """
        Verifica que list_py_files ignora correctamente .git y tests.
        """
        files = list_py_files(repo_structure)
        file_names = [f.name for f in files]
        
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "test_main.py" not in file_names, "Falló al ignorar carpeta 'tests'"
        assert "config.py" not in file_names, "Falló al ignorar carpeta '.git'"

    # --------------------------------------------------------------------------
    # 3. PRUEBA DE MANEJO DE ERRORES (Resiliencia)
    # --------------------------------------------------------------------------
    def test_resilience_partial_failure(self, mock_strategies, repo_structure):
        """
        Si un archivo no se puede leer (permisos), el análisis debe continuar
        con el resto, no detenerse.
        """
        # Creamos un archivo "tóxico" sin permisos de lectura (chmod 000)
        toxic_file = repo_structure / "toxic.py"
        toxic_file.write_text("secret")
        try:
            toxic_file.chmod(0o000) # Quitamos permisos
        except PermissionError:
            pytest.skip("No se pueden cambiar permisos en este entorno, saltando test.")

        facade = MetricsFacade()
        
        # Asumimos que el Bug #1 está arreglado para que este test corra
        # Si no lo arreglan, este test fallará por el Bug #1 antes de llegar aquí.
        try:
            results = facade.compute_all(repo_structure, options={})
            
            # Verificamos que al menos procesó los otros archivos
            assert results["summary"]["num_files"] >= 2, \
                "El análisis se detuvo por completo al encontrar un archivo corrupto/ilegible."
                
        except (UnboundLocalError, NameError):
            pytest.skip("Bloqueado por el error de variable indefinida (Bug #1).")
        finally:
            # Cleanup permisos para poder borrar el tmp folder
            toxic_file.chmod(0o777)

    # --------------------------------------------------------------------------
    # 4. PRUEBA DE MATEMÁTICAS (División por Cero)
    # --------------------------------------------------------------------------
    def test_empty_repo_division_by_zero(self, mock_strategies, tmp_path):
        """
        Repositorio vacío -> num_files = 0.
        Verifica que los promedios no lancen ZeroDivisionError.
        """
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()
        
        facade = MetricsFacade()
        
        try:
            results = facade.compute_all(empty_repo, options={})
            assert results["summary"]["avg_cc"] == 0.0
            assert results["summary"]["maintainability_index"] == 0.0
        except ZeroDivisionError:
            pytest.fail("CRÍTICO: División por cero detectada en repositorio vacío.")
        except (UnboundLocalError, NameError):
            pytest.skip("Bloqueado por el error de variable indefinida (Bug #1).")
