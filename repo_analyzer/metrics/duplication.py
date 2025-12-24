from pathlib import Path
from typing import Dict, Any, List, Tuple, Generator
from collections import defaultdict
import hashlib
import re
from .base import MetricStrategy

def normalize_to_lines(source, remove_comments=True, remove_def_class_header=True) -> List[str]:
    """
    Rompe el código en líneas. Colapsa todos los espacios en blanco.
        Elimina todas las lineas que comiencen en # (si remove_comments= True)
        Elimina todas las lineas que comiencen por def o class (si remove_def_class_header = True)
    """
    lines = []
    for line in source.splitlines():
        clean_line = line
        if remove_comments:
            # Heurística simple: si hay un '#' fuera de comillas, es comentario
            if '#' in clean_line and '"' not in clean_line and "'" not in clean_line:
                clean_line = clean_line.split('#')[0]
        
        clean_line = clean_line.strip()
        if remove_def_class_header:
            # Soporte para 'async def'
            clean_line = re.sub(r'^(async\s+)?(def|class)\s+.*', '', clean_line)        
        
        if clean_line: 
            lines.append(clean_line)
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
    p = Path(path)
    # Manejo de archivos inexistentes
    if not p.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
        
    try:
        # errors='ignore' para archivos binarios o Latin-1
        source = p.read_text(encoding='utf-8', errors='ignore')
        from collections import Counter
        lines = normalize_to_lines(source)
        if len(lines) < window: return 0.0
        shingle_hashes = [hashlib.md5("".join(s).encode()).hexdigest() for _, s in create_shingles(lines, window)]
        counts = Counter(shingle_hashes)
        duplicated = sum(freq for freq in counts.values() if freq > 1)
        
        return duplicated / len(shingle_hashes)
                                
    except Exception:
        return 0.0

class DuplicationStrategy(MetricStrategy):
    """
    Calcula el ratio de duplicación por fichero usando la heurística de shingles.
    """
    def compute(self, filepath: Path, window: int=4) -> float:
        """
        Recibe la ruta del archivo y la ventana (window) para calcular el ratio de duplicación.
        """
        # Delegar el trabajo de cálculo a la función reutilizada
        return compute_duplication(filepath, window)