import pygame
from pathlib import Path
from src.game.stats_module import Stats
from src.game.reputation import Reputation

class Player(pygame.sprite.Sprite):
    def __init__(self, sprites_dir: Path, start_x = 0, start_y = 0):
        super().__init__()

        self.x = start_x
        self.y = start_y

        self.stats = Stats()
        self.reputation = Reputation()

        self.direccion = "down"

        self.sprites = {
            "up": pygame.image.load(sprites_dir / "Spr_delivery_up.png").convert_alpha(),
            "down": pygame.image.load(sprites_dir / "Spr_delivery_down.png").convert_alpha(),
            "left": pygame.image.load(sprites_dir / "Spr_delivery_izq.png").convert_alpha(),
            "right": pygame.image.load(sprites_dir / "Spr_delivery_der.png").convert_alpha(),
        }

        self.image = self.sprites[self.direccion]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

        self.base_speed = 4

    
    def mover(self, dx: int, dy: int, peso_total = 0.0, clima = "clear"):

        if not self.stats.puede_moverse():
            return
        
        if dx < 0:
            self.direccion = "left"
        elif dx > 0:
            self.direccion = "right"
        elif dy < 0:
            self.direccion = "up"
        elif dy > 0:
            self.direccion = "down"
        
        factor = self.stats.factor_velocidad()
        real_speed = int(self.base_speed * factor)

        self.x += dx * real_speed
        self.y += dy * real_speed
        self.rect.topleft = (self.x, self.y)
        self.stats.consume_por_mover(celdas = 1, peso_total=peso_total, condicion_clima=clima)

        self.image = self.sprites[self.direccion]

    def registrar_entrega(self, estado: str):
        self.reputation.registrar_entrega(estado)

    
    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect.topleft)

    def nuevo_dia(self):
        self.reputation.reset_diario()
