from pydantic import BaseModel, validator


#Tiene como propósito tomar las condiciones de clima y su intensidad (que afecta al jugador)
class CondicionClima(BaseModel):
    condition: str
    intensity: float


    #En caso de números que se salgan de la normalización de la intensidad, se aplica el método.
    @validator("intensity", pre=True)
    def normalizar_intensidad(cls, v):
        try:
            v = float(v)
            if v > 1.0:
                return max(0.0, min(1.0, v / 3.0))
            return max(0.0, min(1.0, v))
        except Exception:
            return 1.0
