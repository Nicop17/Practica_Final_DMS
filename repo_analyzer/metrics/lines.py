from .base import MetricStrategy

class LinesStrategy(MetricStrategy):
    """
    Estrategia concreta para calcular el número de líneas por fichero (LOC).
    """
    def compute(self, source: str) -> int:
        """
        Recibe el código fuente (str) y devuelve el número de líneas.
        """
        return len(source.splitlines())