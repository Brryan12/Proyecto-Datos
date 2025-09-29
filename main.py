import pygame
import json
from pathlib import Path
from src.models.CityMap import CityMap
from src.game.map_rend import MapRenderer

import time

from src.game.stats_module import Stats

from src.game.reputation import Reputation

def test_reputation():
    rep = Reputation()

    print("Inicial:", rep.valor, rep.obtener_multiplicador_pago())

    # entregar a tiempo
    rep.registrar_entrega("a_tiempo")
    print("Tras entrega a tiempo:", rep.valor)

    # subir a >=85 y ver bono
    rep.valor = 85
    print("Bono aplicado?:", rep.obtener_multiplicador_pago())

    # entrega tardía con mitigación
    rep.registrar_entrega("tarde")
    print("Tras tardanza mitigada:", rep.valor)

    # entrega tardía sin mitigación
    rep.registrar_entrega("tarde")
    print("Tras tardanza normal:", rep.valor)

    # bajar a derrota
    rep.valor = 15
    print("Derrota?:", rep.derrotado())


def test_stats():
    s = Stats()

    print("=== PRUEBAS DE STATS ===")

    # Estado inicial
    print("Inicial:", s.resistencia, s.estado_actual(), s.puede_moverse())

    # 1) Moverse 1 celda con peso 2 (clear)
    consumo = s.consume_por_mover(celdas=1, peso_total=2, condicion_clima="clear")
    print("Mover 1 celda clear, peso 2 -> consumo", consumo, "Resistencia:", s.resistencia)

    # 2) Moverse 1 celda con peso 6 (rain)
    consumo = s.consume_por_mover(celdas=1, peso_total=6, condicion_clima="rain")
    print("Mover 1 celda lluvia, peso 6 -> consumo", consumo, "Resistencia:", s.resistencia)

    # 3) Agotarlo con tormenta
    s.consume_por_mover(celdas=200, peso_total=1, condicion_clima="storm")
    print("Tras tormenta:", s.resistencia, s.estado_actual(), s.puede_moverse())

    # 4) Recuperar 3 segundos sin descanso
    s.recupera(segundos=3, rest_point=False)
    print("Tras 3s idle:", s.resistencia, s.estado_actual(), s.puede_moverse())

    # 5) Recuperar 2 segundos en descanso
    s.recupera(segundos=2, rest_point=True)
    print("Tras 2s rest:", s.resistencia, s.estado_actual(), s.puede_moverse())



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
    test_reputation()
    main()

