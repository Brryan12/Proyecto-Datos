

class Stats:

    def __init__(self, resistencia_max = 100):
        self.resistencia_max = resistencia_max
        self.resistencia = resistencia_max

    def consume_resistencia(self, cantidad: float):
        self.resistencia -= cantidad
        if self.resistencia < 0: #evita numeros negativos
            self.resistencia = 0

    def recupera_resistencia(self, cantidad: float):
        self.resistencia += cantidad
        if self.resistencia > self.resistencia_max:
            self.resistencia = self.resistencia_max #evita subir del límite

    def estado_actual(self) -> str: 

        if self.resistencia <= 0:
            return "exhausto"
        elif self.resistencia <= 30:
            return "cansado"
        else:
            return "normal"
    
    def factor_velocidad(self) -> float:

        est = self.estado_actual()
        if est == "normal":
            return 1.0
        elif est == "cansado":
            return 0.8
        else:
            return 0.5
    