from pydantic import BaseModel

class CondicionClima(BaseModel):
    condition: str
    intensity: int