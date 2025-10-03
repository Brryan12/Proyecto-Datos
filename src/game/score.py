import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List


class Score:
    def __init__(
        self,
        score_file: Optional[Path] = None,
        reputation_threshold: int = 90,
        reputation_pct: float = 0.05,
    ):
        self.ingresos: float = 0.0
        self.bonus_time: float = 0.0
        self.penalizacion: float = 0.0
        self.events: List[Dict[str, Any]] = []

        if score_file is None:
            score_file = Path("data") / "puntajes.json"
        self.score_file: Path = Path(score_file)

        self.reputation_threshold = reputation_threshold
        self.reputation_pct = reputation_pct

    def agregar_ingreso(
        self,
        payout: float,
        reputation: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> float:
        multiplicador_pago = 1.0
        if reputation is not None and reputation >= self.reputation_threshold:
            multiplicador_pago += self.reputation_pct

        ganado = float(payout) * multiplicador_pago
        self.ingresos += ganado

        self.events.append({
            "type": "income",
            "base": float(payout),
            "reputation": reputation,
            "multiplier": multiplicador_pago,
            "amount": ganado,
            "meta": meta or {},
            "ts": datetime.utcnow().isoformat(),
        })
        return ganado

    def agregar_bono(
        self, ganado: float, motive: str, meta: Optional[Dict[str, Any]] = None
    ) -> None:
        self.bonus_time += float(ganado)
        self.events.append({
            "type": "bonus",
            "amount": float(ganado),
            "reason": motive,
            "meta": meta or {},
            "ts": datetime.utcnow().isoformat(),
        })

    def agregar_penalizacion(
        self, perdido: float, motive: str, meta: Optional[Dict[str, Any]] = None
    ) -> None:
        self.penalizacion += float(perdido)
        self.events.append({
            "type": "penalty",
            "amount": float(perdido),
            "reason": motive,
            "meta": meta or {},
            "ts": datetime.utcnow().isoformat(),
        })

    def calcular_total(self) -> int:
        total = self.ingresos + self.bonus_time - self.penalizacion
        return int(round(total))

    def save_scoreboard(self) -> None:
        self.score_file.parent.mkdir(parents=True, exist_ok=True)

        if self.score_file.exists():
            try:
                with open(self.score_file, "r", encoding="utf-8") as f:
                    tabla = json.load(f)
                    if not isinstance(tabla, list):
                        tabla = []
            except Exception:
                tabla = []
        else:
            tabla = []

        resumen = {
            "timestamp": datetime.utcnow().isoformat(),
            "income": self.ingresos,
            "bonus": self.bonus_time,
            "penalizations": self.penalizacion,
            "puntaje_final": self.calcular_total(),
            "entries_count": len(self.events),
        }

        tabla.append(resumen)
        tabla.sort(key=lambda x: x.get("puntaje_final", 0), reverse=True)

        with open(self.score_file, "w", encoding="utf-8") as f:
            json.dump(tabla, f, indent=2, ensure_ascii=False)

    def exportar_reporte(self, out_path: Optional[Path] = None) -> None:
        p = Path(out_path) if out_path else (
            self.score_file.parent / f"puntaje_full_{datetime.utcnow().isoformat()}.json"
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "summary": {
                "income": self.ingresos,
                "bonus": self.bonus_time,
                "penalizations": self.penalizacion,
                "puntaje_final": self.calcular_total(),
            },
            "entries": self.events,
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)





