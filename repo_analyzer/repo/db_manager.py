import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import ConfigSingleton

class DBManager:
    """
    Responsabilidad: persistir y consultar análisis (SQLite). API simple.
    """

    def __init__(self):
        # Configuración inicial (necesaria para saber dónde está la BD)
        self.db_path = ConfigSingleton.get_instance().db_path
        # Aseguramos que el directorio existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Inicializamos la BD al arrancar
        self.init_db()

    def init_db(self):
        """Crea tablas si hacen falta."""
        conn = sqlite3.connect(str(self.db_path))  # Se conecta a la ruta definida
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_url TEXT,
                analyzed_at TEXT,
                result_json TEXT
            );
        """)
        conn.commit()
        conn.close()

    def save_analysis(self, result: dict) -> None:
        """Guarda el resultado del análisis en la base de datos como JSON."""
        # Prepara datos: URL, fecha y serialización a JSON
        repo_url = result.get("repo", "unknown")
        analyzed_at = result.get("analyzed_at", datetime.now().isoformat())
        result_json = json.dumps(result)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        # Inserta registro en la tabla analyses
        cursor.execute("""  
            INSERT INTO analyses (repo_url, analyzed_at, result_json)
            VALUES (?, ?, ?)
        """, (repo_url, analyzed_at, result_json))
        conn.commit()
        conn.close()

    def get_latest_analysis(self, repo_url: str) -> dict | None:
        """Devuelve los datos del repositorio (o None) si no se ha analizado anteriormente."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        # Selecciona el último análisis basado en la fecha
        cursor.execute("""
            SELECT result_json FROM analyses
            WHERE repo_url = ?
            ORDER BY analyzed_at DESC
            LIMIT 1
        """, (repo_url,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])  # Deserializa JSON a diccionario Python
        return None

    def list_analyses(self, limit: int = 50) -> list:
        """Lista el historial de análisis (solo resúmenes) ordenados por fecha."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT repo_url, analyzed_at, result_json 
            FROM analyses
            ORDER BY analyzed_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        history = []
        for repo_url, analyzed_at, json_str in rows:
            try:
                data = json.loads(json_str)
                # Extraemos solo el resumen para la lista
                summary = data.get("summary", {})
                history.append({
                    "repo": repo_url,
                    "analyzed_at": analyzed_at,
                    "summary": summary
                })
            except:
                continue
        return history