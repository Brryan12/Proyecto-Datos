import pygame
from pathlib import Path
from src.models.CityMap import CityMap

class MapRenderer:
    def __init__(self, city_map: CityMap, sprites_dir: Path, tile_width = 40, tile_height = 44):
        self.city_map = city_map
        self.sprites_dir = sprites_dir
        self.tile_width = tile_width
        self.tile_height = tile_height

        self.TILE_COLORS = {
            "default": (150, 150, 150)
        }

        self.sprites = {}
        self._cargar_sprites()
    
    def _cargar_sprite(self, filename: str) -> pygame.Surface   :
        ruta = self.sprites_dir / filename
        imagen = pygame.image.load(ruta).convert_alpha()
        return pygame.transform.scale(imagen, (self.tile_width, self.tile_height))
    
    def _cargar_sprites(self):
        self.sprites["B"] = self._cargar_sprite("Spr_edificio1.png")
        self.sprites["C"] = self._cargar_sprite("Spr_acera.png")
        self.sprites["P"] = self._cargar_sprite("Spr_parque.png")

    def draw(self, screen: pygame.Surface):

        for y, fila in enumerate(self.city_map.tiles):
            for x, code in enumerate(fila):
                rect = pygame.Rect(
                    x * self.tile_width,
                    y * self.tile_height,
                    self.tile_width,
                    self.tile_height
                )

                if code in self.sprites:
                    screen.blit(self.sprites[code], rect.topleft)
                else:
                    color = self.TILE_COLORS.get(code, self.TILE_COLORS["default"])
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (50,50,50), rect, 1)