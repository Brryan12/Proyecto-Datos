from typing import List, Optional
from dataclasses import dataclass


@dataclass
class GameState:
    player_x: float
    player_y: float
    player_tile_x: int
    player_tile_y: int
    resistencia: float
    reputacion: int
    peso_total: float
    direccion: str
    tiempo_actual: int # Tiempo del juego en el momento de guardar
    pedidos_activos_ids: List[str] # IDs de pedidos activos en ese instante


class UndoSystem:
    
    def __init__(self, max_undo_steps: int = 20):
        self.max_undo_steps = max_undo_steps # Máximo de estados que se pueden guardar
        self.states_stack: List[GameState] = []
        self.enabled = True # Permite activar/desactivar el sistema de undo
    
    def save_state(self, player, tiempo_actual: int, pedidos_activos_ids: List[str] = None):
        if not self.enabled:
            return
            
        tile_x = int(player.x // player.tile_width ) # Se calculan las coordenadas del jugador en la cuadrícula (tiles)
        tile_y = int(player.y // player.tile_height)
        
        new_state = GameState(  # Se crea un nuevo estado con los datos correspondientes
            player_x=player.x,
            player_y=player.y,
            player_tile_x=tile_x,
            player_tile_y=tile_y,
            resistencia=player.stats.resistencia,
            reputacion=player.reputation.valor,
            peso_total=player.peso_total,
            direccion=player.direccion,
            tiempo_actual=tiempo_actual,
            pedidos_activos_ids=pedidos_activos_ids or []
        )
        
        self.states_stack.append(new_state) # Se añade el estado a la pila
        
        if len(self.states_stack) > self.max_undo_steps: # Si se supera el máximo permitido, se elimina el más antiguo
            self.states_stack.pop(0)
    
    def undo_last_move(self, player, gestor_pedidos=None) -> Optional[GameState]: #Devuelve el estado restaurado o None si no hay nada que deshacer.
        if not self.can_undo():
            print("Undo: No hay movimientos para deshacer")
            return None
        
        previous_state = self.states_stack.pop() # Se obtiene el último estado y se elimina de la pila
        
        player.x = previous_state.player_x # Se restauran las propiedades del jugador
        player.y = previous_state.player_y
        player.direccion = previous_state.direccion
        
        center_x = player.x + player.tile_width // 2 # Se actualiza la posición gráfica del jugador en pantalla
        center_y = player.y + player.tile_height // 2
        player.rect.center = (center_x, center_y)
        player.image = player.sprites[player.direccion]
        
        player.stats.resistencia = previous_state.resistencia # Se restauran estadísticas y atributos
        player.reputation.valor = previous_state.reputacion
        player.peso_total = previous_state.peso_total
        
        return previous_state
    
    def undo_n_moves(self, player, n: int, gestor_pedidos=None) -> Optional[GameState]:
        if n <= 0:
            return None
            
        last_state = None
        undone_count = 0
        
        for i in range(n): #Se repite el proceso de undo hasta 'n' veces o hasta que no haya más estados
            if not self.can_undo():
                break
            last_state = self.undo_last_move(player, gestor_pedidos)
            undone_count += 1
        
        # Operación completada silenciosamente
            
        return last_state
    
    def can_undo(self) -> bool: #Devuelve True si hay estados disponibles para deshacer.
        return self.enabled and len(self.states_stack) > 0
    
    def get_undo_count(self) -> int: #Devuelve cuántos estados hay actualmente en la pila de undo.
        return len(self.states_stack)
    

