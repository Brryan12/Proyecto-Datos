import pygame
import json
from pathlib import Path
from src.models.CityMap import CityMap
from src.game.map_rend import MapRenderer

from src.game.statistics import Stats
import time

def test_stats():
    print("=== PRUEBA DEL SISTEMA DE RESISTENCIA ===")
    stats = Stats()

    print("\nInicial:")
    print(f"Resistencia={stats.resistencia}, Estado={stats.estado_actual()}, Factor={stats.factor_velocidad()}, Puede mover={stats.puede_moverse()}")

    # Movimiento con poco peso y clima normal
    consumo = stats.consume_por_mover(celdas=5, peso_total=2, condicion_clima="clear")
    print(f"\nTras mover 5 celdas (peso 2, clear): consumió {consumo}, resistencia={stats.resistencia}, estado={stats.estado_actual()}, factor={stats.factor_velocidad()}, puede mover={stats.puede_moverse()}")

    # Movimiento con sobrepeso y lluvia
    consumo = stats.consume_por_mover(celdas=3, peso_total=6, condicion_clima="rain")
    print(f"\nTras mover 3 celdas (peso 6, rain): consumió {consumo}, resistencia={stats.resistencia}, estado={stats.estado_actual()}, factor={stats.factor_velocidad()}, puede mover={stats.puede_moverse()}")

    # Agotarlo con tormenta
    consumo = stats.consume_por_mover(celdas=50, peso_total=1, condicion_clima="storm")
    print(f"\nTras mover 50 celdas (storm): consumió {consumo}, resistencia={stats.resistencia}, estado={stats.estado_actual()}, factor={stats.factor_velocidad()}, puede mover={stats.puede_moverse()}")

    # Recuperación estando quieto
    print("\nEsperando 3 segundos para recuperación (quieto)...")
    time.sleep(3)
    stats.recupera(segundos=3, rest_point=False)
    print(f"Resistencia={stats.resistencia}, Estado={stats.estado_actual()}, Factor={stats.factor_velocidad()}, Puede mover={stats.puede_moverse()}")

    # Recuperación en punto de descanso
    print("\nEsperando 3 segundos en punto de descanso...")
    time.sleep(3)
    stats.recupera(segundos=3, rest_point=True)
    print(f"Resistencia={stats.resistencia}, Estado={stats.estado_actual()}, Factor={stats.factor_velocidad()}, Puede mover={stats.puede_moverse()}")
    print("=== FIN DE PRUEBA ===")



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
    test_stats()
    main()

