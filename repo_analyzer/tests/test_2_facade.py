import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Configuración del path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importamos lo que vamos a probar
from metrics.facade import MetricsFacade, list_py_files

class TestMetricsFacadeTDD:
    """
    Suite de Pruebas de Integración (TDD).
    Verifica que la Fachada coordine correctamente las estrategias, sume resultados
    y maneje errores de archivo sin detenerse.
    """

    @pytest.fixture
    def mock_strategies(self):
        """
        Mockeamos las estrategias para aislar la lógica de la fachada.
        No queremos que falle si 'lines.py' tiene un bug; queremos probar la coordinación.
        """
        with patch("metrics.facade.LinesStrategy") as MockLines, \
             patch("metrics.facade.NumImportsStrategy") as MockImports, \
             patch("metrics.facade.FunctionsStrategy") as MockFuncs, \
             patch("metrics.facade.DuplicationStrategy") as MockDup, \
             patch("metrics.facade.MaintainabilityStrategy") as MockMaint, \
             patch("metrics.facade.TodosStrategy") as MockTodos, \
             patch("metrics.facade.ClassesStrategy") as MockClasses:
            
            # Valores por defecto para simular métricas de un archivo
            MockLines.return_value.compute.return_value = 10
            MockImports.return_value.compute.return_value = 2
            MockFuncs.return_value.compute.return_value = {"func1": {"cc": 5}}
            MockDup.return_value.compute.return_value = 0.5  # 50% duplicación
            MockMaint.return_value.compute.return_value = 80.0
            MockTodos.return_value.compute.return_value = 1
            MockClasses.return_value.compute.return_value = {}
            
            yield
            
    @pytest.fixture
    def repo_structure(self, tmp_path):
        """Crea un repo temporal con estructura válida e inválida."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / ".git").mkdir()
        
        # Archivos válidos
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "utils.py").write_text("code")
        
        # Archivos que deben ser ignorados
        (tmp_path / "tests" / "test_main.py").write_text("code")
        (tmp_path / ".git" / "config.py").write_text("code")
        
        return tmp_path

    # --------------------------------------------------------------------------
    # 1. LÓGICA DE NEGOCIO (Suma y Agregación)
    # --------------------------------------------------------------------------
    def test_compute_all_aggregates_values_correctly(self, mock_strategies, repo_structure):
        """
        Verifica que la fachada sume los totales y promedie correctamente.
        Tenemos 2 archivos válidos (main.py, utils.py).
        Cada uno retorna 10 líneas, 1 todo, 80 MI.
        """
        facade = MetricsFacade()
        results = facade.compute_all(repo_structure, options={})
        
        summary = results["summary"]
        
        # Verificaciones de Conteo
        assert summary["num_files"] == 2
        assert summary["total_lines"] == 20  # 10 + 10
        assert summary["todos"] == 2         # 1 + 1
        
        # Verificaciones de Promedios
        assert summary["maintainability_index"] == 80.0
        assert summary["duplication"] == 0.5

    # --------------------------------------------------------------------------
    # 2. LÓGICA DE FILTRADO (El test antiguo de 'ignore')
    # --------------------------------------------------------------------------
    def test_list_py_files_filtering(self, repo_structure):
        """
        Verifica que se ignoran carpetas como .git y tests.
        """
        files = list_py_files(repo_structure)
        names = [f.name for f in files]
        
        assert "main.py" in names
        assert "utils.py" in names
        assert "test_main.py" not in names, "Se debería ignorar la carpeta tests"
        assert "config.py" not in names, "Se debería ignorar la carpeta .git"

    # --------------------------------------------------------------------------
    # 3. ROBUSTEZ (Divisiones por cero y archivos corruptos)
    # --------------------------------------------------------------------------
    def test_empty_repo_handling(self, mock_strategies, tmp_path):
        """Manejo de repositorio vacío sin Crash (ZeroDivisionError)."""
        empty = tmp_path / "empty"
        empty.mkdir()
        
        facade = MetricsFacade()
        results = facade.compute_all(empty, {})
        
        assert results["summary"]["num_files"] == 0
        assert results["summary"]["avg_cc"] == 0.0

    def test_resilience_to_read_errors(self, mock_strategies, repo_structure):
        """
        Si un archivo falla al leerse, el análisis debe continuar con el resto.
        """
        # Simulamos un archivo corrupto haciendo que read_text lance excepción
        # OJO: Como estamos mockeando 'Path.read_text' dentro del código es difícil sin monkeypatch.
        # En su lugar, usaremos un archivo con permisos restringidos si el OS lo permite,
        # o confiaremos en que el código tiene un try-except.
        
        toxic = repo_structure / "toxic.py"
        toxic.write_text("boom")
        
        # En Linux/Mac esto funciona para denegar lectura
        try:
            toxic.chmod(0o000)
        except:
            pytest.skip("No se pueden cambiar permisos en este OS")

        facade = MetricsFacade()
        try:
            results = facade.compute_all(repo_structure, {})
            # Debería haber procesado main.py y utils.py (2 archivos), ignorando toxic.py
            # O toxic.py cuenta como archivo pero no suma métricas.
            # Según nuestra implementación, si falla el read, hace 'continue', así que no cuenta en los resultados detallados.
            
            # Recuperamos permisos para poder borrar
            toxic.chmod(0o777)
            
            assert len(results["files"]) >= 2
        except Exception as e:
            toxic.chmod(0o777)
            pytest.fail(f"La fachada se detuvo por un archivo corrupto: {e}")
