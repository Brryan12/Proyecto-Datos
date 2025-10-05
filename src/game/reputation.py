# reputation.py
from typing import Literal, Optional


class Reputation:

    def __init__(
        self,
        valor_inicial: int = 70,
        bono_reputacion_pct: float = 0.05,
        bono_threshold: int = 90,
        mitigacion_threshold: int = 85,
    ):
        self.valor: int = int(valor_inicial)
        self.bono_reputacion_pct: float = float(bono_reputacion_pct)
        self.bono_threshold: int = int(bono_threshold)
        self.mitigacion_threshold: int = int(mitigacion_threshold)
        self._mitigacion_usada: bool = False

        self._streak_no_penalty: int = 0

    def registrar_entrega(
        self,
        estado: Literal["temprano", "a_tiempo", "tarde", "cancelado", "perdido"],
        delay_seconds: Optional[float] = None,
    ) -> None:
        estado_l = str(estado).strip().lower()

        if estado_l in ("a tiempo", "a_tiempo", "on_time", "ontime"):
            estado_l = "a_tiempo"
        if estado_l in ("early",):
            estado_l = "temprano"
        if estado_l in ("lost", "expired", "fallo"):
            estado_l = "perdido"
        if estado_l in ("cancel", "canceled"):
            estado_l = "cancelado"

        delta = 0

        if estado_l == "temprano":
            delta = 5
            self._streak_no_penalty += 1

        elif estado_l == "a_tiempo":
            delta = 3  
            self._streak_no_penalty += 1

        elif estado_l == "tarde":
            if delay_seconds is None:
                delta = -5 
            else:
                if delay_seconds <= 30:
                    delta = -2
                elif delay_seconds <= 120:
                    delta = -5
                else:
                    delta = -10
            if self.valor >= self.mitigacion_threshold and not self._mitigacion_usada:
                delta = int(round(delta / 2.0))
                self._mitigacion_usada = True
            self._streak_no_penalty = 0

        elif estado_l == "cancelado":
            delta = -4
            self._streak_no_penalty = 0

        elif estado_l == "perdido":
            delta = -6
            self._streak_no_penalty = 0

        else:
            raise ValueError(f"Estado desconocido para registrar_entrega: {estado}")

        self._ajustar(delta)
        if self._streak_no_penalty >= 3:
            self._ajustar(2)
            self._streak_no_penalty = 0

    def reset_diario(self) -> None:
        self._mitigacion_usada = False

    def obtener_multiplicador_pago(self) -> float:
        if self.valor >= self.bono_threshold:
            return 1.0 + float(self.bono_reputacion_pct)
        return 1.0

    def derrotado(self) -> bool:
        return self.valor < 20

    def _ajustar(self, delta: int) -> None:
        self.valor = int(max(0, min(100, int(self.valor) + int(delta))))

    def to_dict(self) -> dict:
        return {
            "valor": int(self.valor),
            "bono_reputacion_pct": float(self.bono_reputacion_pct),
            "bono_threshold": int(self.bono_threshold),
            "mitigacion_threshold": int(self.mitigacion_threshold),
            "mitigacion_usada": bool(self._mitigacion_usada),
            "streak_no_penalty": int(self._streak_no_penalty),
        }

    def load(self, d: dict) -> None:
        self.valor = int(d.get("valor", self.valor))
        self.bono_reputacion_pct = float(d.get("bono_reputacion_pct", self.bono_reputacion_pct))
        self.bono_threshold = int(d.get("bono_threshold", self.bono_threshold))
        self.mitigacion_threshold = int(d.get("mitigacion_threshold", self.mitigacion_threshold))
        self._mitigacion_usada = bool(d.get("mitigacion_usada", self._mitigacion_usada))
        self._streak_no_penalty = int(d.get("streak_no_penalty", self._streak_no_penalty))
