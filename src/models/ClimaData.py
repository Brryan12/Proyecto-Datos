from typing import List, Dict
from pydantic import BaseModel
from .CondicionClima import CondicionClima

class ClimaData(BaseModel):
    city: str
    initial: CondicionClima
    conditions: List[str]
    transition: Dict[str, Dict[str, float]]