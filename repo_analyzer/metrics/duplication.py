from pathlib import Path
from typing import Dict, Any, List, Tuple, Generator
from collections import defaultdict
import hashlib
from .base import MetricStrategy

def normalize_to_lines(source, remove_comments=True, remove_def_class_header=True) -> List[str]:
    """
    Rompe el código en líneas. Colapsa todos los espacios en blanco.
        Elimina todas las lineas que comiencen en # (si remove_comments= True)
        Elimina todas las lineas que comiencen por def o class (si remove_def_class_header = True)
    """
    lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped: continue
        if remove_comments and stripped.startswith("#"): continue
        if remove_def_class_header and (stripped.startswith("def ") or stripped.startswith("class ")): continue
        
        if remove_comments and "#" in stripped:
            stripped = stripped.split("#", 1)[0].strip()
            
        lines.append(" ".join(stripped.split()))
    return lines

def create_shingles(lines, window) -> Generator[Tuple[int, List[str]], Any, Any]:
    """
    Genera conjuntos de ítems contiguos de tamaño 'window'.
    Devuelve un generador que produce tuplas de (índice, shingle_list).
    """
    for i in range(len(lines) - window + 1):
        yield (i + 1, lines[i:i + window])

def compute_duplication(path, window):
    """
    Carga el código fuente desde el fichero que está en filepath.
    Normaliza su código usando normalize_to_lines.
    Genera conjuntos de items contiguos de tamaño window, usando create_shingles.
    Para cada shingle, obtiene su hash y lo almacena
    """
    source = Path(path).read_text(encoding="utf-8")
    norm_lines = normalize_to_lines(source)
    shingles = create_shingles(norm_lines, window)

    seen = defaultdict(int)
    total = 0

    for _, shingle in shingles:
        total += 1
        text = "\n".join(shingle)
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()
        seen[h] += 1

    if total == 0:
        return 0.0

    duplicates = sum(freq for freq in seen.values() if freq > 1)
    
    # La duplicación es la cuenta de cuántas ocurrencias son duplicadas / el total de shingles
    return duplicates / total


class DuplicationStrategy(MetricStrategy):
    """
    Calcula el ratio de duplicación por fichero usando la heurística de shingles.
    """
    def compute(self, filepath: Path, window: int) -> float:
        """
        Recibe la ruta del archivo y la ventana (window) para calcular el ratio de duplicación.
        """
        # Delegar el trabajo de cálculo a la función reutilizada
        return compute_duplication(filepath, window)