from pathlib import Path
from typing import Optional

class ConfigSingleton:
    _instance: Optional["ConfigSingleton"] = None  # <--- CORRECCIÓN CRÍTICA: Inicializar a None

    def __init__(self,
                 repo_cache_dir: Path | str,
                 db_path: Path | str,
                 duplication_window: int):
        
        if ConfigSingleton._instance is not None:
            raise TypeError("Esta clase es un Singleton. Usa `get_instance()`.")
        
        self.repo_cache_dir = Path(repo_cache_dir)
        self.db_path = Path(db_path)
        self.duplication_window = duplication_window

    @staticmethod
    def get_instance() -> "ConfigSingleton":
        """Obtiene la instancia única (Lazy Initialization)."""
        if ConfigSingleton._instance is None:
            ConfigSingleton._instance = ConfigSingleton(
                repo_cache_dir=Path.cwd() / "repo_cache", # He quitado "_dir" redundante
                db_path=Path.cwd() / "analysis.db",       # Mejor extensión .db y sin espacios
                duplication_window=5,
            )
        return ConfigSingleton._instance
    
    def as_dict(self) -> dict:
        return {
            "repo_cache_dir": str(self.repo_cache_dir),
            "db_path": str(self.db_path),
            "duplication_window": self.duplication_window
        }
