import subprocess
import shutil
from pathlib import Path
from urllib.parse import urlparse
from config import ConfigSingleton 

class RepoManager:
    """
    Gestiona la clonación, disponibilidad local y limpieza de repositorios de GitHub.
    """
    
    def __init__(self):
        self.config = ConfigSingleton.get_instance()  # Obtiene la configuración Singleton
        self.cache_dir = self.config.repo_cache_dir
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)  # Asegurarse de que el directorio de caché exista

    def _get_local_path(self, repo_url: str) -> Path:
        """
        Genera la ruta local segura para un repositorio basado en su URL.
        """
        # Extraer el nombre del repositorio a partir de la URL (ej: "user/repo.git")
        # Esto simplifica la URL para usarla como nombre de subdirectorio.
        try:
            parsed_url = urlparse(repo_url)
            repo_name = parsed_url.path.strip('/').replace('.git', '')
            
            if not repo_name:
                raise ValueError("URL de repositorio no válida.")
                
            return self.cache_dir / repo_name.lower()
        
        except Exception:  # En caso de URL malformada, usar un hash o un nombre genérico
            import hashlib
            name_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:10]
            return self.cache_dir / name_hash

    def is_cloned(self, repo_url: str) -> bool:
        """
        Comprueba si el repositorio ya ha sido clonado y está disponible en disco.
        """
        local_path = self._get_local_path(repo_url)
        # Se considera clonado si el directorio existe y no está vacío (o contiene .git)
        return local_path.is_dir() and any(local_path.iterdir())

    def remove_repo(self, repo_path: Path) -> None:
        """
        Borra el directorio del repositorio local (usado para forzar recálculo).
        """
        if repo_path.is_dir():
            print(f"Eliminando repositorio local en: {repo_path}")
            shutil.rmtree(repo_path)  # Elimina directorios con contenido
        else:
            print(f"Advertencia: El directorio {repo_path} no existe o no es un directorio.")

    def ensure_repo(self, repo_url: str) -> Path:
        """
        Asegura que el repositorio indicado esté disponible localmente y lo clona si no existe.
        Devuelve el Path al directorio local del repositorio.
        """
        local_path = self._get_local_path(repo_url)

        if self.is_cloned(repo_url):
            print(f"Repositorio ya clonado en: {local_path}. Saltando clonación.")
            return local_path

        print(f"Clonando {repo_url} en {local_path}...")  # Si no está clonado, lo clona

        
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)  # Crea el directorio padre si no existe
            
            # Comando git clone
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(local_path)], 
                check=True,  # Lanza una excepción si el comando falla (ej: repo no existe, no hay git)
                capture_output=True, 
                text=True
            )
            print("Clonación completada con éxito.")
            return local_path
            
        except subprocess.CalledProcessError as e:
            # Fallo en la clonación (URL incorrecta, error de conexión, etc.)
            print(f"ERROR: Fallo al clonar el repositorio {repo_url}.")
            print(f"Git Stderr: {e.stderr}")
            if local_path.exists():
                shutil.rmtree(local_path)  # Limpia el directorio parcial si fue creado
            raise ConnectionError(f"No se pudo clonar el repositorio: {repo_url}") from e
        
        except FileNotFoundError as e:
            # Fallo si "git" no está en el PATH del sistema
            print(f"ERROR: El comando 'git' no fue encontrado. Asegúrate de que Git está instalado y accesible en el PATH.")
            raise EnvironmentError("Git no está disponible en el sistema.") from e