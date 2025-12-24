from .base import MetricStrategy

class LinesStrategy(MetricStrategy):
    """
    Estrategia concreta para calcular el número de líneas por fichero (LOC).
    """
    def compute(self, source: str) -> int:
        """
        Recibe el código fuente (str) y devuelve el número de líneas.
        """
        if source is None:
            raise TypeError("Debe ser string")

        if not isinstance(source, str):
            raise TypeError("El código fuente debe ser un string")
        
        lines = source.splitlines()
        # Si el archivo es solo un '\n', splitlines da [''], pero el test espera 0
        if source == "\n" or not source.strip():
            return 0
        return len(lines)