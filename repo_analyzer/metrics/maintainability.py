import ast, io, tokenize, keyword, math
from pathlib import Path
from collections import defaultdict
from .base import MetricStrategy

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

def compute_maintainability_index(filepath):
    """
    Carga el código fuente desde el fichero que está en filepath.
    Obtiene LOC y CC usando funciones de sesiones anteriores.
    Obtiene el volumen
    Aplica la formula
    """

    source = Path(filepath).read_text(encoding="utf-8")
    tree = ast.parse(source)

    # 1. LOC y CC
    loc, cc_total = 0, 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            loc += node.end_lineno - node.lineno + 1 # Usando el atributo del nodo
            cc_total += cyclomatic_per_function(node)

    # 2. Halstead
    counts = defaultdict(int)
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    for tok in tokens:
        if tok.type == tokenize.OP or keyword.iskeyword(tok.string):
            counts[("op", tok.string)] += 1
        elif tok.type in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING):
            counts[("operand", tok.string)] += 1

    n1 = len({k for k, _ in counts if k == "op"})
    n2 = len({k for k, _ in counts if k == "operand"})
    N1 = sum(v for (k, _), v in counts.items() if k == "op")
    N2 = sum(v for (k, _), v in counts.items() if k == "operand")

    n = n1 + n2
    N = N1 + N2
    V = N * math.log2(n) if n > 1 else 0.0

    # 3. Fórmula MI (Asegurando valores mínimos > 0)
    V = max(V, 1.0)
    CC = max(cc_total, 1.0)
    LOC = max(loc, 1)
    mi_raw = 171.0 - 5.2 * math.log(V) - 0.23 * CC - 16.2 * math.log(LOC)
    mi = mi_raw * 100.0 / 171.0
    return max(0.0, min(100.0, round(mi, 1)))


class MaintainabilityStrategy(MetricStrategy):
    """
    Calcula el Índice de Mantenibilidad (MI) estimado (0-100) para un fichero.
    """
    def compute(self, filepath: Path) -> float:
        """
        Recibe la ruta del archivo y devuelve el MI.
        """
        return compute_maintainability_index(filepath)