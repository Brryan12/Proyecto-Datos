import pygame
import json
from pathlib import Path
from src.models.CityMap import CityMap
from src.models.ClimaData import ClimaData
from src.game.map_rend import MapRenderer
from src.game.stats_module import Stats
from src.game.reputation import Reputation
from src.game.player import Player
from src.game.weather_system import SistemaClima


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
    TILE_WIDTH = 26
    TILE_HEIGHT = 20

    BASE_DIR = Path(__file__).resolve().parent
    CACHE_DIR = BASE_DIR / "cache"
    SPRITES_DIR = BASE_DIR / "sprites"
    try:
        with open(CACHE_DIR / "map.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        city_map = CityMap(**data)
        print("Mapa cargado:", city_map.city_name, city_map.width, city_map.height)
    except Exception as e:
        print(f"Error cargando mapa: {e}")
        return

    try:
        with open(CACHE_DIR / "TigerCity_weather.json", "r", encoding="utf-8") as f:
            clima_data = json.load(f)
        clima = ClimaData(**clima_data)
        sistema_clima = SistemaClima(clima)
    except Exception as e:
        print(f"Error cargando clima: {e}")
        return

    pygame.init()
    font = pygame.font.SysFont("Arial", 20)
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(city_map.city_name)
    clock = pygame.time.Clock()

    # --- inicializar entidades ---
    renderer = MapRenderer(city_map, SPRITES_DIR, TILE_WIDTH, TILE_HEIGHT, viewport_size=(WINDOW_WIDTH, WINDOW_HEIGHT))
    stats = Stats()
    rep = Reputation()
    player = Player(SPRITES_DIR, stats, rep, TILE_WIDTH, TILE_HEIGHT)

    def is_blocked(x, y):
        if x < 0 or y < 0 or x >= city_map.width or y >= city_map.height:
            return True
        tile_code = city_map.tiles[y][x]
        tile_info = city_map.legend.get(tile_code)
        if tile_info and tile_info.blocked:
            return True
        return False

    def player_tile_pos():
        # Calculate player's tile position based on pixel position and tile size
        return player.x // TILE_WIDTH, player.y // TILE_HEIGHT

    running = True
    print("Entrando al loop principal...")
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # actualizar clima
        sistema_clima.actualizar()
        condicion = sistema_clima.obtener_condicion()
        intensidad = sistema_clima.obtener_intensidad()
        efectos = sistema_clima.obtener_efectos()

        keys = pygame.key.get_pressed()
        moved = False
        px, py = player_tile_pos()
        new_x, new_y = px, py

        if keys[pygame.K_UP]:
            new_x, new_y = px, py - 1
            if not is_blocked(new_x, new_y):
                player.mover("up", clima=condicion)
                moved = True
        elif keys[pygame.K_DOWN]:
            new_x, new_y = px, py + 1
            if not is_blocked(new_x, new_y):
                player.mover("down", clima=condicion)
                moved = True
        elif keys[pygame.K_LEFT]:
            new_x, new_y = px - 1, py
            if not is_blocked(new_x, new_y):
                player.mover("izq", clima=condicion)
                moved = True
        elif keys[pygame.K_RIGHT]:
            new_x, new_y = px + 1, py
            if not is_blocked(new_x, new_y):
                player.mover("der", clima=condicion)
                moved = True

        if not moved:
            player.stats.recupera(segundos=dt, rest_point=False)



        # dibujar
        screen.fill((0, 0, 0))
        renderer.draw(screen)
        player.draw(screen)

        # HUD con estado del jugador y clima (multi-line)
        hud_lines = [
            f"Resistencia: {player.stats.resistencia:.1f} | Estado: {player.stats.estado_actual()}",
            f"Reputacion: {player.reputation.valor} | Clima: {condicion} ({intensidad:.2f})",
            f"Vel={efectos['factor_velocidad']:.2f} ResPen={efectos['penalizacion_resistencia']:.2f}"
        ]
        for i, line in enumerate(hud_lines):
            hud_surface = font.render(line, True, (255, 255, 255))
            screen.blit(hud_surface, (10, 10 + i * 22))

        pygame.display.flip()

    print("Saliendo del juego.")
    pygame.quit()


if __name__ == "__main__":
    test_reputation()
    test_stats()
    main()

    