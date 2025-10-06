import pygame
from pathlib import Path
from typing import Optional
from src.game.stats_module import Stats
from src.game.reputation import Reputation
from src.game.save import Save
from src.game.score import Score


class Player(pygame.sprite.Sprite):


    def __init__(self, sprites_dir: Path, stats: Stats, reputation: Reputation, tile_width: int, tile_height: int, start_x: int = 0, start_y: int = 0, save_data: Save = None, player_name: str = None):
        super().__init__()

        # --- Estado base ---
        self.x = start_x
        self.y = start_y
        self.name = player_name if player_name else "Sin Nombre"

        # --- Cargar progreso guardado si existe ---
        if save_data: 
            try: 
                x, y = save_data.position 
                self.x = int(float(x)) 
                self.y = int(float(y)) 
            except Exception: 
                print(f"[WARN] Posición inválida en guardado: {save_data.position}, usando (0,0)") 
                self.x, self.y = 0, 0 
        else: 
            self.x, self.y = int(start_x), int(start_y)

        self.stats = stats
        self.reputation = reputation
        
        # Inicializar score como entidad propia del jugador con archivo específico
        from pathlib import Path
        score_file = Path(__file__).resolve().parent / "saves" / "savedScores.json"
        self.score = Score(score_file=score_file)

        # Si viene un guardado, sincronizamos reputación y score 
        if save_data: 
            self.reputation.valor = save_data.reputation 
            # Restaurar score desde guardado
            if hasattr(save_data, 'score') and save_data.score:
                # Como save_data.score es un int, inicializamos con ingresos
                self.score.ingresos = float(save_data.score)
            if hasattr(save_data, 'player_name') and save_data.player_name:
                self.name = save_data.player_name

        # dirección inicial
        self.direccion = "down"

        # cargar sprites (asegúrate que los nombres coincidan en la carpeta /sprites)
        self.sprites = {
            "up": pygame.image.load(sprites_dir / "Spr_delivery_up.png").convert_alpha(),
            "down": pygame.image.load(sprites_dir / "Spr_delivery_down.png").convert_alpha(),
            "izq": pygame.image.load(sprites_dir / "Spr_delivery_izq.png").convert_alpha(),
            "der": pygame.image.load(sprites_dir / "Spr_delivery_der.png").convert_alpha(),
        }

        # scale sprites to tile size
        self.sprites = {k: pygame.transform.scale(v, (tile_width, tile_height)) for k, v in self.sprites.items()}

        self.tile_width = tile_width
        self.tile_height = tile_height
        
        self.image = self.sprites[self.direccion]
        # Calcular posiciones exactas para el centrado
        center_x = self.x + tile_width // 2
        center_y = self.y + tile_height // 2
        
        # Inicializar rect con el centro en el centro exacto de la casilla
        self.rect = self.image.get_rect(center=(center_x, center_y))

        # velocidad base en píxeles/frame (equivalente a v0 = 3 celdas/seg)
        self.base_speed = 4
        
        # Inventario - peso total que lleva el jugador
        self.peso_total = 0.0
        
        # Último tile pisado (para surface_weight)
        self.current_tile_info = None
        
        # Variable para almacenar la velocidad actual calculada
        self.velocidad_actual = self.base_speed
        
    def calcular_velocidad(self, clima_factor: float = 1.0, surface_weight: float = 1.0) -> float:
        """
        Calcula la velocidad actual según la fórmula:
        v = v0 * Mclima * Mpeso * Mrep * Mresistencia * surface_weight
        
        Returns:
            float: Velocidad calculada en píxeles/frame
        """
        # Velocidad base (v0)
        v0 = self.base_speed
        
        # Mclima - multiplicador por clima (pasado como parámetro)
        m_clima = clima_factor
        
        # Mpeso = max(0.8, 1 - 0.03 * peso_total)
        m_peso = max(0.8, 1 - 0.03 * self.peso_total)
        
        # Mrep - multiplicador por reputación
        m_rep = 1.03 if self.reputation.valor >= 90 else 1.0
        
        # Mresistencia - factor por estado de cansancio
        m_resistencia = self.stats.factor_velocidad()
        
        # Superficie - factor por tipo de terreno
        m_superficie = surface_weight
        
        # Calcular velocidad final
        velocidad = v0 * m_clima * m_peso * m_rep * m_resistencia * m_superficie
        
        return velocidad

    def mover(self, direccion: str, peso_total: float = 0.0, clima: str = "clear", clima_factor: float = 1.0, tile_info: Optional[float] = None):

        if not self.stats.puede_moverse():
            print("Jugador exhausto, no puede moverse.")
            return  # no puede moverse si está exhausto

        if direccion == "up":
            dx, dy = (0, -1)
        elif direccion == "down":
            dx, dy = (0, 1)
        elif direccion == "izq":
            dx, dy = (-1, 0)
        elif direccion == "der":
            dx, dy = (1, 0)
        else:
            dx, dy = (0, 0)

        if dx == 0 and dy == 0:
            return

        self.direccion = direccion
        
        # Actualizar peso total si se proporciona
        if peso_total > 0:
            self.peso_total = peso_total
            
        # Obtener factor de superficie si está disponible
        surface_weight = 1.0
        if tile_info:
            # Extraer el valor surface_weight del objeto TileInfo
            if hasattr(tile_info, 'surface_weight') and tile_info.surface_weight is not None:
                surface_weight = tile_info.surface_weight
            self.current_tile_info = tile_info
            
        # Calcular velocidad real usando la fórmula completa
        velocidad = self.calcular_velocidad(clima_factor=clima_factor, surface_weight=surface_weight)
        real_speed = int(velocidad)
        
        # Guardar la velocidad actual para poder mostrarla en el HUD
        self.velocidad_actual = velocidad
        
        # Mover al jugador con mejor control de colisiones
        new_x = self.x + dx * real_speed
        new_y = self.y + dy * real_speed
        
        # Actualizar posición
        self.x = new_x
        self.y = new_y
        
        # Asegurarnos de que el jugador esté perfectamente alineado con la cuadrícula
        # Calcular la casilla actual
        current_tile_x = int(self.x // self.tile_width)
        current_tile_y = int(self.y // self.tile_height)
        
        # Calcular el centro exacto de la casilla
        center_x = (current_tile_x * self.tile_width) + (self.tile_width // 2)
        center_y = (current_tile_y * self.tile_height) + (self.tile_height // 2)
        
        # Alinear el centro del rectángulo con el centro de la casilla
        self.rect.center = (center_x, center_y)

        # Consumir resistencia por movimiento
        self.stats.consume_por_mover(celdas=1, peso_total=self.peso_total, condicion_clima=clima)

        self.image = self.sprites[self.direccion]

    def registrar_entrega(self, estado: str):
        self.reputation.registrar_entrega(estado)

    def draw(self, screen: pygame.Surface):
        """
        Dibuja el sprite del jugador en la pantalla.
        Usa el rectángulo centrado para posicionar correctamente el sprite.
        
        Args:
            screen: Superficie de pygame donde dibujar
        """
        # Dibujar el sprite usando el rectángulo que ya está centrado
        # Usamos el método rect.topleft para que pygame dibuje desde la esquina superior izquierda
        screen.blit(self.image, self.rect.topleft)

    def nuevo_dia(self):
        self.reputation.reset_diario()
    
    def agregar_ingreso(self, payout: float, meta=None):
        """Agregar ingresos al score del jugador"""
        return self.score.agregar_ingreso(payout, self.reputation.valor, meta)
    
    def agregar_bono(self, cantidad: float, motivo: str, meta=None):
        """Agregar bono al score del jugador"""
        self.score.agregar_bono(cantidad, motivo, meta)
    
    def agregar_penalizacion(self, cantidad: float, motivo: str, meta=None):
        """Agregar penalización al score del jugador"""
        self.score.agregar_penalizacion(cantidad, motivo, meta)
    
    def obtener_score_total(self) -> int:
        """Obtener el score total calculado"""
        return self.score.calcular_total()

    def exportar_estado(self, player_name, day, city_name=None, score=None, reputation=None, position=None, current_weather=None):
        return Save(
        player_name=player_name,
        day=day if day else 1,
        city_name=city_name if city_name is not None else "TigerCity",
        score=self.score.calcular_total(),
        reputation=self.reputation.valor,
        position=(int(self.x), int(self.y)),
        completed_jobs=[],  # puedes llenar si tienes jobs completados
        current_weather=current_weather
    )