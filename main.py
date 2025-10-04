# src/main.py
import sys
import pygame
import json
from pathlib import Path
from typing import List
from src.models.CityMap import CityMap
from src.models.ClimaData import ClimaData
from src.game.button import Button


# Intento de import seguro de ServicioPedidos (soporta dos ubicaciones comunes)
try:
    from src.models.pedidos_service import ServicioPedidos
except Exception:
    try:
        from src.models.pedidos_service import ServicioPedidos
    except Exception as e:
        raise ImportError(
            "No se pudo importar ServicioPedidos. Asegúrate de que el módulo exista en "
            "src/services/pedidos_service.py o src/models/pedidos_service.py"
        ) from e

from src.game.job_manager import GestorPedidos
from src.game.map_rend import MapRenderer
from src.game.map_logic import MapLogic
from src.game.stats_module import Stats
from src.game.reputation import Reputation
from src.game.player import Player
from src.game.weather_system import SistemaClima

# Inicializar pygame antes de usar cualquier función de pygame
pygame.init()

BG = pygame.image.load("./sprites/Background.png")

def get_font(size): # Returns Press-Start-2P in the desired size
    return pygame.font.Font("./sprites/font.ttf", size)

MAP_WIDTH = 605
MAP_HEIGHT = 605
HUD_WIDTH = 300
WINDOW_WIDTH = MAP_WIDTH + HUD_WIDTH
WINDOW_HEIGHT = MAP_HEIGHT
SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
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

def test_job_manager():
    print("=== PRUEBAS DE GESTOR DE PEDIDOS ===")
    from src.models.Pedido import PedidoSolicitud
    gestor = GestorPedidos()

    # Crear pedidos de prueba
    pedido1 = PedidoSolicitud(
        id="job1",
        pickup=[0, 0],
        dropoff=[1, 1],
        payout=100,
        duration=900,  # 15 minutes
        weight=5,
        priority=1,
        release_time=0
    )
    pedido2 = PedidoSolicitud(
        id="job2",
        pickup=[2, 2],
        dropoff=[3, 3],
        payout=200,
        duration=900,  # 15 minutes
        weight=10,
        priority=2,
        release_time=1
    )

    # Agregar pedidos
    gestor.agregar_pedido(pedido1)
    gestor.agregar_pedido(pedido2)
    print(f"Pedidos en cola: {len(gestor.ver_pedidos())}")

    # Ver pedidos
    pedidos = gestor.ver_pedidos()
    print(f"Primer pedido ID: {pedidos[0].id}")

    # Ordenar por duración
    ordenados_duracion = gestor.ordenar_por_duracion()
    print(f"Ordenados por duración: {[p.id for p in ordenados_duracion]}")

    # Ordenar por prioridad
    ordenados_prioridad = gestor.ordenar_por_prioridad()
    print(f"Ordenados por prioridad: {[p.id for p in ordenados_prioridad]}")

    # Obtener siguiente
    siguiente = gestor.obtener_siguiente()
    print(f"Siguiente pedido: {siguiente.id if siguiente else 'None'}")

    # Pedidos pendientes
    tiempo_actual = 500  # 500 seconds
    pendientes = gestor.pedidos_pendientes(tiempo_actual)
    print(f"Pedidos pendientes: {len(pendientes)}")

    # Pedidos vencidos
    vencidos = gestor.pedidos_vencidos(tiempo_actual)
    print(f"Pedidos vencidos: {len(vencidos)}")


