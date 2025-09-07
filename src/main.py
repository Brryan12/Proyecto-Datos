import pygame
from api.ManejadorAPI import ManejadorAPI
import json
from pathlib import Path
from models.CityMap import CityMap

def main():
    # --- Configuración ---
    TILE_WIDTH = 40
    TILE_HEIGHT = 44

    # Colores para cualquier tile que no tenga sprite asignado
    TILE_COLORS = {
        "default": (150, 150, 150)  # Gris
    }

    # --- Rutas base ---
    BASE_DIR = Path(__file__).resolve().parent  # Carpeta donde está este main.py
    CACHE_DIR = BASE_DIR / "cache"
    SPRITES_DIR = BASE_DIR / "sprites"

    # --- Cargar datos del mapa ---
    with open(CACHE_DIR / "map.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    city_map = CityMap(**data)

    # --- Inicializar Pygame ---
    pygame.init()
    screen = pygame.display.set_mode(
        (city_map.width * TILE_WIDTH, city_map.height * TILE_HEIGHT)
    )
    pygame.display.set_caption(city_map.city_name)

    clock = pygame.time.Clock()

    # --- Función para cargar y escalar sprites ---
    def cargar_sprite(nombre_archivo):
        ruta = SPRITES_DIR / nombre_archivo
        imagen = pygame.image.load(ruta).convert_alpha()
        return pygame.transform.scale(imagen, (TILE_WIDTH, TILE_HEIGHT))

    # --- Cargar sprites ---
    sprite_B = cargar_sprite("Spr_edificio1.png")
    sprite_C = cargar_sprite("Spr_acera.png")
    sprite_P = cargar_sprite("Spr_parque.png")

    # --- Bucle principal ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))

        for y, fila in enumerate(city_map.tiles):
            for x, code in enumerate(fila):
                rect = pygame.Rect(
                    x * TILE_WIDTH,
                    y * TILE_HEIGHT,
                    TILE_WIDTH,
                    TILE_HEIGHT
                )

                if code == "B":
                    screen.blit(sprite_B, rect.topleft)
                elif code == "C":
                    screen.blit(sprite_C, rect.topleft)
                elif code == "P":
                    screen.blit(sprite_P, rect.topleft)
                else:
                    color = TILE_COLORS.get(code, TILE_COLORS["default"])
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (50, 50, 50), rect, 1)  # Borde

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()

