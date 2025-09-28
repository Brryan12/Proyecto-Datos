from pydantic import BaseModel
from .ClimaData import ClimaData

class ResultadoClima(BaseModel):
    version: str
    data: ClimaData