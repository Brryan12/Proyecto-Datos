from pydantic import BaseModel 
from typing import Optional, Tuple, List, Dict 
import json 
from pathlib import Path 
import uuid # Para generar IDs únicos 

SAVE_DIR = Path(__file__).resolve().parent / "saves" 
SAVE_FILE = SAVE_DIR / "save.json" 

class Save(BaseModel): 
    player_name: str = "Jugador" 
    city_name: str = "TigerCity" 
    day: int = 1 
    score: int = 0 
    reputation: float = 70.0 
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
        print(f"[SAVE] Juego guardado en {file_path}")
        return save_id

    @classmethod 
    def load_from_file(cls): 
        """Carga todos los guardados válidos desde la carpeta saves"""
        SAVE_DIR.mkdir(exist_ok=True)
        saves = []
        for f in SAVE_DIR.glob("*.json"):
            try:
                if f.stat().st_size == 0:
                    print(f"[WARN] {f} está vacío, se ignorará")
                    continue
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                saves.append(cls(**data))
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"[WARNING] No se pudo cargar {f}: {e}")
        return saves