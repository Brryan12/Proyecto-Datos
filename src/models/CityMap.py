from typing import List, Dict
from pydantic import BaseModel
from .TileInfo import TileInfo

class CityMap(BaseModel): #Se construyen con el basemodel de pydantic
    version: str
    city_name: str
    width: int
    height: int
    goal: int #Número de entregas del jugador
    max_time: int #Tiempo para completar las entregas
    tiles: List[List[str]] #Matriz del mapa
    legend: Dict[str, TileInfo]  #Mapea con TileInfo

    def iterar_elementos(self) -> List[TileInfo]:
        objetos = []
        for y, fila in enumerate(self.tiles): #y devuelve la coordenada vertical y fila las letras
            for x, code in enumerate(fila): #recorre cada elemento de la fila, siendo code el nombre
                info = self.legend.get(code) #self.legend mapea el codigo con la info que corresponde
                if info: 
                    objetos.append(TileInfo( #si no está vacío entonces se agrega el objeto de tipo TileInfo
                        name=info.name,
                        surface_weight=info.surface_weight,
                        blocked=info.blocked,
                        x=x,
                        y=y,
                        codigo=code
                    ))
        return objetos
