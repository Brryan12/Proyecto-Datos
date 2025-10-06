from pydantic import BaseModel
from typing import Optional, Tuple, List, Dict, Any
import json
from pathlib import Path
import uuid
from datetime import datetime

from src.game.save import Save
from src.game.player import Player
from src.game.stats_module import Stats
from src.game.reputation import Reputation
from src.game.job_manager import GestorPedidos
from src.game.weather_system import SistemaClima
from src.game.package_notifier import NotificadorPedidos
from src.models.Pedido import PedidoSolicitud


class GameState(BaseModel):
    """Modelo completo del estado del juego"""
    
    # Información básica del juego
    player_name: str
    day: int
    city_name: str = "TigerCity"
    save_timestamp: str
    
    # Posición y estado físico del jugador
    position: Tuple[float, float]
    direccion: str
    peso_total: float
    
    # Estadísticas del jugador
    resistencia: float
    resistencia_max: float
    exhaust_lock: bool
    score: int
    reputation: float
    
    # Estado del tiempo
    tiempo_actual_segundos: int
    tiempo_total_pausado: int
    tiempo_inicio: int
    
    # Estado del clima
    current_weather: str
    weather_intensity: float
    weather_transition_state: Dict[str, Any]
    
    # Pedidos y trabajo
    active_orders: List[Dict[str, Any]]  # Pedidos en cola
    inventory_orders: List[Dict[str, Any]]  # Pedidos en inventario
    available_orders: List[Dict[str, Any]]  # Pedidos disponibles
    completed_jobs: List[str]
    pedidos_mostrados: List[str]
    selected_inventory_index: int
    
    # Estado del notificador
    pedidos_pendientes: List[Dict[str, Any]]
    notificacion_activa: bool


