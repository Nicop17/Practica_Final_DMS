from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Dependencias del sistema
from config import ConfigSingleton
from repo.repo_manager import RepoManager
from repo.db_manager import DBManager
from metrics.facade import MetricsFacade

# Interfaz que implementa este Proxy
from .subject_interface import SubjectInterface

class ProxySubject(SubjectInterface):
    """
    Patrón Proxy: Actúa como intermediario entre la UI y la lógica de negocio.
    """
    
    def __init__(self):
        # Inicialización de todos los subsistemas
        self.config = ConfigSingleton.get_instance()
        self.db = DBManager()
        self.repo_manager = RepoManager()
        self.facade = MetricsFacade()

    def peticion(self, repo_url: str, force: bool = False, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gestiona la petición de análisis de un repositorio.
        """
        if options is None:
            options = {}

        try:
            # 1. GESTIÓN DE RUTA LOCAL
            # Calculamos la ruta de destino antes de operar
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            local_path = self.cache_dir / repo_name

            # 2. LÓGICA DE FORZADO (Limpieza previa)
            if force:
                print(f"[Proxy] Modo force: Eliminando rastro local de {repo_url}")
                self.repo_manager.remove_repo(local_path)
                # Al no retornar aquí, obligamos al flujo a continuar al análisis
            
            # 3. CONSULTA DE CACHÉ (Solo si no es force)
            elif not force:
                cached_result = self.db.get_latest_analysis(repo_url)
                if cached_result:
                    print(f"[Proxy] HIT: Recuperado de base de datos")
                    cached_result["_from_cache"] = True
                    cached_result["forced"] = False
                    return cached_result

            # 4. ANÁLISIS REAL (Descarga y Cálculo)
            print(f"[Proxy] Iniciando análisis: {repo_url}")
            # ensure_repo ahora clonará siempre si force borró la carpeta antes
            actual_path = self.repo_manager.ensure_repo(repo_url)
            
            results = self.facade.compute_all(actual_path, options)

            # 5. METADATOS Y PERSISTENCIA
            results["repo"] = repo_url
            results["analyzed_at"] = datetime.now().isoformat()
            results["_from_cache"] = False
            results["forced"] = force

            self.db.save_analysis(results)
            return results

        except Exception as e:
            # Tu gestión de excepciones actual es correcta y necesaria según el enunciado
            error_msg = f"Error procesando {repo_url}: {str(e)}"
            return {
                "repo": repo_url,
                "error": error_msg,
                "summary": {"num_files": 0, "total_lines": 0},
                "_from_cache": False,
                "forced": force
            }

    def list_analyses(self) -> List[Dict[str, Any]]:
        return self.db.list_analyses()
