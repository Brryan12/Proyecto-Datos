from typing import List, Optional 
from src.models.Pedido import PedidoSolicitud 

class InventarioPedidos: 
    def __init__(self, max_weight: int):
        self.max_weight = max_weight 
        self.pedidos: List[PedidoSolicitud] = [] #Lista de pedidos aceptados 
        self.selected_index = 0 # Suma del peso de todos los pedidos que ha aceptado 
        
    def current_weight(self) -> int: 
        return sum(p.weight for p in self.pedidos) # Verifica que aún puede aceptar el pedido por el peso 
    
    def can_accept(self, pedido: PedidoSolicitud) -> bool: 
        return self.current_weight() + pedido.weight <= self.max_weight 

    def accept_order(self, pedido: PedidoSolicitud) -> bool: 
        if self.can_accept(pedido): 
            self.pedidos.append(pedido) 
            return True 
        return False 
    
    def reject_order(self, pedido: PedidoSolicitud) -> bool: 
        if pedido in self.pedidos: 
            self.pedidos.remove(pedido) 
            self.selected_index = min(self.selected_index, len(self.pedidos) - 1) 
            return True 
        return False 
    
    def next(self) -> Optional[PedidoSolicitud]: 
        if not self.pedidos:
            return None
        
        self.selected_index = (self.selected_index + 1) % len(self.pedidos) 
        return self.pedidos[self.selected_index] 
    
    def last(self) -> Optional[PedidoSolicitud]: 
        if not self.pedidos:
            return None 
        
        self.selected_index = (self.selected_index - 1) % len(self.pedidos) 
        return self.pedidos[self.selected_index] 
    
    def arrange_by_priority(self): 
        self.pedidos.sort(key=lambda p: p.priority, reverse=True) 
        
    def arrange_by_time(self): 
        self.pedidos.sort(key=lambda p: p.release_time) 
        
    def get_orders(self) -> List[PedidoSolicitud]: 
        return self.pedidos

    def current_order(self) -> Optional[PedidoSolicitud]: 
        if not self.pedidos: 
            return None 
        return self.pedidos[self.selected_index]