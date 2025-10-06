import requests
import json
import csv
from pathlib import Path
from typing import List
from src.models.ClimaData import ClimaData
from src.models.Pedido import PedidoSolicitud
from src.models.CityMap import CityMap


class ManejadorAPI:
    BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

    def __init__(self, cache_dir: str = "cache", default_duration: int = 15 * 60):
        self.session = requests.Session()
        self.session.headers.update({"accept": "application/json"})
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)  # crea carpeta si no existe
        self.default_duration = default_duration

    # ===================== CLIMA =====================
    #Carga la información del clima a clima data.
    def get_weather(self, city: str, mode: str = "seed", save: bool = True) -> ClimaData:
        url = f"{self.BASE_URL}/city/weather"
        params = {"city": city, "mode": mode}

        response = self.session.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        clima = ClimaData(**payload["data"])

        if save:
            self.save_to_json(clima, f"{city}_weather.json")
            self.save_to_csv(clima, f"{city}_weather.csv")

        return clima

    #Guarda los archivos en formato JSON
    def save_to_json(self, data, filename: str):
        filepath = self.cache_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            if hasattr(data, "model_dump"):  # Pydantic v2
                json.dump(data.model_dump(), f, indent=4, ensure_ascii=False)
            elif hasattr(data, "dict"):  # Pydantic v1
                json.dump(data.dict(), f, indent=4, ensure_ascii=False)
            else:
                json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Saved JSON to {filepath}")

    #Carga los archivos en formato JSON
    def load_from_json(self, filename: str):
        filepath = self.cache_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    #Guarda los archivos en formato CSV
    def save_to_csv(self, clima: ClimaData, filename: str):
        filepath = self.cache_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["from_condition", "to_condition", "probability"])
            for from_cond, to_map in clima.transition.items():
                for to_cond, prob in to_map.items():
                    writer.writerow([from_cond, to_cond, prob])
        print(f"Transiciones de clima salvados en {filepath}")

    # ===================== PEDIDOS =====================
    def get_jobs(self, save: bool = True) -> List[PedidoSolicitud]:
        url = f"{self.BASE_URL}/city/jobs"
        response = self.session.get(url)
        response.raise_for_status()
        payload = response.json()

        # Convierte los pedidos.
        jobs = []
        for job in payload["data"]:
            jobs.append(PedidoSolicitud(
                id=job["id"],
                pickup=job["pickup"],
                dropoff=job["dropoff"],
                payout=job["payout"],
                duration=self.default_duration, #Se ignora el deadline del API
                weight=job["weight"],
                priority=job["priority"],
                release_time=job["release_time"]
            ))

        if save:
            self.save_to_json([job.dict() for job in jobs], "jobs.json")
            self.save_jobs_to_csv(jobs, "jobs.csv")

        return jobs

        #Guarda los pedidos en CSV
    def save_jobs_to_csv(self, jobs: List[PedidoSolicitud], filename: str):
        filepath = self.cache_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id", "pickup_x", "pickup_y", "dropoff_x", "dropoff_y",
                "payout", "duration", "weight", "priority", "release_time"
            ])
            for job in jobs:
                writer.writerow([
                    job.id,
                    job.pickup[0], job.pickup[1],
                    job.dropoff[0], job.dropoff[1],
                    job.payout,
                    job.duration,   #En sustitución del deadlone, se guarda la duración.
                    job.weight,
                    job.priority,
                    job.release_time
                ])
        print(f"Jobs saved to {filepath}")

    # ===================== MAPA =====================
    #Recoge la información del mapa para guardarlo en CityMap.
    def get_map(self, save: bool = True) -> CityMap:
        url = f"{self.BASE_URL}/city/map"
        response = self.session.get(url)
        response.raise_for_status()
        payload = response.json()

        city_map = CityMap(**payload["data"])

        if save:
            self.save_to_json(city_map.dict(), "map.json")
            self.save_map_to_csv(city_map, "map.csv")

        return city_map

    #Carga el mapa usando JSON
    def load_map_from_json(self, filename: str = "map.json") -> CityMap:
        filepath = self.cache_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return CityMap(**data)

    #Guarda mapa usando CSV
    def save_map_to_csv(self, city_map: CityMap, filename: str):
        filepath = self.cache_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y", "code", "name", "surface_weight", "blocked"])
            for tile in city_map.iterar_elementos():
                writer.writerow([
                    tile.x,
                    tile.y,
                    tile.codigo,
                    tile.name,
                    tile.surface_weight,
                    tile.blocked
                ])
        print(f"Mapa guardado en {filepath}")

    def update_data(self):
        """Descarga y actualiza todos los datos (clima, jobs, mapa)"""
        print("Actualizando datos desde la API...")
        city = "TigerCity"
        self.get_weather(city, mode="seed", save=True)
        self.get_jobs(save=True)
        self.get_map(save=True)
        print("Datos actualizados exitosamente")
