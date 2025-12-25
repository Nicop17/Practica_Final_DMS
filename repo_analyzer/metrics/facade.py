from pathlib import Path
from typing import Dict, Any, List, Set

# Importación de las estrategias de análisis (Patrón Strategy)
from .base import MetricStrategy
from .lines import LinesStrategy
from .imports import NumImportsStrategy
from .functions import FunctionsStrategy
from .duplication import DuplicationStrategy
from .maintainability import MaintainabilityStrategy
from .todos import TodosStrategy
from .classes import ClassesStrategy

def list_py_files(root: Path) -> List[Path]:
    """
    Explora recursivamente un directorio para encontrar archivos de código fuente Python (.py).
    
    Aplica un filtro de exclusión robusto para ignorar directorios de configuración,
    control de versiones, entornos virtuales y tests, basándose en la ruta relativa
    al proyecto (para evitar falsos positivos con carpetas del sistema).

    Args:
        root (Path): Ruta raíz del repositorio descargado.

    Returns:
        List[Path]: Lista de rutas a archivos .py válidos para el análisis.
    """
    # Lista negra de directorios a excluir del análisis métrico
    IGNORED_DIRS = {
        '.git', '__pycache__', 'venv', '.venv', 'env', 
        'tests', 'test', 'fixtures', 'migrations', 
        'docs', 'build', 'dist', 'egg-info'
    }
    
    result = []
    
    # [DEBUG] Trazabilidad del directorio raíz
    print(f"[DEBUG FACADE] Iniciando búsqueda de archivos en: {root.absolute()}")
    
    if not root.exists():
        print(f"[DEBUG FACADE] ❌ Error Crítico: La ruta {root} no existe en el sistema de archivos.")
        return []

    # 1. Recolección: Buscamos todos los archivos .py indiscriminadamente
    all_py_files = list(root.rglob('*.py'))
    print(f"[DEBUG FACADE] Archivos .py detectados (bruto): {len(all_py_files)}")

    # 2. Filtrado: Aplicamos reglas de negocio para descartar archivos irrelevantes
    for path in all_py_files:
        try:
            # IMPORTANTE: Calculamos la ruta relativa respecto a la raíz del repo.
            # Esto evita que carpetas del sistema operativo (como /home/usuario/tests/...) 
            # interfieran con el filtrado del proyecto.
            rel_path = path.relative_to(root)
            parts = set(rel_path.parts)
            
            # Verificamos intersección con directorios ignorados
            intersection = parts.intersection(IGNORED_DIRS)
            
            if not intersection:
                result.append(path)
            else:
                # Opcional: Descomentar para auditar qué se está ignorando
                # print(f"[DEBUG FACADE] Ignorando archivo de infraestructura/test: {rel_path}")
                pass
                
        except ValueError:
            # Si path no es relativo a root (caso extremo), lo incluimos por seguridad
            result.append(path)
            
    print(f"[DEBUG FACADE] ✅ Archivos válidos para análisis: {len(result)}")
    return result


class MetricsFacade:
    """
    Patrón Fachada (Facade): Proporciona una interfaz unificada y simplificada 
    para ejecutar el conjunto complejo de estrategias de métricas.
    
    Responsabilidades:
    1. Orquestar la ejecución secuencial de métricas sobre cada archivo.
    2. Agregar resultados parciales (sumas y promedios) en un resumen global.
    3. Manejar errores a nivel de archivo para evitar detener el análisis completo.
    """
    
    def __init__(self):
        """Inicializa el catálogo de estrategias disponibles."""
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
        Ejecuta el pipeline de análisis completo sobre un repositorio.

        Args:
            repo_path (Path): Ruta local al repositorio clonado.
            options (dict): Configuración del usuario (ej. ventana de duplicación).

        Returns:
            Dict[str, Any]: Estructura JSON-ready con resultados detallados y sumarios.
        """
        repo_path = Path(repo_path)
        dup_window = options.get("dup_window", 4)

        # Inicialización de la estructura de datos de respuesta
        results = {
            "repo": str(repo_path),
            "analyzed_at": None, # Se inyectará en la capa superior (Proxy)
            "summary": {
                "num_files": 0,
                "total_lines": 0,
                "avg_cc": 0.0,
                "maintainability_index": 0.0,
                "duplication": 0.0,
                "todos": 0,
                "summary_funcs": 0 # Útil para depuración y validación
            },
            "files": []
        }

        # Paso 1: Obtención de archivos filtrados
        py_files = list_py_files(repo_path)
        results["summary"]["num_files"] = len(py_files)

        if not py_files:
            print("[DEBUG FACADE] ⚠️ Alerta: Repositorio vacío o sin archivos Python válidos.")
            return results

        # Acumuladores para el cálculo de estadísticas globales (Promedios)
        total_cc_sum = 0.0
        total_functions_count = 0
        total_mi_sum = 0.0
        total_duplication_sum = 0.0

        # Paso 2: Iteración y Análisis Archivo por Archivo
        for filepath in py_files:
            try:
                # Lectura del código fuente (Manejo de encoding robusto)
                source_code = filepath.read_text(encoding="utf-8", errors="replace")
                
                # --- Ejecución de Estrategias ---
                
                # Métricas basadas en texto plano
                n_lines = self.strategies["lines"].compute(source_code)
                n_imports = self.strategies["imports"].compute(source_code)
                n_todos = self.strategies["todos"].compute(source_code)
                
                # Métricas basadas en AST (Abstract Syntax Tree)
                func_metrics = self.strategies["functions"].compute(source_code)
                class_metrics = self.strategies["classes"].compute(source_code)
                
                # Métricas que requieren contexto de archivo (Path)
                mi_score = self.strategies["maintainability"].compute(filepath)
                dup_ratio = self.strategies["duplication"].compute(filepath, window=dup_window)

                # --- Agregación Local (Por archivo) ---
                
                file_total_cc = sum(f.get("cc", 0) for f in func_metrics.values())
                file_num_funcs = len(func_metrics)
                # Evitar división por cero si no hay funciones
                file_avg_cc = (file_total_cc / file_num_funcs) if file_num_funcs > 0 else 0.0

                # Construcción del DTO (Data Transfer Object) para el archivo actual
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

                # --- Actualización de Acumuladores Globales ---
                results["summary"]["total_lines"] += n_lines
                results["summary"]["todos"] += n_todos
                results["summary"]["summary_funcs"] += file_num_funcs
                
                total_mi_sum += mi_score
                total_duplication_sum += dup_ratio
                total_cc_sum += file_total_cc
                total_functions_count += file_num_funcs

            except Exception as e:
                # Manejo de fallos aislados: Un archivo corrupto no debe detener el análisis
                print(f"[DEBUG FACADE] Excepción controlada analizando {filepath.name}: {e}")
                continue

        # Paso 3: Cálculo de Promedios Finales
        num_analyzed = len(results["files"])
        
        if num_analyzed > 0:
            results["summary"]["maintainability_index"] = total_mi_sum / num_analyzed
            results["summary"]["duplication"] = total_duplication_sum / num_analyzed
        
        if total_functions_count > 0:
            results["summary"]["avg_cc"] = total_cc_sum / total_functions_count
        else:
            results["summary"]["avg_cc"] = 0.0

        return results
