import sys
import pygame
import json
from pathlib import Path
from typing import List
from src.models.CityMap import CityMap
from src.models.ClimaData import ClimaData
from src.game.button import Button
from src.game.package_notifier import NotificadorPedidos
from src.api.ManejadorAPI import ManejadorAPI

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
from src.game.undo import UndoSystem

# Inicializar pygame antes de usar cualquier función de pygame
pygame.init()

BG = pygame.image.load("./sprites/Background.png")
BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
SPRITES_DIR = BASE_DIR / "sprites"

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



def game():
    print("Iniciando Courier Quest...")
    TILE_WIDTH = 20
    TILE_HEIGHT = 20

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
        
        # Mostrar información de release_time de cada pedido
        for pedido in pedidos:
            print(f"Pedido {pedido.id}: release_time = {pedido.release_time}s")
            
    except FileNotFoundError as fnf:
        print("No se encontró jobs.json en cache y no se pudo descargar:", fnf)
    except Exception as e:
        print(f"Error cargando pedidos: {e}")

    # --- Inicializar sistemas ---
    gestor = GestorPedidos()  # Tu gestor existente
    notificador = NotificadorPedidos(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # Configurar pedidos en el notificador (todos pasan por aquí primero)
    notificador.agregar_pedidos_iniciales(pedidos)
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

    # --- Inicializar sistema de deshacer ---
    undo_system = UndoSystem(10000)  # Permite deshacer hasta 50 movimientos
    # Guardar estado inicial
    undo_system.save_state(player, 0, [])



    # Demo: imprimir primeros 3 pedidos (info de duración)

    print("\n--- Demostración de uso de duración con pedidos ---")
    if pedidos:
        for pedido in pedidos[:3]:
            print(f"Pedido ID: {pedido.id}, Duración: {pedido.duration} segundos, Tipo: {type(pedido.duration)}")
        pedidos_ordenados = sorted(pedidos, key=lambda p: p.duration)
        print("Pedidos ordenados por duración (primeros 3):")
        for p in pedidos_ordenados:
            print(f"  {p.id} - {p.duration} s")
    else:
        print("No hay pedidos en cache.")
        

    # --- loop principal ---
    running = True
    tiempo_inicio = pygame.time.get_ticks()
    
    # Variables para controlar el tiempo pausado
    tiempo_total_pausado = 0  # Tiempo total que ha estado pausado el juego
    tiempo_inicio_pausa = None  # Momento cuando comenzó la pausa actual
    juego_pausado = False  # Estado de pausa
    
    while running:
        dt = clock.tick(60) / 1000.0  # delta seconds
        
        # Determinar si el juego debe estar pausado
        hay_notificacion_activa = notificador.activo
        
        # Manejar transiciones de pausa
        if hay_notificacion_activa and not juego_pausado:
            # Comenzar pausa por notificación
            juego_pausado = True
            tiempo_inicio_pausa = pygame.time.get_ticks()
        elif not hay_notificacion_activa and juego_pausado and tiempo_inicio_pausa is not None:
            # Terminar pausa por notificación
            juego_pausado = False
            tiempo_total_pausado += pygame.time.get_ticks() - tiempo_inicio_pausa
            tiempo_inicio_pausa = None
        
        # Calcular tiempo actual en segundos desde el inicio (excluyendo tiempo pausado)
        tiempo_actual_ms = pygame.time.get_ticks() - tiempo_inicio - tiempo_total_pausado
        if juego_pausado and tiempo_inicio_pausa is not None:
            # Si está pausado actualmente, no contar el tiempo desde que comenzó la pausa
            tiempo_actual_ms -= (pygame.time.get_ticks() - tiempo_inicio_pausa)
        
        tiempo_actual_segundos = max(0, tiempo_actual_ms // 1000)
        
        # ACTUALIZAR NOTIFICADOR - Solo cuando no esté pausado
        if not juego_pausado:
            notificador.actualizar(tiempo_actual_segundos)
        
        print(player.current_tile_info)
        
        # Manejo de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            # Manejar eventos del notificador (Z/X para aceptar/rechazar)
            if notificador.manejar_eventos(event, gestor):
                continue  # Evento manejado, continuar
                
            # Manejar sistema de deshacer
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u and not notificador.activo:
                    # Deshacer un movimiento (tecla U)
                    undo_system.undo_last_move(player, gestor)
                elif event.key == pygame.K_r and not notificador.activo:
                    # Deshacer múltiples movimientos (tecla R + número)
                    keys_pressed = pygame.key.get_pressed()
                    undo_count = 1
                    
                    # Permitir deshacer más pasos con números
                    if keys_pressed[pygame.K_1]: undo_count = 1
                    elif keys_pressed[pygame.K_2]: undo_count = 2
                    elif keys_pressed[pygame.K_3]: undo_count = 3
                    elif keys_pressed[pygame.K_4]: undo_count = 4
                    elif keys_pressed[pygame.K_5]: undo_count = 5
                    
                    undo_system.undo_n_moves(player, undo_count, gestor)

        # Obtener datos del clima (siempre disponibles para el HUD)
        condicion = sistema_clima.obtener_condicion()
        intensidad = sistema_clima.obtener_intensidad()
        efectos = sistema_clima.obtener_efectos()

        # Obtener teclas presionadas (siempre disponible para ESC y otros controles)
        keys = pygame.key.get_pressed()

        # --- Lógica del juego (solo si no hay notificación activa) ---
        if not notificador.activo:
            # actualizar clima (solo cuando no esté pausado)
            if not juego_pausado:
                sistema_clima.actualizar()
                # Refrescar datos después de la actualización
                condicion = sistema_clima.obtener_condicion()
                intensidad = sistema_clima.obtener_intensidad()
                efectos = sistema_clima.obtener_efectos()

            # mover jugador
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

            if moved:
                # Guardar estado después de un movimiento exitoso
                pedidos_activos_ids = [p.id for p in gestor.ver_pedidos()]
                undo_system.save_state(player, tiempo_actual_segundos, pedidos_activos_ids)
                
            if not moved:
                # Solo recuperar resistencia cuando no esté pausado
                if not juego_pausado:
                    player.stats.recupera(segundos=dt, rest_point=False)
    

        # dibujar
        SCREEN.fill((0, 0, 0))
        renderer.draw(SCREEN)
        
        # Dibujar paquetes y puntos de entrega para pedidos activos
        pedidos_activos = gestor.ver_pedidos()
        renderer.draw_package_icons(SCREEN, pedidos_activos)
        
        # Dibujar cuadrícula de debug (opcional)
        # Si quieres ver los límites de las casillas, descomenta estas líneas:
        debug_color = (200, 200, 200, 100)
        for x in range(0, MAP_WIDTH, TILE_WIDTH):
            pygame.draw.line(SCREEN, debug_color, (x, 0), (x, MAP_HEIGHT), 1)
        for y in range(0, MAP_HEIGHT, TILE_HEIGHT):
            pygame.draw.line(SCREEN, debug_color, (0, y), (MAP_WIDTH, y), 1)
        
        # Dibujar la posición actual del jugador
        player.draw(SCREEN)
        
        # Opcional: Marcar el tile donde está el jugador
        px, py = map_logic.get_player_tile_pos(player.rect)
        tile_rect = pygame.Rect(
            px * TILE_WIDTH - renderer.camera_x, 
            py * TILE_HEIGHT - renderer.camera_y, 
            TILE_WIDTH, TILE_HEIGHT
        )
        #pygame.draw.rect(SCREEN, (255, 0, 0, 128), tile_rect, 2)

        # --- HUD Actualizado ---
        tiempo_total_segundos = 900
        tiempo_restante_segundos = max(0, tiempo_total_segundos - tiempo_actual_segundos)
        minutos = tiempo_restante_segundos // 60
        segundos = tiempo_restante_segundos % 60
        
        hud_lines = [
            f"Tiempo: {tiempo_actual_segundos}s | Restante: {minutos:02d}:{segundos:02d}",
            f"Resistencia: {player.stats.resistencia:.1f} | Estado: {player.stats.estado_actual()}",
            f"Reputacion: {player.reputation.valor} | Clima: {condicion}",
            f"Pedidos activos: {len(gestor)} | Pendientes: {notificador.obtener_pedidos_pendientes_count()}",
            f"Estado: {'PAUSADO' if juego_pausado else 'ACTIVO'} | Notif: {'SI' if notificador.activo else 'NO'}",
            f"Undo: {undo_system.get_undo_count()} pasos disponibles", 
            "U=volver | (1-5)+R = volver N pasos"
        ]

        urgentes = gestor.ordenar_por_prioridad()
        for idx, pedido in enumerate(urgentes):
            tiempo_restante_pedido = max(0, (pedido.release_time + pedido.duration) - tiempo_actual_segundos)
            hud_lines.append(f"{idx+1}. {pedido.id} P:{pedido.priority} T:{tiempo_restante_pedido}s")

        for i, line in enumerate(hud_lines):
            hud_surface = get_font(8).render(line, True, (255, 255, 255))
            SCREEN.blit(hud_surface, (MAP_WIDTH + 10, 8 + i * 20))

        # DIBUJAR NOTIFICACIÓN (si está activa) - Esto va al final
        notificador.dibujar(SCREEN)
            
        if keys and keys[pygame.K_ESCAPE]:
            # Pausar el tiempo cuando se entra al menú de pausa
            if not juego_pausado:
                juego_pausado = True
                tiempo_inicio_pausa = pygame.time.get_ticks()
                
            paused = pause(player, stats, rep, gestor, city_map.city_name)
            
            # Reanudar el tiempo cuando se sale del menú de pausa
            if juego_pausado and tiempo_inicio_pausa is not None:
                tiempo_total_pausado += pygame.time.get_ticks() - tiempo_inicio_pausa
                juego_pausado = False
                tiempo_inicio_pausa = None
                
            if not paused:  # Si pause() retorna False, significa que queremos salir al menú principal
                return
        pygame.display.flip()

    # Incrementar día y guardar
    current_day = save_data.day + 1 
    new_save = player.exportar_estado( 
        player_name=save_data.player_name,
        city_name= "TigerCity",
        day=current_day,
        #score=
        #reputation=
        position=(px,py),
        #current_weather=  
        ) 
    game_id = new_save.save_to_file() # se genera ID único automáticamente 
    save_data = new_save # actualizar referencia para siguiente tick
    
def main_menu():
    pygame.display.set_caption("Courier Quest - Menú Principal")
    api = ManejadorAPI(cache_dir=CACHE_DIR)
    api.update_data()
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
        
def pause(player, stats, rep, gestor, original_caption):
    pygame.display.set_caption("Courier Quest - Pausa")


    while True:
        SCREEN.blit(BG, (0, 0))

        MENU_MOUSE_POS = pygame.mouse.get_pos()

        # Calcular el centro de la pantalla actual
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        # Ajustar el tamaño de la fuente según el ancho de la pantalla (reducido)
        title_font_size = min(45, WINDOW_WIDTH // 20)
        button_font_size = min(28, WINDOW_WIDTH // 32)  # Reducido para 4 botones

        MENU_TEXT = get_font(title_font_size).render("PAUSED", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(center_x, center_y - 220))

        RESUME_BUTTON = Button(None, pos=(center_x, center_y - 120), 
                            text_input="RESUME", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        SAVE_BUTTON = Button(None, pos=(center_x, center_y - 40), 
                            text_input="SAVE GAME", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        MAIN_MENU_BUTTON = Button(None, pos=(center_x, center_y + 40), 
                            text_input="MAIN MENU", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        QUIT_BUTTON = Button(None, pos=(center_x, center_y + 120), 
                            text_input="QUIT", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")

        SCREEN.blit(MENU_TEXT, MENU_RECT)

        for button in [RESUME_BUTTON, SAVE_BUTTON, MAIN_MENU_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(SCREEN)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if RESUME_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.display.set_caption(original_caption)  # Restaurar caption original
                    return True  # Retorna True para continuar el juego
                if SAVE_BUTTON.checkForInput(MENU_MOUSE_POS):
                    try:
                        pass
                    except Exception as e:
                        print(f"Error al guardar: {e}")
                    # Continuar en pausa después de guardar
                if MAIN_MENU_BUTTON.checkForInput(MENU_MOUSE_POS):
                    return False  # Retorna False para ir al menú principal
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()


if __name__ == "__main__":
    main_menu()

def __init__(self, player_name: str,  day: int, city_name: str, score: int,
                 reputation: float, position: tuple, completed_jobs: list,
                 current_weather: str):
        self.id = str(uuid.uuid4()) # ID único de la partida 
        self.player_name = player_name
        self.day = day
        self.city_name = "TigerCity" 
        self.score = score
        self.reputation = reputation
        self.position = position
        self.completed_jobs = completed_jobs
        self.current_weather = current_weather

    def to_dict(self):
        return {
            "id": self.id,
            "player_name": self.player_name,
            "day": self.day,
            "city_name": self.city_name,
            "score": self.score,
            "reputation": self.reputation,
            "position": self.position,
            "completed_jobs": self.completed_jobs,
            "current_weather": self.current_weather
        }

    def save_to_file(self):
        """Guarda el estado actual del juego en un ID único. Devuelve el ID usado. """ 
        SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}

        # cargar partidas previas 
        if SAVE_FILE.exists():
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}

        # guardar esta partida 
        data[self.id] = self.to_dict()

        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"[SAVE] Partida '{self.player_name}' guardada (ID={self.id}) en {SAVE_FILE}")
        return self.id

    @classmethod
    def load_from_file(cls):
        """Carga todas las partidas guardadas"""
        if not SAVE_FILE.exists():
            print("[SAVE] No se encontró archivo de guardado, creando uno nuevo.")
            new_save = cls()
            new_save.save_to_file()
            return [new_save]

        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        saves = []
        for v in data.values():
            if "id" not in v:
                v["id"] = str(uuid.uuid4())
            saves.append(cls(**v))

        print(f"[SAVE] Se cargaron {len(saves)} partidas.")
        return saves
