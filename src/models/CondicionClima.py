from pydantic import BaseModel, validator

class CondicionClima(BaseModel):
    condition: str
    intensity: int

    @validator("intensity", pre=True)
    def normalizar_intensidad(cls, v):
        try:
            v = float(v)
            if v > 1.0:
                return max(0.0, min(1.0, v / 3.0))
            return max(0.0, min(1.0, v))
        except Exception:
            return 1.0