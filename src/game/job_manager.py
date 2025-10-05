from collections import deque
from typing import List, Optional
from src.models.Pedido import PedidoSolicitud


class GestorPedidos:
    """Gestor de pedidos usando una cola FIFO y operaciones auxiliares."""

    def __init__(self):
        # Cola de pedidos activos (FIFO)
        self.cola_pedidos: deque[PedidoSolicitud] = deque()

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
