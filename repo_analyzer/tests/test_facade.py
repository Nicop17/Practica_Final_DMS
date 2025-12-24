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
    Suite de Pruebas de Integración para MetricsFacade.
    
    Verifica que la fachada coordine correctamente las diferentes estrategias de métricas,
    gestione el ciclo de vida de los datos y mantenga la estabilidad ante fallos externos
    o estructuras de repositorio inusuales.
    """

    @pytest.fixture
    def mock_strategies(self):
        """
        Aísla la Fachada mediante el uso de Mocks para todas las estrategias internas.
        Permite validar la lógica de orquestación y agregación de resultados sin
        depender de la implementación específica de cada métrica.
        """
        with patch("metrics.facade.LinesStrategy") as MockLines, \
             patch("metrics.facade.NumImportsStrategy") as MockImports, \
             patch("metrics.facade.FunctionsStrategy") as MockFunctions, \
             patch("metrics.facade.DuplicationStrategy") as MockDuplication, \
             patch("metrics.facade.MaintainabilityStrategy") as MockMaintainability, \
             patch("metrics.facade.TodosStrategy") as MockTodos, \
             patch("metrics.facade.ClassesStrategy") as MockClasses:
            
            # Configuración de respuestas controladas para validar el flujo de datos
            instance_funcs = MockFunctions.return_value
            instance_funcs.compute.return_value = {} 
            
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
        """Crea una estructura de repositorio controlada para pruebas de descubrimiento."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / ".git").mkdir()
        
        # Archivos que deben ser detectados
        (tmp_path / "src" / "main.py").write_text("print('main')")
        (tmp_path / "utils.py").write_text("print('utils')")
        
        # Archivos que deben ser ignorados por convención
        (tmp_path / "tests" / "test_main.py").write_text("print('test')")
        (tmp_path / ".git" / "config.py").write_text("config")
        
        return tmp_path

    # --------------------------------------------------------------------------
    # 1. PRUEBA DE ORQUESTACIÓN Y SCOPE
    # --------------------------------------------------------------------------
    def test_crash_on_undefined_variable(self, mock_strategies, repo_structure):
        """
        Valida la integridad de la orquestación en el método compute_all.
        Asegura que todas las variables de contexto (como el código fuente)
        estén correctamente inicializadas y asignadas antes de la agregación
        de resultados en el resumen final.
        """
        facade = MetricsFacade()
        
        try:
            # Ejecución del flujo principal de análisis
            facade.compute_all(repo_structure, options={})
        except (UnboundLocalError, NameError):
            pytest.fail("ERROR DE SCOPE: Existe una variable usada antes de ser asignada en la lógica de agregación.")
        except Exception as e:
            pytest.fail(f"ERROR DE INTEGRACIÓN: El flujo de análisis falló por una causa no controlada: {e}")

    # --------------------------------------------------------------------------
    # 2. PRUEBA DE LÓGICA DE DESCUBRIMIENTO
    # --------------------------------------------------------------------------
    def test_ignore_directories_logic(self, repo_structure):
        """
        Verifica el algoritmo de descubrimiento de archivos (list_py_files).
        Garantiza que el sistema filtre correctamente carpetas de metadatos (.git)
        y carpetas de pruebas (tests), cumpliendo con el estándar de analizar
        únicamente el código fuente de producción.
        """
        files = list_py_files(repo_structure)
        file_names = [f.name for f in files]
        
        assert "main.py" in file_names
        assert "utils.py" in file_names
        assert "test_main.py" not in file_names, "El filtro de archivos incluyó la carpeta de tests."
        assert "config.py" not in file_names, "El filtro de archivos incluyó carpetas ocultas/metadatos."

    # --------------------------------------------------------------------------
    # 3. PRUEBA DE RESILIENCIA (Manejo de Errores Parciales)
    # --------------------------------------------------------------------------
    def test_resilience_partial_failure(self, mock_strategies, repo_structure):
        """
        Valida la capacidad del sistema para recuperarse de errores de E/S.
        Asegura que si un archivo individual no puede procesarse (por ejemplo,
        falta de permisos), el análisis continúe con el resto de los archivos
        en lugar de detener la ejecución global.
        """
        toxic_file = repo_structure / "toxic.py"
        toxic_file.write_text("secret")
        try:
            toxic_file.chmod(0o000) # Simulación de error de permisos
        except PermissionError:
            pytest.skip("Restricción de entorno: No se pueden modificar permisos de archivos.")

        facade = MetricsFacade()
        
        results = facade.compute_all(repo_structure, options={})
        
        # El resumen debe reflejar que el proceso fue exitoso para los archivos legibles
        assert results["summary"]["num_files"] >= 2, \
            "El motor de análisis falló al intentar omitir archivos ilegibles."
        
        # Cleanup
        toxic_file.chmod(0o777)

    # --------------------------------------------------------------------------
    # 4. PRUEBA DE CASOS LÍMITE (Repositorio Vacío)
    # --------------------------------------------------------------------------
    def test_empty_repo_division_by_zero(self, mock_strategies, tmp_path):
        """
        Verifica el manejo de divisiones por cero en estadísticas.
        Al analizar un directorio sin archivos Python, el sistema debe inicializar
        los promedios y contadores en 0.0 de forma segura, evitando crashes
        matemáticos en el resumen de métricas.
        """
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()
        
        facade = MetricsFacade()
        
        try:
            results = facade.compute_all(empty_repo, options={})
            assert results["summary"]["avg_cc"] == 0.0
            assert results["summary"]["maintainability_index"] == 0.0
        except ZeroDivisionError:
            pytest.fail("ERROR MATEMÁTICO: El sistema intentó dividir por cero al calcular promedios de un repo vacío.")