import pygame
import json
from pathlib import Path
from src.models.CityMap import CityMap
from src.game.map_rend import MapRenderer


def main():
    print("Iniciando Courier Quest...")
    TILE_WIDTH = 40
    TILE_HEIGHT = 44

    BASE_DIR = Path(__file__).resolve().parent
    CACHE_DIR = BASE_DIR / "cache"
    SPRITES_DIR = BASE_DIR / "sprites"

    with open(CACHE_DIR / "map.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    city_map = CityMap(**data)

    print("Mapa cargado:", city_map.city_name, city_map.width, city_map.height)

    pygame.init()
    screen = pygame.display.set_mode(
        (city_map.width * TILE_WIDTH, city_map.height * TILE_HEIGHT)
    )
    pygame.display.set_caption(city_map.city_name)
    clock = pygame.time.Clock()

    renderer = MapRenderer(city_map, SPRITES_DIR, TILE_WIDTH, TILE_HEIGHT)

    running = True
    print("Entrando al loop principal...")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        renderer.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    print("Saliendo del juego.")
    pygame.quit()


if __name__ == "__main__":
    main()

