import pygame
import json
from pathlib import Path
from src.models.CityMap import CityMap
from src.game.map_rend import MapRenderer
from src.game.stats_module import Stats
from src.game.reputation import Reputation
from src.game.player import Player


def test_reputation():
    print("=== PRUEBAS DE REPUTATION ===")
    rep = Reputation()

    print("Inicial:", rep.valor, rep.obtener_multiplicador_pago())

    rep.registrar_entrega("a_tiempo")
    print("Tras entrega a tiempo:", rep.valor)

    rep.valor = 85
    print("Bono aplicado?:", rep.obtener_multiplicador_pago())

    rep.registrar_entrega("tarde")
    print("Tras tardanza mitigada:", rep.valor)

    rep.registrar_entrega("tarde")
    print("Tras tardanza normal:", rep.valor)

    rep.valor = 15
    print("Derrota?:", rep.derrotado())


def test_stats():
    print("=== PRUEBAS DE STATS ===")
    s = Stats()

    print("Inicial:", s.resistencia, s.estado_actual(), s.puede_moverse())

    consumo = s.consume_por_mover(celdas=1, peso_total=2, condicion_clima="clear")
    print("Mover 1 celda clear, peso 2 -> consumo", consumo, "Resistencia:", s.resistencia)

    consumo = s.consume_por_mover(celdas=1, peso_total=6, condicion_clima="rain")
    print("Mover 1 celda lluvia, peso 6 -> consumo", consumo, "Resistencia:", s.resistencia)

    s.consume_por_mover(celdas=200, peso_total=1, condicion_clima="storm")
    print("Tras tormenta:", s.resistencia, s.estado_actual(), s.puede_moverse())

    s.recupera(segundos=3, rest_point=False)
    print("Tras 3s idle:", s.resistencia, s.estado_actual(), s.puede_moverse())

    s.recupera(segundos=2, rest_point=True)
    print("Tras 2s rest:", s.resistencia, s.estado_actual(), s.puede_moverse())



def main():
    print("Iniciando Courier Quest...")
    TILE_WIDTH = 20
    TILE_HEIGHT = 20

    BASE_DIR = Path(__file__).resolve().parent
    CACHE_DIR = BASE_DIR / "cache"
    SPRITES_DIR = BASE_DIR / "sprites"

    # cargar mapa
    with open(CACHE_DIR / "map.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    city_map = CityMap(**data)
    print("Mapa cargado:", city_map.city_name, city_map.width, city_map.height)

    pygame.init()

    font = pygame.font.SysFont("Arial", 20)

    WINDOW_WIDTH = 605
    WINDOW_HEIGHT = 605
    screen = pygame.display.set_mode(
        ((WINDOW_WIDTH, WINDOW_HEIGHT))
    )
    pygame.display.set_caption(city_map.city_name)
    clock = pygame.time.Clock()

    renderer = MapRenderer(city_map, SPRITES_DIR, TILE_WIDTH, TILE_HEIGHT)

    stats = Stats()
    rep = Reputation()
    player = Player(SPRITES_DIR, stats, rep)  # ✅ ahora sí después del display
    print("Sprite inicial cargado:", player.image)
    print("Rect inicial:", player.rect.topleft)

    player.mover("up")
    print("Movido arriba:", player.rect.topleft)

    player.mover("right")
    print("Movido derecha:", player.rect.topleft)

    running = True
    print("Entrando al loop principal...")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # input simple para mover al jugador
        keys = pygame.key.get_pressed()
        moved = False
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player.mover("up")
            moved = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player.mover("down")
            moved = True
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player.mover("izq")
            moved = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player.mover("der")
            moved = True

        if not moved:
            player.stats.recupera(segundos = 0.60, rest_point = False)

        screen.fill((0, 0, 0))
        renderer.draw(screen)
        screen.blit(player.image, player.rect)
        hud_text = f"Resistencia: {player.stats.resistencia: .1f} | Estado: {player.stats.estado_actual()} | Reputacion: {player.reputation.valor}"
        hud_surface = font.render(hud_text, True, (255, 255, 255))
        screen.blit(hud_surface, (10,10))

        pygame.display.flip()
        clock.tick(60)

    print("Saliendo del juego.")
    pygame.quit()


# -------------------
# EJECUCIÓN
# -------------------
if __name__ == "__main__":
    test_reputation()
    test_stats()
    main()

    