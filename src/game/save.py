from pydantic import BaseModel 
from typing import Optional, Tuple, List, Dict 
import json 
from pathlib import Path 
import uuid # Para generar IDs únicos 

SAVE_DIR = Path(__file__).resolve().parent / "saves" 
SAVE_FILE = SAVE_DIR / "save.json" 

SAVE_SCORES = SAVE_DIR / "saveScores.json"

class Save(BaseModel): 
    player_name: Optional[str] = None 
    city_name: str = "TigerCity" 
    day: Optional[int] = None 
    score: Optional[int] = 0 
    reputation: Optional[float] = 0.0 
    position: Tuple[int, int] = (0, 0) 
    completed_jobs: List[str] = [] 
    current_weather: Optional[str] = None 
    
    def save_to_file(self) -> str: 
        """Guarda el estado actual y devuelve un ID único."""
        SAVE_DIR.mkdir(exist_ok=True)
        save_id = str(uuid.uuid4())
        file_path = SAVE_DIR / f"{save_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4, ensure_ascii=False)

        return save_id

    @classmethod 
    def load_from_file(cls): 
        """Carga todos los guardados válidos desde la carpeta saves"""
        SAVE_DIR.mkdir(exist_ok=True)
        saves = []
        for f in SAVE_DIR.glob("*.json"):
            try:
                # Ignorar el archivo de scores ya que tiene un formato diferente
                if f.name == "savedScores.json":
                    continue
                    
                if f.stat().st_size == 0:
                    print(f"[WARNING] {f} está vacío, se ignorará")
                    continue
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                saves.append(cls(**data))
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"[WARNING] No se pudo cargar {f}: {e}")
        return saves
    
    @classmethod
    def save_score_only_global(self):
        """Guarda o actualiza el score del jugador en savedScores.json"""
        self.SAVE_SCORES.mkdir(exist_ok=True)
        
        # Cargar scores existentes
        scores = {}
        if self.SAVE_SCORES.exists():
            try:
                with open(self.SAVE_SCORES, "r", encoding="utf-8") as f:
                    scores = json.load(f)
            except json.JSONDecodeError:
                scores = {}
        
        # Actualizar o agregar el score del jugador
        if self.player_name:
            scores[self.player_name] = self.score
        
        # Guardar nuevamente
        with open(self.SAVE_SCORES, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=4, ensure_ascii=False)
        
        return str(self.SAVE_SCORES)
    
    @classmethod
    def get_ranking(cls, top_n: int = 10) -> list[tuple[str, int]]:
        """Devuelve un ranking de jugadores ordenado por score descendente.
        
        Args:
            top_n: número máximo de jugadores a mostrar.
        
        Returns:
            Lista de tuplas (nombre, score) ordenadas de mayor a menor score.
        """
        if not cls.SAVE_SCORES.exists():
            return []

        try:
            with open(cls.SAVE_SCORE, "r", encoding="utf-8") as f:
                scores = json.load(f)
        except json.JSONDecodeError:
            return []

        # Ordenar por score descendente
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_n]