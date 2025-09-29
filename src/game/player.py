import pygame
from pathlib import Path
from src.game.stats_module import Stats
from src.game.reputation import Reputation


class Player(pygame.sprite.Sprite):


    def __init__(self, sprites_dir: Path, stats: Stats, reputation: Reputation, start_x: int = 0, start_y: int = 0):
        super().__init__()

        # --- Estado base ---
        self.x = start_x
        self.y = start_y

        self.stats = stats
        self.reputation = reputation

        # dirección inicial
        self.direccion = "down"

        # cargar sprites (asegúrate que los nombres coincidan en la carpeta /sprites)
        self.sprites = {
            "up": pygame.image.load(sprites_dir / "Spr_delivery_up.png").convert_alpha(),
            "down": pygame.image.load(sprites_dir / "Spr_delivery_down.png").convert_alpha(),
            "izq": pygame.image.load(sprites_dir / "Spr_delivery_izq.png").convert_alpha(),
            "der": pygame.image.load(sprites_dir / "Spr_delivery_der.png").convert_alpha(),
        }

        self.image = self.sprites[self.direccion]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

        # velocidad base en píxeles/frame
        self.base_speed = 4

    def mover(self, direccion: str, peso_total: float = 0.0, clima: str = "clear"):

        if not self.stats.puede_moverse():
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

        factor = self.stats.factor_velocidad()
        real_speed = int(self.base_speed * factor)

        self.x += dx * real_speed
        self.y += dy * real_speed
        self.rect.topleft = (self.x, self.y)

        self.stats.consume_por_mover(celdas=1, peso_total=peso_total, condicion_clima=clima)

        self.image = self.sprites[self.direccion]

    def registrar_entrega(self, estado: str):
        self.reputation.registrar_entrega(estado)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect.topleft)

    def nuevo_dia(self):
        self.reputation.reset_diario()