def game():
    print("Iniciando Courier Quest...")
    TILE_WIDTH = 20
    TILE_HEIGHT = 20

    BASE_DIR = Path(__file__).resolve().parent
    CACHE_DIR = BASE_DIR / "cache"
    SPRITES_DIR = BASE_DIR / "sprites"

    # --- cargar mapa ---
    try:
        with open(CACHE_DIR / "map.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        city_map = CityMap(**data)
        print("Mapa cargado:", city_map.city_name, city_map.width, city_map.height)
    except Exception as e:
        print(f"Error cargando mapa: {e}")
        return

    # --- cargar clima ---
    try:
        with open(CACHE_DIR / "TigerCity_weather.json", "r", encoding="utf-8") as f:
            clima_data = json.load(f)
        clima = ClimaData(**clima_data)
        sistema_clima = SistemaClima(clima)
    except Exception as e:
        print(f"Error cargando clima: {e}")
        return

    # --- cargar pedidos (usa cache si existe; no forzar descarga por defecto) ---
    pedidos: List = []
    try:
        servicio_pedidos = ServicioPedidos(cache_dir=CACHE_DIR)
        # Usa cache si existe; si quieres forzar descarga pon force_update=True
        pedidos = servicio_pedidos.cargar_pedidos(force_update=False)
        print(f"Pedidos cargados desde cache/API: {len(pedidos)}")
    except FileNotFoundError as fnf:
        print("No se encontró jobs.json en cache y no se pudo descargar:", fnf)
    except Exception as e:
        print(f"Error cargando pedidos: {e}")

    # Poblamos GestorPedidos con lo cargado (si hay)
    gestor = GestorPedidos()
    for p in pedidos:
        gestor.agregar_pedido(p)



    pygame.display.set_caption(city_map.city_name)
    clock = pygame.time.Clock()

    # --- inicializar entidades ---
    renderer = MapRenderer(city_map, SPRITES_DIR, TILE_WIDTH, TILE_HEIGHT, viewport_size=(MAP_WIDTH, MAP_HEIGHT))
    map_logic = MapLogic(city_map, TILE_WIDTH, TILE_HEIGHT)
    stats = Stats()
    rep = Reputation()
    
    # Inicializar jugador con una posición específica en el mapa (por ejemplo, en el centro)
    # Multiplicamos por TILE_WIDTH/HEIGHT para convertir de coordenadas de tile a píxeles
    initial_tile_x = 15  # Ajustar según la posición inicial deseada
    initial_tile_y = 15  # Ajustar según la posición inicial deseada
    
    # Calcular la posición exacta para que el jugador esté centrado en la casilla usando MapLogic
    start_x, start_y = map_logic.tiles_to_pixels(initial_tile_x, initial_tile_y)
    
    player = Player(SPRITES_DIR, stats, rep, TILE_WIDTH, TILE_HEIGHT, 
                    start_x=start_x, 
                    start_y=start_y)



    # Demo: imprimir primeros 3 pedidos (info de duración)

    print("\n--- Demostración de uso de duración con pedidos ---")
    if pedidos:
        for pedido in pedidos[:3]:
            print(f"Pedido ID: {pedido.id}, Duración: {pedido.duration} segundos, Tipo: {type(pedido.duration)}")
        pedidos_ordenados = sorted(pedidos, key=lambda p: p.duration)
        print("Pedidos ordenados por duración (primeros 3):")
        for p in pedidos_ordenados[:3]:
            print(f"  {p.id} - {p.duration} s")
    else:
        print("No hay pedidos en cache.")
        

    # --- loop principal ---
    while True:
        dt = clock.tick(60) / 1000.0  # delta seconds        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # actualizar clima
        sistema_clima.actualizar()
        condicion = sistema_clima.obtener_condicion()
        intensidad = sistema_clima.obtener_intensidad()
        efectos = sistema_clima.obtener_efectos()

        # mover jugador
        keys = pygame.key.get_pressed()
        moved = False
        px, py = map_logic.get_player_tile_pos(player.rect)
        new_x, new_y = px, py

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= 1
            if not map_logic.is_blocked(new_x, new_y):
                # Obtener información del tile para surface_weight
                tile_info = map_logic.get_tile_info(new_x, new_y)
                
                # Obtener factor de clima desde sistema_clima
                clima_factor = efectos["factor_velocidad"]
                
                # Mover al jugador con todos los factores
                player.mover(
                    direccion="up", 
                    clima=condicion, 
                    clima_factor=clima_factor,
                    tile_info=tile_info,
                )
                moved = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += 1
            if not map_logic.is_blocked(new_x, new_y):
                tile_info = map_logic.get_tile_info(new_x, new_y)
                clima_factor = efectos["factor_velocidad"]
                player.mover(
                    direccion="down", 
                    clima=condicion, 
                    clima_factor=clima_factor,
                    tile_info=tile_info,
                )
                moved = True
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= 1
            if not map_logic.is_blocked(new_x, new_y):
                tile_info = map_logic.get_tile_info(new_x, new_y)
                clima_factor = efectos["factor_velocidad"]
                player.mover(
                    direccion="izq", 
                    clima=condicion, 
                    clima_factor=clima_factor,
                    tile_info=tile_info,
                )
                moved = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += 1
            if not map_logic.is_blocked(new_x, new_y):
                tile_info = map_logic.get_tile_info(new_x, new_y)
                clima_factor = efectos["factor_velocidad"]
                player.mover(
                    direccion="der", 
                    clima=condicion, 
                    clima_factor=clima_factor,
                    tile_info=tile_info,
                )
                moved = True

        if not moved:
            player.stats.recupera(segundos=dt, rest_point=False)

        # dibujar
        SCREEN.fill((0, 0, 0))
        renderer.draw(SCREEN)
        player.draw(SCREEN)

        # HUD con estado del jugador y clima (multi-line)
        hud_lines = [
            f"Resistencia: {player.stats.resistencia:.1f} | Estado: {player.stats.estado_actual()}",
            f"Reputacion: {player.reputation.valor} | Clima: {condicion} ({intensidad:.2f})",
            f"Velocidad: {player.velocidad_actual:.2f} | ResPen: {efectos['penalizacion_resistencia']:.2f}",
            f"Peso: {player.peso_total} | Pedidos en cola: {len(gestor)}"
        ]

        # Mostrar 3 primeros pedidos por prioridad en HUD
        urgentes = gestor.ordenar_por_prioridad()[:3]
        for idx, pedido in enumerate(urgentes):
            hud_lines.append(f"{idx+1}. {pedido.id} P={pedido.priority} Dur={pedido.duration}s")

        for i, line in enumerate(hud_lines):
            hud_surface = get_font(8).render(line, True, (255, 255, 255))
            SCREEN.blit(hud_surface, (MAP_WIDTH + 10, 8 + i * 20))

        if  keys[pygame.K_ESCAPE]:
            paused = pause()
            if not paused:  # Si pause() retorna False, significa que queremos salir al menú principal
                return
        pygame.display.flip()

def main_menu():
    pygame.display.set_caption("Courier Quest - Menú Principal")
    while True:
        SCREEN.blit(BG, (0, 0))

        MENU_MOUSE_POS = pygame.mouse.get_pos()

        # Calcular el centro de la pantalla actual
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        # Ajustar el tamaño de la fuente según el ancho de la pantalla (reducido)
        title_font_size = min(45, WINDOW_WIDTH // 20)
        button_font_size = min(32, WINDOW_WIDTH // 28)

        MENU_TEXT = get_font(title_font_size).render("COURIER QUEST", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(center_x, center_y - 200))

        PLAY_BUTTON = Button(image=pygame.image.load("sprites/Play Rect.png"), pos=(center_x, center_y - 100), 
                            text_input="PLAY", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        OPTIONS_BUTTON = Button(image=pygame.image.load("sprites/Options Rect.png"), pos=(center_x, center_y + 20), 
                            text_input="OPTIONS", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        QUIT_BUTTON = Button(image=pygame.image.load("sprites/Quit Rect.png"), pos=(center_x, center_y + 140), 
                            text_input="QUIT", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")

        SCREEN.blit(MENU_TEXT, MENU_RECT)

        for button in [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(SCREEN)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.checkForInput(MENU_MOUSE_POS):
                    game()
                if OPTIONS_BUTTON.checkForInput(MENU_MOUSE_POS):
                    # options() # Función no implementada aún
                    pass
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()
        
def pause():
    pygame.display.set_caption("Courier Quest - Pausa")
    while True:
        SCREEN.blit(BG, (0, 0))

        MENU_MOUSE_POS = pygame.mouse.get_pos()

        # Calcular el centro de la pantalla actual
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        # Ajustar el tamaño de la fuente según el ancho de la pantalla (reducido)
        title_font_size = min(45, WINDOW_WIDTH // 20)
        button_font_size = min(32, WINDOW_WIDTH // 28)

        MENU_TEXT = get_font(title_font_size).render("PAUSED", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(center_x, center_y - 200))

        RESUME_BUTTON = Button(image=pygame.image.load("sprites/Play Rect.png"), pos=(center_x, center_y - 100), 
                            text_input="RESUME", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        MAIN_MENU_BUTTON = Button(image=pygame.image.load("sprites/Options Rect.png"), pos=(center_x, center_y + 20), 
                            text_input="MAIN MENU", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        QUIT_BUTTON = Button(image=pygame.image.load("sprites/Quit Rect.png"), pos=(center_x, center_y + 140), 
                            text_input="QUIT", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")

        SCREEN.blit(MENU_TEXT, MENU_RECT)

        for button in [RESUME_BUTTON, MAIN_MENU_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(SCREEN)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if RESUME_BUTTON.checkForInput(MENU_MOUSE_POS):
                    return True  # Retorna True para continuar el juego
                if MAIN_MENU_BUTTON.checkForInput(MENU_MOUSE_POS):
                    return False  # Retorna False para ir al menú principal
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # También permite salir de pausa con ESC
                    return True

        pygame.display.update()


if __name__ == "__main__":
    test_reputation()
    test_stats()
    test_job_manager()
    main_menu()
