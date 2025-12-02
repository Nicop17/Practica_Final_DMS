from .base import MetricStrategy

class TodosStrategy(MetricStrategy):
    """
    Estrategia para contar comentarios TODO y FIXME.
    """
    def compute(self, source: str) -> int:
        count = 0
        for line in source.splitlines():
            # Buscamos la marca de comentario (#) y las palabras clave
            if "#" in line and ("TODO" in line or "FIXME" in line):
                count += 1
        return count