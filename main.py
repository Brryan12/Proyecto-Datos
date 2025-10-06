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
from src.game.events import Events
from src.game.save import Save
from src.game.inventory import InventarioPedidos  # Importar InventarioPedidos

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
from src.game.game_state_manager import GameStateManager

# Inicializar pygame antes de usar cualquier función de pygame
pygame.init()

BG = pygame.image.load("./sprites/Background.png")
BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
SPRITES_DIR = BASE_DIR / "sprites"

def get_font(size): # Returns Press-Start-2P in the desired size
    return pygame.font.Font("./sprites/font.ttf", size)

def get_player_name():
    """Pantalla para ingresar el nombre del jugador"""
    pygame.display.set_caption("Courier Quest - Ingresa tu nombre")
    
    name = ""
    max_length = 15
    input_active = True
    cursor_visible = True
    cursor_timer = 0
    
    while input_active:
        dt = pygame.time.Clock().tick(60)
        cursor_timer += dt
        
        # Alternar cursor cada 500ms
        if cursor_timer >= 500:
            cursor_visible = not cursor_visible
            cursor_timer = 0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip():
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.key == pygame.K_ESCAPE:
                    return None  # Cancelar y volver al menú
                else:
                    # Agregar carácter si hay espacio y es válido
                    if len(name) < max_length and event.unicode.isprintable():
                        name += event.unicode
        
        # Dibujar pantalla
        SCREEN.blit(BG, (0, 0))
        
        # Título
        title_font = get_font(32)
        title_text = title_font.render("INGRESA TU NOMBRE", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
        SCREEN.blit(title_text, title_rect)
        
        # Campo de entrada
        input_font = get_font(24)
        input_width = 400
        input_height = 50
        input_rect = pygame.Rect((WINDOW_WIDTH - input_width) // 2, WINDOW_HEIGHT // 2 - 25, input_width, input_height)
        
        # Fondo del campo
        pygame.draw.rect(SCREEN, (255, 255, 255), input_rect)
        pygame.draw.rect(SCREEN, (0, 0, 0), input_rect, 3)
        
        # Texto ingresado
        display_text = name
        if cursor_visible:
            display_text += "|"
        
        text_surface = input_font.render(display_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=input_rect.center)
        SCREEN.blit(text_surface, text_rect)
        
        # Instrucciones
        instruction_font = get_font(16)
        instruction_text = instruction_font.render("Presiona ENTER para continuar o ESC para cancelar", True, (255, 255, 255))
        instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))
        SCREEN.blit(instruction_text, instruction_rect)
        
        pygame.display.update()
    
    return name.strip()

