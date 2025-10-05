import time
import random
from typing import Dict, Any, Optional

_MULTIPLICADORES_BASE: Dict[str, float] = {
    "clear": 1.00,
    "clouds": 0.98,
    "rain_light": 0.90,
    "rain": 0.85,
    "storm": 0.75,
    "fog": 0.88,
    "wind": 0.92,
    "heat": 0.90,
    "cold": 0.92,
}

_PENALIZACIONES_BASE: Dict[str, float] = {
    "clear": 0.0,
    "clouds": 0.0,
    "rain_light": 0.1,
    "rain": 0.1,
    "storm": 0.3,
    "fog": 0.0,
    "wind": 0.1,
    "heat": 0.2,
    "cold": 0.0,
}


class SistemaClima:

    def __init__(self, datos_clima: Any, semilla: Optional[int] = None):
        if semilla is not None:
            random.seed(semilla)

        self.datos_clima = datos_clima
        inicial_cond = getattr(datos_clima.initial, "condition", "clear")
        inicial_int = getattr(datos_clima.initial, "intensity", 1.0)

        self.condicion_actual: str = str(inicial_cond)
        self.intensidad_actual: float = max(0.0, min(1.0, float(inicial_int)))
        self.en_transicion: bool = False
        self.transicion_inicio: float = 0.0
        self.transicion_duracion: float = 0.0
        self.condicion_origen: str = self.condicion_actual
        self.condicion_destino: str = self.condicion_actual
        self.mult_origen: float = _MULTIPLICADORES_BASE.get(self.condicion_actual, 1.0)
        self.mult_destino: float = self.mult_origen
        self.pen_origen: float = _PENALIZACIONES_BASE.get(self.condicion_actual, 0.0)
        self.pen_destino: float = self.pen_origen
        self.intensidad_origen: float = self.intensidad_actual
        self.intensidad_destino: float = self.intensidad_actual

        self.proximo_cambio: float = time.time() + self._intervalo_siguiente()
    def _intervalo_siguiente(self) -> float:
        return float(random.randint(45, 60))

    def _duracion_transicion(self) -> float:
        return random.uniform(3.0, 5.0)
    def _proximo_estado(self, actual: str) -> str:
        transiciones = getattr(self.datos_clima, "transition", {}).get(actual, {})
        if not transiciones:
            return actual
        estados = list(transiciones.keys())
        probabilidades = list(transiciones.values())
        return random.choices(estados, weights=probabilidades, k=1)[0]

    def actualizar(self) -> None:
        ahora = time.time()
        if self.en_transicion:
            progreso = min(1.0, (ahora - self.transicion_inicio) / self.transicion_duracion)
            self.intensidad_actual = (
                (1 - progreso) * self.intensidad_origen + progreso * self.intensidad_destino
            )
            if progreso >= 1.0:
                self.en_transicion = False
                self.condicion_actual = self.condicion_destino
                self.intensidad_actual = self.intensidad_destino
                self.mult_origen = self.mult_destino
                self.pen_origen = self.pen_destino
            return

        if ahora >= self.proximo_cambio:
            nuevo = self._proximo_estado(self.condicion_actual)
            if nuevo == self.condicion_actual:
                self.intensidad_destino = max(
                    0.0, min(1.0, self.intensidad_actual + random.uniform(-0.3, 0.3))
                )
                self.en_transicion = True
                self.transicion_inicio = ahora
                self.transicion_duracion = self._duracion_transicion()
                self.intensidad_origen = self.intensidad_actual
            else:
                self.en_transicion = True
                self.transicion_inicio = ahora
                self.transicion_duracion = self._duracion_transicion()
                self.condicion_origen = self.condicion_actual
                self.condicion_destino = nuevo
                self.intensidad_origen = self.intensidad_actual
                self.intensidad_destino = random.uniform(0.0, 1.0)
                self.mult_origen = _MULTIPLICADORES_BASE.get(self.condicion_origen, 1.0)
                self.mult_destino = _MULTIPLICADORES_BASE.get(self.condicion_destino, 1.0)
                self.pen_origen = _PENALIZACIONES_BASE.get(self.condicion_origen, 0.0)
                self.pen_destino = _PENALIZACIONES_BASE.get(self.condicion_destino, 0.0)

            self.proximo_cambio = ahora + self._intervalo_siguiente()

    def obtener_condicion(self) -> str:
        return self.condicion_actual

    def obtener_intensidad(self) -> float:
        return self.intensidad_actual

    def obtener_efectos(self) -> Dict[str, float]:
        """Devuelve efectos interpolados (factor velocidad y penalización resistencia)."""
        if self.en_transicion:
            progreso = min(1.0, (time.time() - self.transicion_inicio) / self.transicion_duracion)
            mult_eff = (1 - progreso) * self.mult_origen + progreso * self.mult_destino
            pen_eff = (1 - progreso) * self.pen_origen + progreso * self.pen_destino
        else:
            mult_eff = self.mult_origen
            pen_eff = self.pen_origen
        return {
            "factor_velocidad": mult_eff,
            "penalizacion_resistencia": pen_eff * self.intensidad_actual,
        }

    def tiempo_para_cambio(self) -> float:
        return max(0.0, self.proximo_cambio - time.time())


