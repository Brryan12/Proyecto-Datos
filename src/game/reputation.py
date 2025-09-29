from typing import Literal

class Reputation:
    def __init__(self, valor_inicial: int = 70, bono_reputacion: float = 0.05):
        self.valor = valor_inicial
        self.bono_reputacion = bono_reputacion
        self._mitigacion_usada = False

    def registrar_entrega(self, estado: Literal["temprano", "a_tiempo", "tarde", "fallo"]):
        if estado == "temprano":
            self._ajustar(3)
        elif estado == "a_tiempo":
            self._ajustar(2)
        elif estado == "tarde":
            if self.valor >= 85 and not self._mitigacion_usada: #en caso de entrega tardia
                self._ajustar(-2)
                self._mitigacion_usada = True
            else:
                self._ajustar(-5)
        elif estado == "fallo":
            self._ajustar(-10)
    
    def reset_diario(self):
        self._mitigacion_usada = False
    
    def obtener_multiplicador_pago(self) -> float:
        if self.valor >= 85:
            return 1.0 + self.bono_reputacion
        return 1.0
    
    def derrotado(self)->bool:
        return self.valor < 20
    
    def _ajustar(self, delta: int) -> None:
        self.valor += delta
        if self.valor > 100:
            self.valor = 100
        if self.valor < 0:
            self.valor
    
    def to_dict(self) -> dict:
        return {
            "valor": self.valor,
            "bono_reputacion": self.bono_reputacion,
            "mitigacion_usada": self._mitigacion_usada,
        }
    def load(self, d: dict):
        self.valor = int(d.get("valor", self.valor))
        self.bono_reputacion = float(d.get("bono_reputacion", self.bono_reputacion))
        self._mitigacion_usada = bool(d.get("mitigacion_usada", self._mitigacion_usada))