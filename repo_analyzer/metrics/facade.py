from pathlib import Path
from typing import Dict, Any, List

from .base import MetricStrategy
from .lines import LinesStrategy
from .imports import NumImportsStrategy
from .functions import FunctionsStrategy
from .duplication import DuplicationStrategy
from .maintainability import MaintainabilityStrategy

def list_py_files(root: str | Path) -> List[Path]:
    """Lista archivos .py excluyendo directorios ignorados."""
    root_path = Path(root)
    result = []
    IGNORED_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'tests', 'fixtures'} 
    for path in root_path.rglob('*.py'):
        if not any(part in IGNORED_DIRS for part in path.parts):
            result.append(path)
    return result


class MetricsFacade:
    """
    Coordina la ejecución de todas las estrategias de métricas sobre un repositorio local.
    """
    
    def __init__(self):
        # 1. Instanciar y almacenar TODAS las estrategias
        self.strategies: Dict[str, MetricStrategy] = {
            "lines_count": LinesStrategy(),
            "num_imports": NumImportsStrategy(),
            "functions": FunctionsStrategy(), 
            "duplication": DuplicationStrategy(), 
            "maintainability": MaintainabilityStrategy(), 
        }

    def compute_all(self, repo_path: Path, options: dict) -> Dict[str, Any]:
        """
        Recorre el repositorio, aplica todas las estrategias y agrega los resultados.
        """
        # Obtener la ventana de duplicación de las opciones o usar el valor por defecto
        dup_window = options.get("dup_window", 10) # Usar 10 como fallback si no se obtiene de ConfigSingleton
        
        results: Dict[str, Any] = {
            "repo": str(repo_path),
            "analyzed_at": None, # Se rellenará antes de guardar en DB (por ProxySubject)
            "summary": {
                "num_files": 0,
                "total_lines": 0,
                "avg_cc": 0.0, 
                "maintainability_index": 0.0, 
                "duplication": 0.0
            },
            "files": [] 
        }
        
        py_files = list_py_files(repo_path)
        total_cc = 0
        total_functions = 0
        total_mi = 0
        
        for filepath in py_files:
            try:
                source_code = filepath.read_text(encoding="utf-8")
                               
                # Métricas por Función (AST)
                func_metrics = self.strategies["functions"].compute(source_code)
                
                # Métricas por Fichero (Sencillas)
                file_metrics = {
                    "path": str(filepath.relative_to(repo_path)),
                    "total_lines": self.strategies["lines_count"].compute(source_code),
                    "num_imports": self.strategies["num_imports"].compute(source_code),
                    "todos": self.strategies["todos"].compute(source_code),
                    # Métricas que requieren ruta (Path) o ventana (options)
                    "duplication_ratio": self.strategies["duplication"].compute(filepath, dup_window),
                    "maintainability_index": self.strategies["maintainability"].compute(filepath),
                    "functions": func_metrics,
                }
                               
                # Calcular CC promedio por fichero (para el resumen global)
                num_file_funcs = len(func_metrics)
                file_cc_sum = sum(f["cc"] for f in func_metrics.values())
                
                file_metrics["avg_cc"] = file_cc_sum / num_file_funcs if num_file_funcs > 0 else 0.0
                
                
                total_cc += file_cc_sum
                total_functions += num_file_funcs
                results["summary"]["total_lines"] += file_metrics["total_lines"]
                total_mi += file_metrics["maintainability_index"] # Se promediará al final
                results["summary"]["duplication"] += file_metrics["duplication_ratio"] # Se promediará al final

                results["files"].append(file_metrics)
                
            except Exception as e:
                # Capturar cualquier error para que el análisis continúe si es posible
                print(f"Advertencia: Error al procesar {filepath}. {e}")
                
        # Finalizar Resumen 
        
        results["summary"]["num_files"] = len(py_files)
        
        # CC Promedio Global
        results["summary"]["avg_cc"] = total_cc / total_functions if total_functions > 0 else 0.0
        
        # MI Promedio Global
        num_files_analyzed = len(results["files"])
        results["summary"]["maintainability_index"] = total_mi / num_files_analyzed if num_files_analyzed > 0 else 0.0
        
        # Duplication Ratio Promedio Global
        results["summary"]["duplication"] = results["summary"]["duplication"] / num_files_analyzed if num_files_analyzed > 0 else 0.0
        
        return results