from typing import List
from pydantic import BaseModel
from datetime import datetime


class PedidoSolicitud(BaseModel):
    id: str
    recoger: List[int]      # coordenada de llegada
    llevar: List[int]     # coordenada para dar el pedido
    pago: int               # pago recibido
    deadline: datetime     # fecha para cumplir la solicitud
    peso: int               # peso del pedido
    prioridad: int          # tipo de prioridad
    tiempo: int          