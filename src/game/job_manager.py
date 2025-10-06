from collections import deque
from typing import List, Optional
from src.models.Pedido import PedidoSolicitud
from src.game.inventory import InventarioPedidos


class GestorPedidos:
    """Gestor de pedidos usando una cola FIFO y operaciones auxiliares."""

    def __init__(self, max_inventory_weight: int = 50):
        # Cola de pedidos activos (FIFO)
        self.cola_pedidos: deque[PedidoSolicitud] = deque()
        self.available_orders: List[PedidoSolicitud] = [] #Pedidos disponibles
        self.inventory = InventarioPedidos(max_weight=max_inventory_weight)

    def __len__(self) -> int:
        """Permite usar len(gestor) para obtener el número de pedidos en cola."""
        return len(self.cola_pedidos)
    

    def agregar_pedido(self, pedido: PedidoSolicitud) -> None:
        """Agrega un pedido a la cola (FIFO)."""
        self.cola_pedidos.append(pedido)

    def obtener_siguiente(self) -> Optional[PedidoSolicitud]:
        """Saca y devuelve el siguiente pedido en la cola (FIFO)."""
        if self.cola_pedidos:
            return self.cola_pedidos.popleft()
        return None

    def ver_pedido_actual(self) -> Optional[PedidoSolicitud]:
        """Devuelve el primer pedido de la cola sin retirarlo."""
        if self.cola_pedidos:
            return self.cola_pedidos[0]
        return None

    def ver_pedidos(self) -> List[PedidoSolicitud]:
        """Devuelve una lista de los pedidos actuales (sin sacarlos)."""
        return list(self.cola_pedidos)


    # ------------------ Ordenamientos ------------------
    def ordenar_por_duracion(self) -> List[PedidoSolicitud]:
        """Devuelve los pedidos ordenados por duración (menor a mayor)."""
        return sorted(self.cola_pedidos, key=lambda p: p.duration)

    def ordenar_por_prioridad(self) -> List[PedidoSolicitud]:
        """Devuelve los pedidos ordenados por prioridad (mayor a menor)."""
        return sorted(self.cola_pedidos, key=lambda p: p.priority, reverse=True)

    # ------------------ Filtros por tiempo ------------------
    def pedidos_vencidos(self, tiempo_actual: int) -> List[PedidoSolicitud]:
        """
        Devuelve una lista de pedidos que ya excedieron su duración
        desde release_time.
        """
        return [p for p in self.cola_pedidos if tiempo_actual >= p.release_time + p.duration]

    def pedidos_pendientes(self, tiempo_actual: int) -> List[PedidoSolicitud]:
        """
        Devuelve los pedidos que aún están dentro de su duración.
        """
        return [p for p in self.cola_pedidos if tiempo_actual < p.release_time + p.duration]

    # -------------------------
    # Pedidos Disponibles
    # -------------------------

    def add_available(self, pedido: PedidoSolicitud):
        """Agrega un pedido a la lista de disponibles"""
        self.available_orders.append(pedido)

    def remove_available(self, pedido: PedidoSolicitud):
        """Elimina un pedido de los disponibles"""
        if pedido in self.available_orders:
            self.available_orders.remove(pedido)

    # Pedidos disponibles para aceptar 
    def list_available(self) -> List[PedidoSolicitud]:
        return self.available_orders

    def ordenar_disponibles_por_prioridad(self):
        self.available_orders.sort(key=lambda p: p.priority, reverse=True)

    def ordenar_disponibles_por_tiempo(self):
        self.available_orders.sort(key=lambda p: p.release_time)

    # -------------------------
    # Aceptar o rechazar pedidos
    # -------------------------
    def accept_available_order(self, pedido_id: str) -> bool:
        """Acepta un pedido disponible y lo agrega al inventario"""
        pedido = next((p for p in self.available_orders if p.id == pedido_id), None)
        if not pedido:
            return False
        if self.inventory.accept_order(pedido):
            self.remove_available(pedido)
            return True
        return False  # No pudo aceptar por límite de peso

    def reject_available_order(self, pedido_id: str) -> bool:
        """Rechaza un pedido que ya está en el inventario"""
        pedido = next((p for p in self.inventory.get_orders() if p.id == pedido_id), None)
        if not pedido:
            return False
        return self.inventory.reject_order(pedido)

    # -------------------------
    # Navegación en el inventario
    # -------------------------
    def siguiente_inventario(self) -> Optional[PedidoSolicitud]:
        return self.inventory.next()

    def anterior_inventario(self) -> Optional[PedidoSolicitud]:
        return self.inventory.last()

    def pedido_actual(self) -> Optional[PedidoSolicitud]:
        return self.inventory.current_order()

    # -------------------------
    # Información rápida
    # -------------------------
    def peso_inventario(self) -> int:
        return self.inventory.current_weight()

    def listar_inventario(self) -> List[PedidoSolicitud]:
        return self.inventory.get_orders()