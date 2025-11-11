from abc import ABC, abstractmethod
from typing import Any

class MetricStrategy(ABC):
    """
    Clase base abstracta que define la interfaz común para todas las métricas
    (Patrón Strategy).
    """
    @abstractmethod
    def compute(self, data: Any) -> Any:
        """
        Calcula la métrica a partir de los datos de entrada. 
        Debe ser implementado por todas las subclases concretas.
        
        Args:
            data: El dato de entrada, que puede ser código fuente (str), 
                  un AST, o una ruta (Path), dependiendo de la estrategia.
        
        Returns:
            El resultado de la métrica.
        """
        pass