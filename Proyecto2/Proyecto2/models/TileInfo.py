from typing import List, Dict, Optional
from pydantic import BaseModel


class TileInfo(BaseModel):
    name: str
    surface_weight: Optional[float] = None
    blocked: Optional[bool] = None
    x: Optional[int] = None
    y: Optional[int] = None
    codigo: Optional[str] = None
    