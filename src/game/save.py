from pydantic import BaseModel 
from typing import Optional, Tuple, List, Dict 
import json 
from pathlib import Path 
import uuid # Para generar IDs únicos 

SAVE_DIR = Path(__file__).resolve().parent.parent.parent / "cache" 
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
    
    def save_to_file(self): 
        """Guarda el estado actual del juego""" 
        SAVE_DIR.mkdir(exist_ok=True) 
        
        with open(SAVE_FILE, "w", encoding="utf-8") as f: 
            json.dump(self.dict(), f, indent=4, ensure_ascii=False) 
            print(f"[SAVE] Juego guardado en {SAVE_FILE}") 
            
    @classmethod 
    def load_from_file(cls): 
        """Carga el estado desde el archivo JSON""" 
        if not SAVE_FILE.exists(): 
                    print("[SAVE] No existe archivo de guardado. Creando nuevo.") 
                    data = cls() 
                    data.save_to_file() 
                    return data 
                
        try: 
                    with open(SAVE_FILE, "r", encoding="utf-8") as f: 
                        raw_data = json.load(f) 
                    
                    # --- Validación y conversión segura de posición --- 
                    pos = raw_data.get("position", [0, 0]) 
                    try: 
                        x, y = int(float(pos[0])), int(float(pos[1])) 
                    
                    except Exception: 
                        x, y = 0, 0 
                    
                    raw_data["position"] = (x, y) 
                    print("[SAVE] Archivo de guardado cargado correctamente.") 
                    return cls(**raw_data) 
        except Exception as e: 
                    print(f"[SAVE ERROR] No se pudo cargar el archivo: {e}") 
                    return cls()                     
     
    