from typing import List
from pydantic import BaseModel


class PedidoSolicitud(BaseModel):
    id: str
    pickup: List[int]       # coordenada de recogida [x, y]
    dropoff: List[int]      # coordenada de entrega [x, y]
    payout: int             # pago recibido
    duration: int           # duración en segundos (tiempo límite del pedido)
    weight: int             # peso del pedido
    priority: int           # prioridad del pedido (0 normal, 1 urgente, etc.)
    release_time: int       # tiempo de liberación en segundos desde el inicio del juego

