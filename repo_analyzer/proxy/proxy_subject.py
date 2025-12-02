from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Dependencias del sistema
from config import ConfigSingleton
from repo.repo_manager import RepoManager
from repo.db_manager import DBManager
from metrics.facade import MetricsFacade

# Interfaz que implementa este Proxy
from .interface import SubjectInterface

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
        Decide si leer de la BD o calcular de cero.
        """
        if options is None:
            options = {}

        try:
            # 1. CONSULTA DE CACHÉ
            # Si no se fuerza el análisis, intentamos recuperar de la BD
            if not force:
                cached_result = self.db.get_latest_analysis(repo_url)
                if cached_result:
                    print(f"[Proxy] HIT: Análisis recuperado de caché para {repo_url}")
                    return cached_result

            # 2. Calcular de cero (Si no está en la BD o force=True)
            print(f"[Proxy] MISS (o force): Iniciando análisis completo para {repo_url}")
            
            # Aseguramos que el repositorio esté descargado
            local_path = self.repo_manager.ensure_repo(repo_url)

            # Si force=True, borramos lo que hubiera y volvemos a descargar 
            # para garantizar que analizamos la versión más reciente del código
            if force:
                print("[Proxy] Limpiando copia local...")
                self.repo_manager.remove_repo(local_path)
                local_path = self.repo_manager.ensure_repo(repo_url)

            # Delegamos en la fachada el cálculo de las métricas
            print("[Proxy] Calculando métricas...")
            results = self.facade.compute_all(local_path, options)

            # Añadimos URL y fecha si faltan
            results["repo"] = repo_url
            if "analyzed_at" not in results:
                results["analyzed_at"] = datetime.now().isoformat()

            # D. Guardaamos el resultado en la BD (para futuros usos)
            self.db.save_analysis(results)
            
            return results

        except Exception as e:
            # Si algo falla (git, red, código), capturo el error            
            error_msg = f"Error procesando {repo_url}: {str(e)}"
            print(f"[Proxy Error] {error_msg}")
            
            # Devuelvemos un diccionario con el error para mostrarlo en la web
            return {
                "repo": repo_url,
                "analyzed_at": datetime.now().isoformat(),
                "error": error_msg,
                "summary": {"num_files": 0, "total_lines": 0}
            }

    def list_analyses(self) -> List[Dict[str, Any]]:
        """
        Devuelve el historial de análisis consultando directamente al DBManager.
        """
        return self.db.list_analyses()