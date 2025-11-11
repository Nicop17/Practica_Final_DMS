from .base import MetricStrategy

class NumImportsStrategy(MetricStrategy):
    """
    Estrategia concreta para contar el número de declaraciones de import
    """
    def compute(self, source: str) -> int:
        """
        Recibe el código fuente (str) y devuelve el conteo de imports.
        """
        count = 0
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                count += 1
        return count