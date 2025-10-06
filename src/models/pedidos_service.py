import json
from pathlib import Path
from typing import List
from src.models.Pedido import PedidoSolicitud
from src.api.ManejadorAPI import ManejadorAPI


class ServicioPedidos:
    def __init__(self, cache_dir: str = "cache", default_duration: int = 15 * 60):

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.api = ManejadorAPI(cache_dir=self.cache_dir)
        self.default_duration = default_duration

    def cargar_pedidos(self, force_update: bool = True) -> List[PedidoSolicitud]:

        jobs_file = self.cache_dir / "jobs.json"

        if force_update or not jobs_file.exists():
            print("jobs.json no encontrado o actualización forzada. Descargando desde API...")
            self.api.get_jobs(save=True)

        with open(jobs_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        pedidos: List[PedidoSolicitud] = []
        for job in data:
            pedido = PedidoSolicitud(
                id=job.get("id"),
                pickup=job.get("pickup"),
                dropoff=job.get("dropoff"),
                payout=job.get("payout"),
                duration=self.default_duration,   # ⬅️ ignoramos deadline, siempre duración fija
                weight=job.get("weight"),
                priority=job.get("priority"),
                release_time=job.get("release_time"),
            )
            pedidos.append(pedido)

        return pedidos


