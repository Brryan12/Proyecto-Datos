import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

class Score:

    def __init__(self, score_file: Optional[Path] = None, reputation_bonus = 90, reputation_pct = 0.03):
        self.ingresos = 0.0
        self.bonus_time = 0.0
        self.penalizacion = 0.0
        self.events: List[Dict[str, Any]] = [] #lista de python con diccionarios

        if score_file is None: #Se crea el archivo para guardar el score
            score_file = Path("data") / "puntajes.json"
        self.score_file: Path = Path(score_file)

        self.reputation_bonus = reputation_bonus
        self.reputation_pct = reputation_pct
    
    def agregar_ingreso(self, payout: float, reputation: Optional[int] = None, 
                        meta: Optional[Dict[str, Any]] = None) -> float:
        multiplicador_pago = 1.0
        if reputation is not None and reputation >= self.reputation_bonus:
            multiplicador_pago += self.reputation_bonus
        
        ganado = float(payout) * multiplicador_pago
        self.ingresos += ganado

        self.events.append({
            "type": "income",
            "base": float(payout),
            "reputation": reputation,
            "multiplier": multiplicador_pago,
            "amount": ganado,
            "meta": meta or {},
            "timeS": datetime.utcnow().isoformat() #guarda el tiempo real
        })
        return ganado

    def agregar_bono(self, ganado: float, motive: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self.bonus_time += float(ganado)
        self.events.append({
            "type": "penalty",
            "amount": float(ganado),
            "reason": motive,
            "meta": meta or {},
            "ts": datetime.utcnow().isoformat()
        })

    def agregar_penalizacion(self, ganado: float, motive: str, meta: Optional[Dict[str, Any]] = None) -> None:
        self.penalizacion += float(ganado)
        self.events.append({
            "type": "penalty",
            "amount": float(ganado),
            "reason": motive,
            "meta": meta or {},
            "ts": datetime.utcnow().isoformat()
        })
    
    def calcular_total(self) -> int:
        total = self.ingresos + self.bonus_time - self.penalizacion
        return int(round(total))
    
    def save_scoreboard(self):

        self.score_file.parent.mkdir(parents = True, exist_ok = True)

        tabla: List[Dict[str, Any]] = [],
        if self.score_file.exists():
            try:
                with open(self.score_file, "r", encoding= "utf-8") as f:
                    tabla = json.load(f)
            except Exception:
                tabla = []
        
        resumen = {
            "timestamp": datetime.utcnow().isoformat,
            "income": self.ingresos,
            "bonus": self.bonus_time,
            "penalizations": self.penalizacion,
            "puntaje_final": self.calcular_total(),
            "entries_count": len(self.events),
        }
        tabla.append(resumen)
        tabla.sort(key = lambda x: x.get("puntaje_final", 0), reverse = True) #Sorting method.
        with open (self.score_file, "w", encoding = "utf-8") as f:
            json.dump(tabla, f, indent = 2, ensure_ascii = False)
    
    def exportar_reporte(self, out_path: Optional[Path] = None) -> None:
        p = Path(out_path) if out_path else (self.score_file.parent / f"puntaje_full_{datetime.utcnow().isoformat()}.json")
        p.parent.mkdir(parents = True, exist_ok = True)
        report = {
            "summary": {
                        "income": self.ingresos,
                        "bonus": self.bonus_time,
                        "penalizations": self.penalizacion,
                        "puntaje_final": self.calcular_total(),
            },
            "entries": self.events
        }
        with open(p, "w", encoding = "utf-8") as f:
            json.dump(report, f, indent = 2, ensure_ascii = False)



