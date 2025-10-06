from typing import List, Dict
from pydantic import BaseModel
from .CondicionClima import CondicionClima


#Trabaja el nombre de la ciudad, la condición inicial del clima, las condiciones disponibles y la transición entre climas, que debe aplicarse en otro archivo la cadena de markov.
class ClimaData(BaseModel):
    city: str
    initial: CondicionClima
    conditions: List[str]
    transition: Dict[str, Dict[str, float]]
