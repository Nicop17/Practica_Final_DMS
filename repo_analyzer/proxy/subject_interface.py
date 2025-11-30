from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union
from pathlib import Path

class SubjectInterface(ABC):
    """
    Interfaz común (Subject) para el Proxy y el RealSubject (lógica de negocio).
    Define el contrato que la UI espera usar.
    """

    @abstractmethod
    def peticion(self, repo_ref: Union[str, Path], force: bool = False, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Solicita un análisis.
        repo_ref: Puede ser una URL o un path local.
        """
        pass

    @abstractmethod
    def list_analyses(self) -> List[Dict[str, Any]]:
        """Lista el historial de análisis."""
        pass