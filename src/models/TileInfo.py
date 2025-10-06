from typing import List, Dict, Optional
from pydantic import BaseModel

#Describe cada uno de los tiles del mapa
class TileInfo(BaseModel):
    name: str
    surface_weight: Optional[float] = None #Determina si afecta el movimiento del jugador
    blocked: Optional[bool] = None #Considera la colisión de unidades
    x: Optional[int] = None
    y: Optional[int] = None
    codigo: Optional[str] = None #Sirve de base para identificar cuáles son calles, edificios y parques.
    
