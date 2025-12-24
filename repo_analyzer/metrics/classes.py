import ast
from typing import Dict
from .base import MetricStrategy

class ClassesStrategy(MetricStrategy):
    """
    Estrategia para calcular métricas de Clases (Métodos públicos).
    Usa AST para identificar estructuras de clase, por lo que lo separamos de functions.py.
    """
    
    def compute(self, source: str) -> Dict[str, int]:
        """
        Devuelve: { "NombreClase": numero_metodos_publicos }
        """
        results = {}
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return results

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                public_methods = 0
                # Recorremos el cuerpo de la clase
                for item in node.body:
                    # Si es función y no empieza por _, es público
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Contamos solo los que no empiezan por "_" (públicos)
                        if not item.name.startswith("_"):
                            public_methods += 1
                
                results[node.name] = public_methods
        
        return results