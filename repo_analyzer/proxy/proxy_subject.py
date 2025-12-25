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
    Responsabilidades:
    1. Cacheo: Comprueba si el análisis ya existe en BD para ahorrar tiempo.
    2. Si no hay caché, coordina la descarga (RepoManager) y el cálculo (MetricsFacade).
    3. Persistencia: Guarda los nuevos cálculos en la BD.
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
                # 1. CONSULTA DE CACHÉ
                if not force:
                    cached_result = self.db.get_latest_analysis(repo_url)
                    if cached_result:
                        print(f"[Proxy] HIT: Análisis recuperado de caché para {repo_url}")
                        
                        # --- CORRECCIÓN 1: Marcar que viene de caché ---
                        cached_result["_from_cache"] = True
                        cached_result["forced"] = False
                        
                        return cached_result

                # 2. CÁLCULO REAL (MISS o FORCE)
                print(f"[Proxy] MISS (o force): Iniciando análisis completo para {repo_url}")
                
                local_path = self.repo_manager.ensure_repo(repo_url)

                if force:
                    print("[Proxy] Limpiando copia local...")
                    self.repo_manager.remove_repo(local_path)
                    local_path = self.repo_manager.ensure_repo(repo_url)

                print("[Proxy] Calculando métricas...")
                results = self.facade.compute_all(local_path, options)

                # Completar metadatos
                results["repo"] = repo_url
                if "analyzed_at" not in results or not results["analyzed_at"]:
                    results["analyzed_at"] = datetime.now().isoformat()

                # Guardar en BD (sin las marcas efímeras _from_cache/forced, para mantener la BD limpia)
                self.db.save_analysis(results)
                
                # --- CORRECCIÓN 2: Marcar el estado actual para la UI ---
                results["_from_cache"] = False
                results["forced"] = force  # Reflejamos si el usuario pidió forzar
                
                return results

            except Exception as e:
                # ... (Manejo de errores igual que antes) ...
                error_msg = f"Error procesando {repo_url}: {str(e)}"
                print(f"[Proxy Error] {error_msg}")
                return {
                    "repo": repo_url,
                    "analyzed_at": datetime.now().isoformat(),
                    "error": error_msg,
                    "summary": {"num_files": 0, "total_lines": 0},
                    "_from_cache": False,
                    "forced": force
                }
    def list_analyses(self) -> List[Dict[str, Any]]:
        """
        Devuelve el historial de análisis consultando directamente al DBManager.
        """
        return self.db.list_analyses()
