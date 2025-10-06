import pygame
from typing import List, Optional
from src.models.Pedido import PedidoSolicitud
from src.game.job_manager import GestorPedidos

class NotificadorPedidos:
    def __init__(self, screen_width: int, screen_height: int):
        self.activo = False
        self.pedido_actual: Optional[PedidoSolicitud] = None
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Fuentes para la interfaz
        self.fuente_titulo = pygame.font.Font("./sprites/font.ttf", 10)
        self.fuente_detalles = pygame.font.Font("./sprites/font.ttf", 8)
        self.fuente_opciones = pygame.font.Font("./sprites/font.ttf", 10)
        
        # Gestión de pedidos pendientes por tiempo
        self.pedidos_pendientes: List[PedidoSolicitud] = []
        self.pedidos_mostrados = set()  # IDs de pedidos ya notificados al jugador
        
    def agregar_pedidos_iniciales(self, pedidos: List[PedidoSolicitud]):
        """Agrega todos los pedidos iniciales a la lista de pendientes"""
        self.pedidos_pendientes.extend(pedidos)

        
    def actualizar(self, tiempo_actual_segundos: int):
        """Verifica si hay pedidos que deben mostrarse según su release_time"""
        if self.activo:
            return False  # Ya hay una notificación activa
            
        # Buscar el primer pedido que deba mostrarse
        for pedido in self.pedidos_pendientes[:]:
            if (pedido.release_time <= tiempo_actual_segundos and 
                pedido.id not in self.pedidos_mostrados):
                
                self.mostrar_pedido(pedido)
                self.pedidos_mostrados.add(pedido.id)
                self.pedidos_pendientes.remove(pedido)
                return True
        return False
        
    def mostrar_pedido(self, pedido: PedidoSolicitud):
        """Activa la notificación para un pedido específico"""
        self.activo = True
        self.pedido_actual = pedido

        
    def ocultar_pedido(self):
        """Desactiva la notificación actual"""
        self.activo = False
        self.pedido_actual = None
        
    def dibujar(self, screen: pygame.Surface):
        """Dibuja la notificación en pantalla si está activa"""
        if not self.activo or not self.pedido_actual:
            return
            
        # Configuración del cuadro de notificación
        ancho_cuadro = 500
        alto_cuadro = 200
        x = (self.screen_width - ancho_cuadro) // 2
        y = (self.screen_height - alto_cuadro) // 2
        
        # Dibujar fondo
        pygame.draw.rect(screen, (255, 255, 255), (x, y, ancho_cuadro, alto_cuadro))
        pygame.draw.rect(screen, (0, 0, 0), (x, y, ancho_cuadro, alto_cuadro), 3)
        
        # Renderizar textos
        titulo = self.fuente_titulo.render("¡¡¡Nuevo pedido!!!", True, (0, 0, 0))
        detalles = self.fuente_detalles.render(
            f"ID: {self.pedido_actual.id} | Pago: {self.pedido_actual.payout} | " +
            f"Peso: {self.pedido_actual.weight}kg | Prioridad: {self.pedido_actual.priority}", 
            True, (0, 0, 0)
        )
        opciones = self.fuente_opciones.render("(Z) aceptar                (X) rechazar", True, (0, 0, 0))
        
        # Centrar y dibujar textos
        screen.blit(titulo, (x + (ancho_cuadro - titulo.get_width()) // 2, y + 20))
        screen.blit(detalles, (x + (ancho_cuadro - detalles.get_width()) // 2, y + 80))
        screen.blit(opciones, (x + (ancho_cuadro - opciones.get_width()) // 2, y + 130))
        
    def manejar_eventos(self, event: pygame.event.Event, gestor_pedidos: GestorPedidos) -> bool:
        """Maneja los eventos de teclado para aceptar/rechazar pedidos"""
        if not self.activo or not self.pedido_actual:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:  # Aceptar pedido
                gestor_pedidos.agregar_pedido(self.pedido_actual)

                self.ocultar_pedido()
                return True
                
            elif event.key == pygame.K_x:  # Rechazar pedido

                self.ocultar_pedido()
                return True
                
        return False
    
    def obtener_pedidos_pendientes_count(self) -> int:
        """Devuelve la cantidad de pedidos pendientes por mostrar"""
        return len(self.pedidos_pendientes)