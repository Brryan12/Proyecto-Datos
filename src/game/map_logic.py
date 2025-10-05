from typing import Tuple, Optional
from src.models.CityMap import CityMap
from src.models.TileInfo import TileInfo


class MapLogic:
    
    def __init__(self, city_map: CityMap, tile_width: int, tile_height: int):
        self.city_map = city_map
        self.tile_width = tile_width
        self.tile_height = tile_height
        
        # Cache para optimizar consultas frecuentes
        self._tile_cache = {}
        
    def is_blocked(self, tile_x: int, tile_y: int) -> bool:
        # Verificar límites del mapa
        if tile_x < 0 or tile_y < 0 or tile_x >= self.city_map.width or tile_y >= self.city_map.height:
            return True
        
        try:
            # Obtener información del tile
            tile_info = self.get_tile_info(tile_x, tile_y)
            
            # Si el tile está explícitamente marcado como bloqueado
            if tile_info.blocked == True:
                return True
                
            # Si es un edificio, siempre bloqueado
            if tile_info.name == "building":
                return True
                
            # Parques: caminables en este juego
            if tile_info.name == "park":
                return False
                
            # Calles siempre caminables
            if tile_info.name == "street":
                return False
                
            # Por defecto, si no sabemos qué es, lo consideramos bloqueado
            return True
        
        except (IndexError, AttributeError):
            # Seguridad adicional para errores de índice o atributos
            return True
    
    def get_tile_info(self, tile_x: int, tile_y: int) -> Optional[TileInfo]:
        # Verificar límites
        if tile_x < 0 or tile_y < 0 or tile_x >= self.city_map.width or tile_y >= self.city_map.height:
            return None
            
        try:
            # Usar cache para optimizar consultas repetidas
            cache_key = (tile_x, tile_y)
            if cache_key in self._tile_cache:
                return self._tile_cache[cache_key]
            
            # Obtener código del tile y su información
            tile_code = self.city_map.tiles[tile_y][tile_x]
            tile_info = self.city_map.legend.get(tile_code)
            
            # Guardar en cache
            self._tile_cache[cache_key] = tile_info
            
            return tile_info
            
        except (IndexError, KeyError):
            return None

    
    def pixels_to_tiles(self, pixel_x: float, pixel_y: float) -> Tuple[int, int]:

        tile_x = int(pixel_x // self.tile_width)
        tile_y = int(pixel_y // self.tile_height)
        return tile_x, tile_y
    
    def tiles_to_pixels(self, tile_x: int, tile_y: int) -> Tuple[int, int]:

        pixel_x = tile_x * self.tile_width
        pixel_y = tile_y * self.tile_height
        return pixel_x, pixel_y

    
    def get_player_tile_pos(self, player_rect) -> Tuple[int, int]:

        center_x, center_y = player_rect.center
        return self.pixels_to_tiles(center_x, center_y)
    

