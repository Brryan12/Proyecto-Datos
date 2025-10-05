# stats_module.py
from typing import Dict, Literal


class Stats:


    def __init__(
        self,
        resistencia_max: float = 100.0,
        recuperacion_threshold: float = 30.0,
        consumo_por_celda: float = 0.5,
        peso_extra_por_unidad: float = 0.2,
        recuperacion_rate_idle: float = 5.0,
        recuperacion_rate_rest_point: float = 10.0,
    ):
        self.resistencia_max: float = resistencia_max
        self.resistencia: float = resistencia_max
        self.recuperacion_threshold: float = recuperacion_threshold
        self.consumo_por_celda: float = consumo_por_celda
        self.peso_extra_por_unidad: float = peso_extra_por_unidad

        self.extras_clima: Dict[str, float] = {
            "rain": 0.1,
            "wind": 0.1,
            "rain_light": 0.1,
            "storm": 0.3,
            "heat": 0.2,
            "clear": 0.0,
            "clouds": 0.0,
            "fog": 0.0,
            "cold": 0.0,
        }

        self.recuperacion_rate_idle: float = recuperacion_rate_idle
        self.recuperacion_rate_rest_point: float = recuperacion_rate_rest_point

        self._exhaust_lock: bool = False

    # ---------------- Consumo ----------------
    def consumo_por_celda_total(self, peso_total: float, condicion_clima: str) -> float:
        base = self.consumo_por_celda
        peso_extra = 0.0
        if peso_total > 3.0:
            peso_extra = (peso_total - 3.0) * self.peso_extra_por_unidad
        clima_extra = self.extras_clima.get(condicion_clima, 0.0)
        return base + peso_extra + clima_extra

    def consume_por_mover(
        self, celdas: float = 1.0, peso_total: float = 0.0, condicion_clima: str = "clear"
    ) -> float:

        por_celda = self.consumo_por_celda_total(peso_total, condicion_clima)
        cantidad = por_celda * max(0.0, float(celdas))
        self._do_consume(cantidad)
        return cantidad

    def _do_consume(self, cantidad: float) -> None:
        self.resistencia -= cantidad
        if self.resistencia <= 0.0:
            self.resistencia = 0.0
            self._exhaust_lock = True

    def recupera(self, segundos: float, rest_point: bool = False) -> float:
        rate = self.recuperacion_rate_rest_point if rest_point else self.recuperacion_rate_idle
        cant = rate * max(0.0, segundos)
        self.resistencia += cant
        if self.resistencia > self.resistencia_max:
            self.resistencia = self.resistencia_max
        if self._exhaust_lock and self.resistencia >= self.recuperacion_threshold:
            self._exhaust_lock = False
        return cant

    def estado_actual(self) -> Literal["normal", "cansado", "exhausto"]:
        if self.resistencia <= 0.0:
            return "exhausto"
        if self.resistencia <= self.recuperacion_threshold:
            return "cansado"
        return "normal"

    def factor_velocidad(self) -> float:
        estado = self.estado_actual()
        if estado == "normal":
            return 1.0
        if estado == "cansado":
            return 0.8
        return 0.0

    def puede_moverse(self) -> bool:
        if self._exhaust_lock:
            return self.resistencia >= self.recuperacion_threshold
        return self.resistencia > 0.0

    def to_dict(self) -> dict:
        return {
            "resistencia_max": self.resistencia_max,
            "resistencia": self.resistencia,
            "recuperacion_threshold": self.recuperacion_threshold,
            "exhaust_lock": self._exhaust_lock,
        }

    def load(self, d: dict) -> None:
        self.resistencia_max = float(d.get("resistencia_max", self.resistencia_max))
        self.resistencia = float(d.get("resistencia", self.resistencia))
        self.recuperacion_threshold = float(d.get("recuperacion_threshold", self.recuperacion_threshold))
        self._exhaust_lock = bool(d.get("exhaust_lock", self._exhaust_lock))
