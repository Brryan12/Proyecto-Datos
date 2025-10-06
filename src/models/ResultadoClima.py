from pydantic import BaseModel
from .ClimaData import ClimaData

class ResultadoClima(BaseModel):
    version: str #Recoge la información de la versión del API
    data: ClimaData #Envuelve los datos del clima del ClimaData.
