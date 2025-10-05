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
    tiempo_actual: int
    pedidos_activos_ids: List[str]


class UndoSystem:
    
    def __init__(self, max_undo_steps: int = 20):
        self.max_undo_steps = max_undo_steps
        self.states_stack: List[GameState] = []
        self.enabled = True
    
    def save_state(self, player, tiempo_actual: int, pedidos_activos_ids: List[str] = None):
        if not self.enabled:
            return
            
        tile_x = int(player.x // player.tile_width)
        tile_y = int(player.y // player.tile_height)
        
        new_state = GameState(
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
        
        self.states_stack.append(new_state)
        
        if len(self.states_stack) > self.max_undo_steps:
            self.states_stack.pop(0)
            
        print(f"Undo: Estado guardado en ({tile_x}, {tile_y}) - Stack size: {len(self.states_stack)}")
    
    def undo_last_move(self, player, gestor_pedidos=None) -> Optional[GameState]:
        if not self.can_undo():
            print("Undo: No hay movimientos para deshacer")
            return None
        
        previous_state = self.states_stack.pop()
        
        player.x = previous_state.player_x
        player.y = previous_state.player_y
        player.direccion = previous_state.direccion
        
        center_x = player.x + player.tile_width // 2
        center_y = player.y + player.tile_height // 2
        player.rect.center = (center_x, center_y)
        player.image = player.sprites[player.direccion]
        
        player.stats.resistencia = previous_state.resistencia
        player.reputation.valor = previous_state.reputacion
        player.peso_total = previous_state.peso_total
        
        print(f"Undo: Restaurado a posición ({previous_state.player_tile_x}, {previous_state.player_tile_y}) - Stack size: {len(self.states_stack)}")
        
        return previous_state
    
    def undo_n_moves(self, player, n: int, gestor_pedidos=None) -> Optional[GameState]:
        if n <= 0:
            return None
            
        last_state = None
        undone_count = 0
        
        for i in range(n):
            if not self.can_undo():
                break
            last_state = self.undo_last_move(player, gestor_pedidos)
            undone_count += 1
        
        if undone_count > 0:
            print(f"Undo: Deshecho {undone_count} de {n} movimientos solicitados")
        else:
            print("Undo: No se pudo deshacer ningún movimiento")
            
        return last_state
    
    def can_undo(self) -> bool:
        return self.enabled and len(self.states_stack) > 0
    
    def get_undo_count(self) -> int:
        return len(self.states_stack)
    

