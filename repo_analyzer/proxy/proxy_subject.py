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

    def peticion(self, repo_url: str, force: bool = False, options: dict = None) -> dict:
        # 1. Definir la ruta antes que nada
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        local_path = self.cache_dir / repo_name

        # 2. Si es 'force', borrar el disco ANTES de intentar descargar
        if force:
            self.repo_manager.remove_repo(local_path)
        
        # 3. Si no es 'force', intentar caché
        elif not force:
            cached = self.db.get_latest_analysis(repo_url)
            if cached:
                cached["_from_cache"] = True
                return cached

        # 4. Ahora sí, descargar y analizar
        # ensure_repo encontrará la carpeta vacía y clonará de cero
        actual_path = self.repo_manager.ensure_repo(repo_url)
        result = self.facade.compute_all(actual_path, options or {})
        
        # ... guardar en DB y retornar ...
        self.db.save_analysis(result)
        result["_from_cache"] = False
        return result

    def list_analyses(self) -> List[Dict[str, Any]]:
        return self.db.list_analyses()
