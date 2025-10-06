from typing import List, Optional 
from src.models.Pedido import PedidoSolicitud
import pygame

class InventarioPedidos: 
    def __init__(self, max_weight: int, screen_width: int, screen_height: int):
        self.max_weight = max_weight 
        self.pedidos: List[PedidoSolicitud] = [] #Lista de pedidos aceptados 
        self.selected_index = 0 # Suma del peso de todos los pedidos que ha aceptado 
        self.inventario_activo = False  # Estado para mostrar/ocultar inventario
        self.screen_width = screen_width
        self.screen_height = screen_height
        
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
    
    def toggle_inventario(self):
        """Alterna el estado del inventario (activo/inactivo)."""
        self.inventario_activo = not self.inventario_activo

    def dibujar_inventario(self, screen: pygame.Surface):
        """Dibuja el inventario en la parte superior de la pantalla."""
        if not self.inventario_activo:
            return

        # Configuración del cuadro del inventario
        ancho_cuadro = self.screen_width - 350
        alto_cuadro = 200
        x = 20
        y = 20

        # Dibujar fondo del inventario
        pygame.draw.rect(screen, (200, 200, 200), (x, y, ancho_cuadro, alto_cuadro))
        pygame.draw.rect(screen, (0, 0, 0), (x, y, ancho_cuadro, alto_cuadro), 3)

        # Renderizar los pedidos en el inventario
        fuente_titulo = pygame.font.Font("./sprites/font.ttf", 8)
        fuente_texto = pygame.font.Font("./sprites/font.ttf", 6)
        
        texto_titulo = fuente_titulo.render("Inventario de Pedidos", True, (0, 0, 0))
        screen.blit(texto_titulo, (x + 10, y + 10))

        # Mostrar peso actual
        peso_actual = self.current_weight()
        texto_peso = fuente_texto.render(f"Peso: {peso_actual}/{self.max_weight}kg", True, (0, 0, 0))
        screen.blit(texto_peso, (x + 10, y + 35))

        for i, pedido in enumerate(self.pedidos[:6]):  # Mostrar hasta 6 pedidos
            texto_pedido = fuente_texto.render(
                f"{i + 1}. {pedido.id} | {pedido.weight}kg | ${pedido.payout}",
                True, (0, 0, 0)
            )
            screen.blit(texto_pedido, (x + 10, y + 60 + i * 18))