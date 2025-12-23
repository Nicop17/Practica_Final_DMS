import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# ==============================================================================
# CONFIGURACIÓN DE ENTORNO DE PRUEBAS
# ==============================================================================

# 1. Definir la raíz del proyecto
# Estamos en repo_analyzer/tests/test_mediator.py -> Queremos llegar a repo_analyzer/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# 2. Inyectar la raíz en el path de Python (Prioridad 0)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 3. Mockear Flask GLOBALMENTE antes de cualquier import
mock_flask = MagicMock()
sys.modules["flask"] = mock_flask

# 4. Importar el módulo bajo prueba
try:
    from ui.mediator import UIMediator
except ImportError as e:
    pytest.fail(f"Error CRÍTICO de importación. Python no encuentra el módulo 'ui'. Detalles: {e}")


class TestUIMediator:
    """
    Suite de pruebas unitarias para el patrón Mediador.
    Aísla la lógica de coordinación de la interfaz web y la base de datos.
    """

    @pytest.fixture
    def mock_subject(self):
        """Mock del Subject (Lógica de Negocio / Proxy)."""
        subject = MagicMock()
        # Configuramos comportamientos por defecto
        subject.list_analyses.return_value = []
        subject.peticion.return_value = {}
        return subject

    @pytest.fixture
    def mediator(self, mock_subject):
        """Instancia del mediador inyectando el subject mockeado."""
        return UIMediator(mock_subject)

    # ==========================================================================
    # TESTS
    # ==========================================================================

    @patch("ui.mediator.render_template")
    @patch("ui.mediator.HistoryComponent")
    @patch("ui.mediator.OutputComponent")
    @patch("ui.mediator.OptionsComponent")
    @patch("ui.mediator.InputComponent")
    def test_show_index_initialization(self, MockInput, MockOpts, MockOut, MockHist, mock_render, mediator, mock_subject):
        """
        [GET /] Carga Inicial.
        Debe coordinar la obtención del historial y renderizar la vista base.
        """
        # Preparación (Arrange)
        MockHist.return_value.get_entries.return_value = {"history": ["item_test"]}

        # Ejecución (Act)
        mediator.show_index()

        # Aserción (Assert)
        MockHist.return_value.get_entries.assert_called_once_with(mock_subject)
        assert mock_render.call_args[0][0] == "index.html"
        assert mock_render.call_args[1]["history"] == ["item_test"]

    @patch("ui.mediator.render_template")
    @patch("ui.mediator.HistoryComponent")
    @patch("ui.mediator.OutputComponent")
    @patch("ui.mediator.OptionsComponent")
    @patch("ui.mediator.InputComponent")
    def test_handle_analyze_validation_failure(self, MockInput, MockOpts, MockOut, MockHist, mock_render, mediator, mock_subject):
        """
        [POST /analyze] Fallo de Validación.
        Si el InputComponent detecta error, el Subject NO debe ejecutarse.
        """
        # Preparación: Input devuelve error
        MockInput.return_value.parse.return_value = (None, "URL Inválida")
        MockInput.return_value.context.return_value = {"input_error": "URL Inválida"}
        
        form_data = {} # Formulario vacío

        # Ejecución
        mediator.handle_analyze(form_data)

        # Aserción Crítica: El negocio está protegido
        mock_subject.peticion.assert_not_called()
        
        # Aserción UI: Se muestra el error
        assert mock_render.call_args[1]["input_error"] == "URL Inválida"

    # AÑADIMOS EL PARCHE DE CONFIGSINGLETON AQUÍ
    @patch("ui.mediator.ConfigSingleton") 
    @patch("ui.mediator.render_template")
    @patch("ui.mediator.HistoryComponent")
    @patch("ui.mediator.OutputComponent")
    @patch("ui.mediator.OptionsComponent")
    @patch("ui.mediator.InputComponent")
    def test_handle_analyze_success_flow(self, MockInput, MockOpts, MockOut, MockHist, mock_render, MockConfig, mediator, mock_subject):
        """
        [POST /analyze] Flujo Exitoso.
        Input OK -> Options OK -> Subject OK -> Render OK.
        """
        # Preparación
        url = "http://git.com/repo"
        MockInput.return_value.parse.return_value = (url, None)
        MockOpts.return_value.parse.return_value = {"force": True}
        
        # Simulamos valores del ConfigSingleton (aunque OptionsComponent esté mockeado, es buena práctica)
        MockConfig.get_instance.return_value.duplication_window = 10

        # Simulamos respuesta del negocio
        mock_subject.peticion.return_value = {"loc": 500}
        MockOut.return_value.prepare.return_value = {"metrics": "ok"}
        
        form_data = {"repo_url": url}

        # Ejecución
        mediator.handle_analyze(form_data)

        # Aserciones
        # 1. Los datos fluyeron correctamente al subject
        mock_subject.peticion.assert_called_once_with(url, force=True)
        # 2. Se actualizó el historial tras el análisis
        assert MockHist.return_value.get_entries.called
        # 3. El renderizado final incluye los resultados
        assert mock_render.call_args[1]["metrics"] == "ok"
