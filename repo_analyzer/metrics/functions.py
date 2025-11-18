import ast
from typing import Dict, Any, List
from .base import MetricStrategy

def lines_per_function(fn_node: ast.FunctionDef) -> int:
    """
    Devuelve el número de líneas que ocupa una función.
    """
    return fn_node.end_lineno - fn_node.lineno + 1

def num_params(fn_node: ast.FunctionDef, count_first: bool = True) -> int:
    """
    Cuenta parámetros formales declarados en la función.
    """
    n_params = len(fn_node.args.args)
    if not count_first and n_params > 0:
        n_params -= 1  # No contar 'self' en métodos (asumiendo que es el primer argumento)
    return n_params

def cyclomatic_per_function(fn_node: ast.FunctionDef) -> int:
    """
    Añade un punto de complejidad ciclomática por cada decision point. Los decision points son nodos que introducen caminos alternativos.
    """
    decision_points = 0
    
    def visit(node):
        nonlocal decision_points
        if isinstance(node, (ast.If, ast.For, ast.While, ast.AsyncFor,
                             ast.ExceptHandler, ast.IfExp)):  # Puntos de decisión simples
            decision_points += 1
        elif isinstance(node, ast.comprehension):  # Comprehensions
            decision_points += 1
        elif isinstance(node, ast.BoolOp):  # Operadores booleanos
            decision_points += len(node.values) - 1
        elif isinstance(node, ast.Compare):  # Comparaciones encadenadas
            decision_points += max(len(node.ops) - 1, 0)
        
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(fn_node)
    return 1 + decision_points

def max_nesting(fn_node: ast.FunctionDef) -> int:
    """
    Devuelve la máxima profundidad de anidamiento de estructuras de control dentro de la función (cuántos niveles de if/for/while/try/with anidados hay).
    """
    max_depth = 0
    
    def visit(node, current_depth=0):
        nonlocal max_depth
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try,
                             ast.With, ast.AsyncWith)):
            current_depth += 1
            max_depth = max(max_depth, current_depth)
            for child in ast.iter_child_nodes(node):
                visit(child, current_depth)
            return
        for child in ast.iter_child_nodes(node):
            visit(child, current_depth)

    visit(fn_node)
    return max_depth


class FunctionsStrategy(MetricStrategy):
    """
    Reúne métricas por función (LOC, parámetros, CC, anidamiento) usando el AST.
    """
    def compute(self, source: str) -> Dict[str, Any]:
        """
        Analiza el código y devuelve un diccionario con métricas por función/método.
        """
        results: Dict[str, Any] = {}

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return results

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                
                is_method = isinstance(node.parent, ast.ClassDef) if hasattr(node, 'parent') else False
                
                # Asignar el nombre único para funciones (ej. ClassName.method_name)
                func_name = node.name
                if is_method:
                    # En entornos de AST más simples, esto requeriría un ClassVisitor.
                    # Asumiremos que el nombre es suficiente para este ejercicio.
                    pass 

                # Determinar si es un método para saber si descontar 'self'
                count_self = not (is_method and node.args.args and node.args.args[0].arg == 'self')
                
                # Calcular todas las métricas
                params = num_params(node, count_first=count_self)
                loc = lines_per_function(node)
                cc = cyclomatic_per_function(node)
                nesting = max_nesting(node)

                results[func_name] = {
                    "loc": loc,
                    "params": params,
                    "cc": cc,
                    "max_nesting": nesting
                }

        return results