def select_save_file():
    """Pantalla para seleccionar una partida guardada"""
    pygame.display.set_caption("Courier Quest - Seleccionar Partida")
    
    # Buscar todos los archivos de guardado usando GameStateManager
    game_state_manager = GameStateManager()
    save_files = []
    saves_dir = Path("src/game/saves")
    
    if saves_dir.exists():
        for file in saves_dir.glob("*.json"):
            # Excluir el archivo savedScores.json que es solo para puntuaciones
            if file.name != "savedScores.json":
                save_info = game_state_manager.get_save_info(file)
                if save_info:
                    save_files.append(save_info)
    
    if not save_files:
        # No hay partidas guardadas, mostrar mensaje
        show_no_saves_message()
        return None
    
    selected_index = 0
    scroll_offset = 0
    max_visible = 5
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = max(0, selected_index - 1)
                    if selected_index < scroll_offset:
                        scroll_offset = selected_index
                elif event.key == pygame.K_DOWN:
                    selected_index = min(len(save_files) - 1, selected_index + 1)
                    if selected_index >= scroll_offset + max_visible:
                        scroll_offset = selected_index - max_visible + 1
                elif event.key == pygame.K_RETURN:
                    return save_files[selected_index]['file']
                elif event.key == pygame.K_ESCAPE:
                    return None
        
        # Dibujar pantalla
        SCREEN.blit(BG, (0, 0))
        
        # Título
        title_font = get_font(24)
        title_text = title_font.render("SELECCIONAR PARTIDA GUARDADA", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 50))
        SCREEN.blit(title_text, title_rect)
        
        # Lista de partidas
        list_font = get_font(16)
        y_start = 120
        
        for i in range(max_visible):
            file_index = scroll_offset + i
            if file_index >= len(save_files):
                break
                
            save_info = save_files[file_index]
            
            # Color de fondo para la selección actual
            if file_index == selected_index:
                rect = pygame.Rect(30, y_start + i * 60 - 10, WINDOW_WIDTH - 60, 70)
                pygame.draw.rect(SCREEN, (120, 120, 120), rect)
                pygame.draw.rect(SCREEN, (255, 255, 255), rect, 3)
            
            # Información de la partida
            name_text = list_font.render(f"Jugador: {save_info['player_name']}", True, (255, 255, 255))
            day_text = list_font.render(f"Día: {save_info['day']} | Rep: {save_info['reputation']:.1f} | Score: {save_info.get('score', 0)}", True, (200, 200, 200))
            city_text = list_font.render(f"Ciudad: {save_info['city']}", True, (180, 180, 180))
            
            SCREEN.blit(name_text, (60, y_start + i * 60))
            SCREEN.blit(day_text, (60, y_start + i * 60 + 18))
            SCREEN.blit(city_text, (60, y_start + i * 60 + 36))
        
        # Indicadores de scroll
        if scroll_offset > 0:
            up_arrow = list_font.render("↑ Más arriba", True, (255, 255, 255))
            SCREEN.blit(up_arrow, (WINDOW_WIDTH // 2 - 50, 100))
        
        if scroll_offset + max_visible < len(save_files):
            down_arrow = list_font.render("↓ Más abajo", True, (255, 255, 255))
            SCREEN.blit(down_arrow, (WINDOW_WIDTH // 2 - 50, y_start + max_visible * 60))
        
        # Instrucciones
        instruction_font = get_font(12)
        instructions = [
            "↑↓ Navegar | ENTER Seleccionar | ESC Cancelar"
        ]
        
        for i, instruction in enumerate(instructions):
            text = instruction_font.render(instruction, True, (255, 255, 255))
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50 + i * 20))
            SCREEN.blit(text, text_rect)
        
        pygame.display.update()

def show_no_saves_message():
    """Mostrar mensaje cuando no hay partidas guardadas"""
    clock = pygame.time.Clock()
    show_time = 0
    
    while show_time < 2000:  # Mostrar por 2 segundos
        dt = clock.tick(60)
        show_time += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                return  # Salir al presionar cualquier tecla
        
        SCREEN.blit(BG, (0, 0))
        
        # Mensaje
        font = get_font(20)
        message = font.render("NO HAY PARTIDAS GUARDADAS", True, (255, 255, 255))
        message_rect = message.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        SCREEN.blit(message, message_rect)
        
        sub_message = get_font(14).render("Presiona cualquier tecla para volver", True, (200, 200, 200))
        sub_rect = sub_message.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        SCREEN.blit(sub_message, sub_rect)
        
        pygame.display.update()

def es_adyacente(pos1, pos2):
    """Devuelve True si las posiciones están a una casilla de distancia (adyacentes)."""
    x1, y1 = pos1
    x2, y2 = pos2
    return (abs(x1 - x2) == 1 and y1 == y2) or (abs(y1 - y2) == 1 and x1 == x2)

MAP_WIDTH = 605
MAP_HEIGHT = 605
HUD_WIDTH = 300
WINDOW_WIDTH = MAP_WIDTH + HUD_WIDTH
WINDOW_HEIGHT = MAP_HEIGHT
SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

save = Save.load_from_file()

def game(new_game=False, save_file=None):
    global save
    print("Iniciando Courier Quest...")
    
    # Si es nueva partida, siempre preguntar el nombre
    if new_game:
        player_name = get_player_name()
        if player_name is None:  # Usuario canceló
            return  # Volver al menú principal
        # Para nueva partida, no usar save data existente
        save_data_to_use = None
        is_full_save = False
        loaded_full_state = None
    else:
        # Continuar partida: cargar desde archivo específico si se proporciona
        if save_file:
            try:
                # Detectar si es un archivo de GameStateManager o Save básico
                with open(save_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Verificar si tiene campos del GameStateManager
                if 'tiempo_actual_segundos' in data and 'active_orders' in data:
                    # Es un guardado completo de GameStateManager
                    game_state_manager = GameStateManager()
                    loaded_game_state = game_state_manager.load_game_state(save_file)
                    
                    player_name = loaded_game_state.player_name
                    save_data_to_use = None  # No usar Save básico
                    is_full_save = True
                    loaded_full_state = loaded_game_state

                else:
                    # Es un guardado básico de Save
                    from src.game.save import Save
                    save_data_to_use = Save(**data)
                    save = save_data_to_use  # Actualizar save global
                    player_name = save_data_to_use.player_name
                    is_full_save = False
                    loaded_full_state = None

                    
            except Exception as e:
                print(f"Error cargando partida: {e}")
                return
        else:
            # Usar save existente (comportamiento anterior)
            saved_name = getattr(save, 'player_name', None) if save else None
            if not saved_name or saved_name.strip() == "":
                # Si no hay nombre guardado, preguntar
                player_name = get_player_name()
                if player_name is None:  # Usuario canceló
                    return  # Volver al menú principal
            else:
                player_name = saved_name
            save_data_to_use = save
            is_full_save = False
            loaded_full_state = None
    
    TILE_WIDTH = 20
    TILE_HEIGHT = 20





    # --- cargar mapa ---
    try:
        with open(CACHE_DIR / "map.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        city_map = CityMap(**data)

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
                    start_y=start_y,
                    save_data=save_data_to_use,
                    player_name=player_name)

    # --- Inicializar sistema de deshacer ---
    undo_system = UndoSystem(10000)  # Permite deshacer hasta 50 movimientos
    # Guardar estado inicial
    undo_system.save_state(player, 0, [])

    # --- Inicializar inventario ---
    inventario = InventarioPedidos(max_weight=10, screen_width=WINDOW_WIDTH, screen_height=WINDOW_HEIGHT)

    # Listas para rastrear el estado de los pedidos
    pedidos_recogidos = []  # Pedidos que han sido recogidos del mapa
    pedidos_entregados = []  # Pedidos que han sido completamente entregados

    def recoger_paquete(pedido):
        """Recoge un paquete del mapa y lo agrega al inventario"""
        if inventario.can_accept(pedido):
            # Agregar al inventario
            success = inventario.accept_order(pedido)
            if success:
                # Marcar como recogido para que no se dibuje en el mapa
                if pedido not in pedidos_recogidos:
                    pedidos_recogidos.append(pedido)
                print(f"Paquete {pedido.id} recogido y agregado al inventario")
            else:
                print(f"No se pudo agregar el paquete {pedido.id} al inventario")
        else:
            print(f"No hay espacio en el inventario para el paquete {pedido.id}")

    def entregar_paquete(pedido_a_entregar):
        """Entrega un paquete del inventario"""
        # Verificar que el paquete esté en el inventario
        pedidos_en_inventario = inventario.get_orders()
        
        if pedido_a_entregar in pedidos_en_inventario:
            # Remover del inventario
            inventario.reject_order(pedido_a_entregar)
            # Agregar puntuación
            player.score.agregar_ingreso(pedido_a_entregar.payout)
            # Marcar como entregado para que el dropoff desaparezca
            if pedido_a_entregar not in pedidos_entregados:
                pedidos_entregados.append(pedido_a_entregar)
            print(f"Paquete {pedido_a_entregar.id} entregado exitosamente. Pago: ${pedido_a_entregar.payout}")
        else:
            print(f"No tienes el paquete {pedido_a_entregar.id} en tu inventario")

    # --- Restaurar estado completo si se cargó una partida completa ---
    if is_full_save and loaded_full_state:
        game_state_manager = GameStateManager()
        tiempo_datos = game_state_manager.restore_game_state(
            loaded_full_state, player, stats, rep, gestor,
            sistema_clima, notificador
        )
        # Usar los datos de tiempo restaurados
        tiempo_actual_segundos_restored, tiempo_total_pausado_restored, tiempo_inicio_restored = tiempo_datos

    # --- loop principal ---
    running = True
    # Inicializar tiempo según si se restauró o es nueva partida
    if is_full_save and loaded_full_state:
        # Para continuar desde donde se guardó, ajustar tiempo_inicio
        # Fórmula: tiempo_actual_ms = pygame.time.get_ticks() - tiempo_inicio - tiempo_total_pausado
        # Despejando: tiempo_inicio = pygame.time.get_ticks() - tiempo_actual_ms - tiempo_total_pausado
        tiempo_actual_target_ms = tiempo_actual_segundos_restored * 1000
        tiempo_inicio = pygame.time.get_ticks() - tiempo_actual_target_ms - tiempo_total_pausado_restored
        tiempo_total_pausado = tiempo_total_pausado_restored
    else:
        tiempo_inicio = pygame.time.get_ticks()
        tiempo_total_pausado = 0
    
    # Variables para controlar el tiempo pausado
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
        
        # Dibujar casillas de pickup y dropoff
        for pedido in pedidos:
            # Dibujar pickup (verde) solo si no ha sido recogido
            if pedido not in pedidos_recogidos:
                px, py = pedido.pickup
                pygame.draw.rect(SCREEN, (0, 200, 0), (px * 20, py * 20, 18, 18))
        
        # Dibujar dropoffs (rojo) solo para paquetes que están en el inventario
        pedidos_en_inventario = inventario.get_orders()
        for pedido in pedidos_en_inventario:
            if pedido not in pedidos_entregados:
                dx, dy = pedido.dropoff
                pygame.draw.rect(SCREEN, (200, 0, 0), (dx * 20, dy * 20, 18, 18))




        
        # Procesar eventos
        pedidos_data = {
            'pedidos': pedidos,
            'pedidos_recogidos': pedidos_recogidos,
            'pedidos_entregados': pedidos_entregados,
            'es_adyacente_func': es_adyacente
        }
        event_handler = Events(
            player, gestor, notificador, undo_system, inventario,
            recoger_callback=recoger_paquete,
            entregar_callback=entregar_paquete,
            pedidos_data=pedidos_data,
            map_logic=map_logic,
            sistema_clima=sistema_clima,
            tiempo_actual=lambda: tiempo_actual_segundos
        )
        accion = event_handler.procesar_eventos()

        if accion == "salir":
            print("Saliendo del juego.")
            pygame.quit()

        if accion == "pausa":
            if not juego_pausado:
                juego_pausado = True
                tiempo_inicio_pausa = pygame.time.get_ticks()

            # Preparar datos para GameStateManager
            game_state_data = {
                'sistema_clima': sistema_clima,
                'notificador': notificador,
                'tiempo_actual': tiempo_actual_segundos,
                'tiempo_pausado': tiempo_total_pausado,
                'tiempo_inicio': tiempo_inicio,
                'day': save_data_to_use.day if save_data_to_use else 1
            }
            
            paused = pause(player, stats, rep, gestor, city_map.city_name, game_state_data)

            if juego_pausado and tiempo_inicio_pausa is not None:
                tiempo_total_pausado += pygame.time.get_ticks() - tiempo_inicio_pausa
                juego_pausado = False
                tiempo_inicio_pausa = None

            if not paused:
                return  # volver al menú principal
                
        # Obtener datos del clima (siempre disponibles para el HUD)
        condicion = sistema_clima.obtener_condicion()
        intensidad = sistema_clima.obtener_intensidad()
        efectos = sistema_clima.obtener_efectos()

        # Obtener teclas presionadas (siempre disponible para ESC y otros controles)
        keys = pygame.key.get_pressed()

        # --- Lógica del juego ---
        # Actualizar clima (solo cuando no esté pausado)
        if not juego_pausado:
            sistema_clima.actualizar()
            
        # Manejar movimiento del jugador usando el sistema integrado
        moved = event_handler.manejar_movimiento(keys, dt)
    

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
        
        # --- HUD Actualizado ---
        px, py = map_logic.get_player_tile_pos(player.rect)
        tiempo_total_segundos = 900
        tiempo_restante_segundos = max(0, tiempo_total_segundos - tiempo_actual_segundos)
        minutos = tiempo_restante_segundos // 60
        segundos = tiempo_restante_segundos % 60
        
        hud_lines = [
            f"Tiempo: {tiempo_actual_segundos}s | Restante: {minutos:02d}:{segundos:02d}",
            f"Jugador: {player.name} | Score: {player.score.calcular_total()}",
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
            hud_lines.append(f"{idx+1}. {pedido.id} P:{pedido.priority} T:{tiempo_restante_pedido}s Peso:{pedido.weight}kg")

        for i, line in enumerate(hud_lines):
            hud_surface = get_font(8).render(line, True, (255, 255, 255))
            SCREEN.blit(hud_surface, (MAP_WIDTH + 10, 8 + i * 20))

        # Mostrar información de interacción con paquetes (posiciones adyacentes)
        interaccion_y = 550
        
        # Verificar si puede recoger algún paquete
        puede_recoger = False
        for pedido in pedidos:
            if pedido not in pedidos_recogidos and es_adyacente((player.x, player.y), tuple(pedido.pickup)):
                puede_recoger = True
                break
        
        if puede_recoger:
            font = get_font(10)
            texto = font.render("Presiona N para recoger paquete", True, (255, 255, 0))
            SCREEN.blit(texto, (MAP_WIDTH + 10, interaccion_y))
        
        # Verificar si puede entregar algún paquete
        puede_entregar = False
        pedidos_en_inventario = inventario.get_orders()
        for pedido in pedidos_en_inventario:
            if pedido not in pedidos_entregados and es_adyacente((player.x, player.y), tuple(pedido.dropoff)):
                puede_entregar = True
                break
        
        if puede_entregar:
            font = get_font(10)
            texto = font.render("Presiona M para entregar paquete", True, (255, 255, 0))
            SCREEN.blit(texto, (MAP_WIDTH + 10, interaccion_y + 20))

        # DIBUJAR NOTIFICACIÓN (si está activa) - Esto va al final
        notificador.dibujar(SCREEN)
        
        # Manejar pausa si se presionó ESC
        if accion == "pausa":
            # Pausar el tiempo cuando se entra al menú de pausa
            if not juego_pausado:
                juego_pausado = True
                tiempo_inicio_pausa = pygame.time.get_ticks()
            
            # Preparar datos para GameStateManager
            game_state_data = {
                'sistema_clima': sistema_clima,
                'notificador': notificador,
                'tiempo_actual': tiempo_actual_segundos,
                'tiempo_pausado': tiempo_total_pausado,
                'tiempo_inicio': tiempo_inicio,
                'day': save_data_to_use.day if save_data_to_use else 1
            }
            
            paused = pause(player, stats, rep, gestor, city_map.city_name, game_state_data)
            
            # Reanudar el tiempo cuando se sale del menú de pausa
            if juego_pausado and tiempo_inicio_pausa is not None:
                tiempo_total_pausado += pygame.time.get_ticks() - tiempo_inicio_pausa
                juego_pausado = False
                tiempo_inicio_pausa = None
                
            if not paused:  # Si pause() retorna False, significa que queremos salir al menú principal
                return

        # Dibujar el inventario si está activo
        inventario.dibujar_inventario(SCREEN)
        
        # Actualizar la screen
        pygame.display.update()

    
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

        NEW_GAME_BUTTON = Button(None, pos=(center_x, center_y - 100), 
                            text_input="NEW GAME", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        CONTINUE_BUTTON = Button(None, pos=(center_x, center_y - 20), 
                            text_input="CONTINUE", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        SCORE_BUTTON = Button(None, pos=(center_x, center_y + 60), 
                            text_input="SCORE BOARD", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")
        QUIT_BUTTON = Button(None, pos=(center_x, center_y + 140), 
                            text_input="QUIT", font=get_font(button_font_size), base_color="#d7fcd4", hovering_color="White")

        SCREEN.blit(MENU_TEXT, MENU_RECT)

        for button in [NEW_GAME_BUTTON, CONTINUE_BUTTON, SCORE_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(SCREEN)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if NEW_GAME_BUTTON.checkForInput(MENU_MOUSE_POS):
                    game(new_game=True)
                if CONTINUE_BUTTON.checkForInput(MENU_MOUSE_POS):
                    selected_save = select_save_file()
                    if selected_save:  # Usuario seleccionó una partida
                        game(new_game=False, save_file=selected_save)
                if SCORE_BUTTON.checkForInput(MENU_MOUSE_POS):
                    # options() # Función no implementada aún
                    pass
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()
        
def pause(player, stats, rep, gestor, original_caption, game_state_data=None):
    """
    Función de pausa mejorada con soporte para GameStateManager
    
    Args:
        game_state_data: Dict con todos los objetos necesarios para el guardado completo
                        {'sistema_clima': ..., 'notificador': ..., 'tiempo_actual': ..., etc}
    """
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
                        # Usar GameStateManager si los datos están disponibles
                        if game_state_data:
                            game_state_manager = GameStateManager()
                            game_state = game_state_manager.create_game_state(
                                player=player,
                                stats=stats,
                                reputation=rep,
                                gestor_pedidos=gestor,
                                sistema_clima=game_state_data['sistema_clima'],
                                notificador=game_state_data['notificador'],
                                tiempo_actual=game_state_data['tiempo_actual'],
                                tiempo_pausado=game_state_data['tiempo_pausado'],
                                tiempo_inicio=game_state_data['tiempo_inicio'],
                                day=game_state_data.get('day', 1)
                            )
                            save_id = game_state_manager.save_game_state(game_state)

                        else:
                            # Fallback al método anterior (limitado)
                            save_data = player.exportar_estado(
                                player_name=player.name, 
                                day=1,  # aquí puedes usar el día actual
                                current_weather="clear"
                            )
                            save_id = save_data.save_to_file()

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