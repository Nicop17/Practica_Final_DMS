from pathlib import Path
from typing import Dict, Any, List, Set

# Importamos las estrategias
from .base import MetricStrategy
from .lines import LinesStrategy
from .imports import NumImportsStrategy
from .functions import FunctionsStrategy
from .duplication import DuplicationStrategy
from .maintainability import MaintainabilityStrategy
from .todos import TodosStrategy
from .classes import ClassesStrategy

def list_py_files(root: Path) -> List[Path]:
    """Lista recursivamente archivos .py ignorando carpetas comunes."""
    IGNORED_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'env', 'tests', 'fixtures', 'migrations'}
    result = []
    
    for path in root.rglob('*.py'):
        # Revisamos si alguna parte de la ruta está en la lista negra
        if not set(path.parts).intersection(IGNORED_DIRS):
            result.append(path)
            
    return result

class MetricsFacade:
    """
    Fachada que coordina la ejecución de todas las métricas.
    """
    
    def __init__(self):
        # Inicializamos las estrategias
        self.strategies: Dict[str, MetricStrategy] = {
            "lines": LinesStrategy(),
            "imports": NumImportsStrategy(),
            "functions": FunctionsStrategy(),
            "duplication": DuplicationStrategy(),
            "maintainability": MaintainabilityStrategy(),
            "todos": TodosStrategy(),
            "classes": ClassesStrategy(),
        }

    def compute_all(self, repo_path: Path, options: dict) -> Dict[str, Any]:
        """
        Ejecuta el análisis completo sobre un repositorio.
        """
        repo_path = Path(repo_path)
        dup_window = options.get("dup_window", 4)

        # Estructura del resultado
        results = {
            "repo": str(repo_path),
            "analyzed_at": None, 
            "summary": {
                "num_files": 0,
                "total_lines": 0,
                "avg_cc": 0.0,
                "maintainability_index": 0.0,
                "duplication": 0.0,
                "todos": 0,
            },
            "files": []
        }

        py_files = list_py_files(repo_path)
        results["summary"]["num_files"] = len(py_files)

        if not py_files:
            return results

        # Acumuladores
        total_cc_sum = 0.0
        total_functions_count = 0
        total_mi_sum = 0.0
        total_duplication_sum = 0.0

        for filepath in py_files:
            try:
                # 1. Leer código (Punto crítico de fallo controlado)
                source_code = filepath.read_text(encoding="utf-8", errors="replace")
                
                # 2. Calcular métricas
                n_lines = self.strategies["lines"].compute(source_code)
                n_imports = self.strategies["imports"].compute(source_code)
                n_todos = self.strategies["todos"].compute(source_code)
                func_metrics = self.strategies["functions"].compute(source_code)
                class_metrics = self.strategies["classes"].compute(source_code)
                
                # Métricas que requieren Path
                mi_score = self.strategies["maintainability"].compute(filepath)
                dup_ratio = self.strategies["duplication"].compute(filepath, window=dup_window)

                # 3. Procesar datos del archivo
                file_total_cc = sum(f.get("cc", 0) for f in func_metrics.values())
                file_num_funcs = len(func_metrics)
                file_avg_cc = (file_total_cc / file_num_funcs) if file_num_funcs > 0 else 0.0

                file_data = {
                    "path": str(filepath.relative_to(repo_path)),
                    "total_lines": n_lines,
                    "num_imports": n_imports,
                    "todos": n_todos,
                    "duplication_ratio": dup_ratio,
                    "maintainability_index": mi_score,
                    "avg_cc": file_avg_cc,
                    "functions": func_metrics,
                    "classes": class_metrics
                }
                
                results["files"].append(file_data)

                # 4. Acumular al Global
                results["summary"]["total_lines"] += n_lines
                results["summary"]["todos"] += n_todos
                
                total_mi_sum += mi_score
                total_duplication_sum += dup_ratio
                total_cc_sum += file_total_cc
                total_functions_count += file_num_funcs

            except Exception as e:
                # Si falla un archivo, lo saltamos pero no paramos todo
                print(f"Error analizando {filepath.name}: {e}")
                continue

        # 5. Promedios finales
        num_analyzed = len(results["files"])
        if num_analyzed > 0:
            results["summary"]["maintainability_index"] = total_mi_sum / num_analyzed
            results["summary"]["duplication"] = total_duplication_sum / num_analyzed
        
        if total_functions_count > 0:
            results["summary"]["avg_cc"] = total_cc_sum / total_functions_count

        return results
