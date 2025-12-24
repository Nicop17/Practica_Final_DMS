import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# ==============================================================================
# CONFIGURACIÓN DEL ENTORNO DE PRUEBAS
# ==============================================================================

# 1. Localización de la raíz del proyecto para asegurar importaciones correctas
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Aislamiento de dependencias externas (Flask)
# Se mockea globalmente para permitir la ejecución de lógica pura del Mediador
mock_flask = MagicMock()
sys.modules["flask"] = mock_flask

try:
    from ui.mediator import UIMediator
except ImportError as e:
    pytest.fail(f"ERROR DE SISTEMA: No se encuentra el módulo 'ui'. Verifique el PYTHONPATH. Detalle: {e}")


class TestUIMediator:
    """
    Suite de validación para el patrón Mediador (UIMediator).
    
    Verifica la correcta coordinación entre los componentes de la interfaz de usuario
    (Input, Options, Output, History) y la lógica de negocio (Subject), garantizando
    un bajo acoplamiento y un flujo de datos íntegro.
    """

    @pytest.fixture
    def mock_subject(self):
        """Provee un doble de prueba para la lógica de negocio (Proxy/Subject)."""
        subject = MagicMock()
        subject.list_analyses.return_value = []
        subject.peticion.return_value = {}
        return subject

    @pytest.fixture
    def mediator(self, mock_subject):
        """Instancia el Mediador inyectando la dependencia del Subject."""
        return UIMediator(mock_subject)

    # ==========================================================================
    # VALIDACIÓN DE FLUJOS DE COORDINACIÓN
    # ==========================================================================

    @patch("ui.mediator.render_template")
    @patch("ui.mediator.HistoryComponent")
    @patch("ui.mediator.OutputComponent")
    @patch("ui.mediator.OptionsComponent")
    @patch("ui.mediator.InputComponent")
    def test_show_index_initialization(self, MockInput, MockOpts, MockOut, MockHist, mock_render, mediator, mock_subject):
        """
        Valida la carga inicial del dashboard [GET /].
        Asegura que el Mediador:
        1. Solicite la recuperación del historial de análisis mediante el HistoryComponent.
        2. Renderice la vista base 'index.html' pasando los datos recuperados.
        """
        # Configuración del historial simulado
        MockHist.return_value.get_entries.return_value = {"history": ["item_test"]}

        mediator.show_index()

        # Verificación de la orquestación
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
        Valida la protección de la lógica de negocio ante datos de entrada erróneos [POST /analyze].
        Garantiza que:
        1. Si la validación en InputComponent falla, el proceso de análisis se detiene.
        2. No se realiza ninguna petición al Subject (negocio).
        3. Se retorna a la UI con los mensajes de error correspondientes.
        """
        # Simulación de fallo en validación de entrada
        MockInput.return_value.parse.return_value = (None, "URL Inválida")
        MockInput.return_value.context.return_value = {"input_error": "URL Inválida"}
        
        form_data = {} 

        mediator.handle_analyze(form_data)

        # El negocio debe permanecer intacto si la entrada es inválida
        mock_subject.peticion.assert_not_called()
        assert mock_render.call_args[1]["input_error"] == "URL Inválida"

    @patch("ui.mediator.ConfigSingleton") 
    @patch("ui.mediator.render_template")
    @patch("ui.mediator.HistoryComponent")
    @patch("ui.mediator.OutputComponent")
    @patch("ui.mediator.OptionsComponent")
    @patch("ui.mediator.InputComponent")
    def test_handle_analyze_success_flow(self, MockInput, MockOpts, MockOut, MockHist, mock_render, MockConfig, mediator, mock_subject):
        """
        Valida el flujo completo de análisis exitoso [POST /analyze].
        Comprueba la cadena de mando del Mediador:
        1. Parseo de entrada y opciones de configuración.
        2. Ejecución del análisis en el Subject con los parámetros correctos.
        3. Preparación de resultados mediante OutputComponent.
        4. Actualización del historial y renderizado final.
        """
        # Configuración de flujo exitoso
        url = "http://git.com/repo"
        MockInput.return_value.parse.return_value = (url, None)
        MockOpts.return_value.parse.return_value = {"force": True}
        MockConfig.get_instance.return_value.duplication_window = 10
        mock_subject.peticion.return_value = {"loc": 500}
        MockOut.return_value.prepare.return_value = {"metrics": "ok"}
        
        form_data = {"repo_url": url}

        mediator.handle_analyze(form_data)

        # Verificación de integridad de datos y flujo
        mock_subject.peticion.assert_called_once_with(url, force=True, options={"force": True})        
        assert MockHist.return_value.get_entries.called
        assert mock_render.call_args[1]["metrics"] == "ok"