class GameStateManager:
    """Gestor centralizado del estado del juego"""
    
    def __init__(self):
        self.save_dir = Path(__file__).resolve().parent / "saves"
        self.save_dir.mkdir(exist_ok=True)
    
    def create_game_state(
        self,
        player: Player,
        stats: Stats,
        reputation: Reputation,
        gestor_pedidos: GestorPedidos,
        sistema_clima: SistemaClima,
        notificador: NotificadorPedidos,
        tiempo_actual: int,
        tiempo_pausado: int,
        tiempo_inicio: int,
        day: int
    ) -> GameState:
        """Crea un estado completo del juego a partir de todos los componentes"""
        
        # Serializar pedidos activos
        active_orders = []
        for pedido in gestor_pedidos.ver_pedidos():
            active_orders.append(self._serialize_pedido(pedido))
        
        # Serializar inventario
        inventory_orders = []
        for pedido in gestor_pedidos.inventory.get_orders():
            inventory_orders.append(self._serialize_pedido(pedido))
        
        # Serializar pedidos disponibles
        available_orders = []
        for pedido in gestor_pedidos.list_available():
            available_orders.append(self._serialize_pedido(pedido))
        
        # Serializar pedidos pendientes de notificación
        pedidos_pendientes = []
        for pedido in notificador.pedidos_pendientes:
            pedidos_pendientes.append(self._serialize_pedido(pedido))
        
        # Estado del clima
        weather_state = {
            "condicion_actual": sistema_clima.condicion_actual,
            "intensidad_actual": sistema_clima.intensidad_actual,
            "en_transicion": sistema_clima.en_transicion,
            "transicion_inicio": sistema_clima.transicion_inicio,
            "transicion_duracion": sistema_clima.transicion_duracion,
            "condicion_origen": sistema_clima.condicion_origen,
            "condicion_destino": sistema_clima.condicion_destino,
        }
        
        return GameState(
            player_name=player.name,
            day=day,
            save_timestamp=datetime.now().isoformat(),
            
            # Posición y estado físico
            position=(player.x, player.y),
            direccion=player.direccion,
            peso_total=player.peso_total,
            
            # Estadísticas
            resistencia=stats.resistencia,
            resistencia_max=stats.resistencia_max,
            exhaust_lock=stats._exhaust_lock,
            score=getattr(stats, 'score', 0),
            reputation=reputation.valor,
            
            # Estado del tiempo
            tiempo_actual_segundos=tiempo_actual,
            tiempo_total_pausado=tiempo_pausado,
            tiempo_inicio=tiempo_inicio,
            
            # Estado del clima
            current_weather=sistema_clima.condicion_actual,
            weather_intensity=sistema_clima.intensidad_actual,
            weather_transition_state=weather_state,
            
            # Pedidos
            active_orders=active_orders,
            inventory_orders=inventory_orders,
            available_orders=available_orders,
            completed_jobs=[], # TODO: implementar si es necesario
            pedidos_mostrados=list(notificador.pedidos_mostrados),
            selected_inventory_index=gestor_pedidos.inventory.selected_index,
            
            # Notificador
            pedidos_pendientes=pedidos_pendientes,
            notificacion_activa=notificador.activo
        )
    
    def _serialize_pedido(self, pedido: PedidoSolicitud) -> Dict[str, Any]:
        """Serializa un pedido a diccionario"""
        return {
            "id": pedido.id,
            "priority": pedido.priority,
            "weight": pedido.weight,
            "payout": pedido.payout,
            "duration": pedido.duration,
            "release_time": pedido.release_time,
            "pickup": pedido.pickup,
            "dropoff": pedido.dropoff
        }
    
    def _deserialize_pedido(self, data: Dict[str, Any]) -> PedidoSolicitud:
        """Deserializa un diccionario a pedido"""
        return PedidoSolicitud(
            id=data["id"],
            priority=data["priority"],
            weight=data["weight"],
            payout=data["payout"],
            duration=data["duration"],
            release_time=data["release_time"],
            pickup=data["pickup"],
            dropoff=data["dropoff"]
        )
    
    def save_game_state(self, game_state: GameState) -> str:
        """Guarda el estado completo del juego"""
        save_id = str(uuid.uuid4())
        file_path = self.save_dir / f"{save_id}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(game_state.model_dump(), f, indent=4, ensure_ascii=False)
        
        print(f"[SAVE] Estado completo guardado en {file_path}")
        return save_id
    
    def load_game_state(self, save_file: Path) -> GameState:
        """Carga un estado completo del juego"""
        with open(save_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return GameState(**data)
    
    def restore_game_state(
        self,
        game_state: GameState,
        player: Player,
        stats: Stats,
        reputation: Reputation,
        gestor_pedidos: GestorPedidos,
        sistema_clima: SistemaClima,
        notificador: NotificadorPedidos
    ) -> Tuple[int, int, int]:
        """Restaura el estado del juego en todos los componentes"""
        
        # Restaurar player
        player.x = game_state.position[0]
        player.y = game_state.position[1]
        player.direccion = game_state.direccion
        player.peso_total = game_state.peso_total
        player.name = game_state.player_name
        
        # Actualizar rect del player
        center_x = player.x + player.tile_width // 2
        center_y = player.y + player.tile_height // 2
        player.rect.center = (center_x, center_y)
        player.image = player.sprites[player.direccion]
        
        # Restaurar estadísticas
        stats.resistencia = game_state.resistencia
        stats.resistencia_max = game_state.resistencia_max
        stats._exhaust_lock = game_state.exhaust_lock
        if hasattr(stats, 'score'):
            stats.score = game_state.score
        
        # Restaurar reputación
        reputation.valor = game_state.reputation
        
        # Restaurar clima
        weather_state = game_state.weather_transition_state
        sistema_clima.condicion_actual = weather_state["condicion_actual"]
        sistema_clima.intensidad_actual = weather_state["intensidad_actual"]
        sistema_clima.en_transicion = weather_state["en_transicion"]
        sistema_clima.transicion_inicio = weather_state["transicion_inicio"]
        sistema_clima.transicion_duracion = weather_state["transicion_duracion"]
        sistema_clima.condicion_origen = weather_state["condicion_origen"]
        sistema_clima.condicion_destino = weather_state["condicion_destino"]
        
        # Restaurar pedidos activos
        gestor_pedidos.cola_pedidos.clear()
        for pedido_data in game_state.active_orders:
            pedido = self._deserialize_pedido(pedido_data)
            gestor_pedidos.cola_pedidos.append(pedido)
        
        # Restaurar inventario
        gestor_pedidos.inventory.pedidos.clear()
        for pedido_data in game_state.inventory_orders:
            pedido = self._deserialize_pedido(pedido_data)
            gestor_pedidos.inventory.pedidos.append(pedido)
        
        gestor_pedidos.inventory.selected_index = game_state.selected_inventory_index
        
        # Restaurar pedidos disponibles
        gestor_pedidos.available_orders.clear()
        for pedido_data in game_state.available_orders:
            pedido = self._deserialize_pedido(pedido_data)
            gestor_pedidos.available_orders.append(pedido)
        
        # Restaurar notificador
        notificador.pedidos_pendientes.clear()
        for pedido_data in game_state.pedidos_pendientes:
            pedido = self._deserialize_pedido(pedido_data)
            notificador.pedidos_pendientes.append(pedido)
        
        notificador.pedidos_mostrados = set(game_state.pedidos_mostrados)
        notificador.activo = game_state.notificacion_activa
        
        # Retornar datos de tiempo para main.py
        return (
            game_state.tiempo_actual_segundos,
            game_state.tiempo_total_pausado,
            game_state.tiempo_inicio
        )
    
    def get_save_info(self, save_file: Path) -> Dict[str, Any]:
        """Obtiene información básica de un archivo de guardado para mostrar en el menú"""
        try:
            game_state = self.load_game_state(save_file)
            return {
                'file': save_file,
                'player_name': game_state.player_name,
                'day': game_state.day,
                'reputation': game_state.reputation,
                'city': game_state.city_name,
                'save_timestamp': game_state.save_timestamp,
                'score': game_state.score
            }
        except Exception as e:
            print(f"Error leyendo {save_file}: {e}")
            return None