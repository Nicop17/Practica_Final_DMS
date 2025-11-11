from pathlib import Path

class ConfigSingleton:
    _instance: "ConfigSingleton" #La instancia única que se puede tener de esta clase
    #Se supone que el constructor es privado
    def __init__(self,
                 repo_cache_dir: Path | str, #directorio local donde se descargan repos.
                 db_path: Path | str, #ruta del fichero SQLite.
                 duplication_window: int): #valor por defecto para duplicación.
        
        if ConfigSingleton._instance is not None:
                raise TypeError("Esta clase es un Singleton. Usa `get_instance()` para obtener la instancia.")
        self.repo_cache_dir = Path(repo_cache_dir)
        self.db_path = Path(db_path)
        self.duplication_window = duplication_window


    @staticmethod
    def get_instance():
        """
        obtiene la instancia única.
        """
        if ConfigSingleton._instance == None:
            ConfigSingleton._instance = ConfigSingleton(
                repo_cache_dir = Path.cwd() / "repo_cache_dir",
                db_path = Path.cwd() / "Base de datos",
                duplication_window = 5,
            )
        return ConfigSingleton._instance
    
    def as_dict(self) -> dict: #para debug
        """
        Devuelve la configuración como un diccionario (para debug o serialización).
        
        Añadimos 'self' como primer argumento para que sea un método de instancia.
        """
        return {
            # Convertimos las rutas (objetos Path) a strings para facilitar la lectura
            "repo_cache_dir": str(self.repo_cache_dir),
            "db_path": str(self.db_path),
            "duplication_window": self.duplication_window
        }
