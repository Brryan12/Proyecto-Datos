# map_rend.py
import pygame
from pathlib import Path
from typing import Optional, Tuple

from src.models.CityMap import CityMap


class MapRenderer:
    TILE_COLORS = {
        "B": (120, 120, 120),  # edificio (fallback)
        "C": (200, 200, 200),  # calle (fallback)
        "P": (130, 200, 130),  # parque (fallback)
        "default": (150, 150, 150),
    }

    def __init__(
        self,
        city_map: CityMap,
        sprites_dir: Path,
        tile_width: int = 40,
        tile_height: int = 44,
        viewport_size: Optional[Tuple[int, int]] = None, #Dupla para el viewport, el cual da la ubicación en x y y con ints.
    ):
        self.city_map = city_map
        self.sprites_dir = Path(sprites_dir)
        self.tile_width = int(tile_width)
        self.tile_height = int(tile_height)
        self.camera_x = 0
        self.camera_y = 0

        self.viewport_size = viewport_size

        self.sprites: dict[str, Optional[pygame.Surface]] = {}
        self._cargar_sprites()

    def _cargar_sprite(self, filename: str) -> Optional[pygame.Surface]:
        ruta = self.sprites_dir / filename
        try:
            surf = pygame.image.load(str(ruta)).convert_alpha()
            return pygame.transform.scale(surf, (self.tile_width, self.tile_height))
        except Exception as e:
            print(f"[MapRenderer] Warning: no se pudo cargar sprite '{ruta}': {e}")
            return None

    def _cargar_sprites(self):
        self.sprites["B"] = self._cargar_sprite("Spr_edificio1.png")
        self.sprites["C"] = self._cargar_sprite("Spr_acera.png")
        self.sprites["P"] = self._cargar_sprite("Spr_parque.png")
        
        # Cargar sprites para paquetes y puntos de entrega
        self.sprites["package"] = self._cargar_sprite("package.png")
        self.sprites["delivery_point"] = self._cargar_sprite("delivery_point.png")

    def set_camera_pos(self, px: int, py: int) -> None:
        self.camera_x = int(px)
        self.camera_y = int(py)
        self._clamp_camera()

    def move_camera(self, dx: int, dy: int) -> None:
        self.camera_x += int(dx)
        self.camera_y += int(dy)
        self._clamp_camera()

    def center_camera_on_tile(self, tx: int, ty: int, screen_size: Optional[Tuple[int,int]] = None) -> None:
        sw, sh = screen_size if screen_size else self.viewport_size if self.viewport_size else (800, 600)
        self.camera_x = tx * self.tile_width - sw // 2 + self.tile_width // 2
        self.camera_y = ty * self.tile_height - sh // 2 + self.tile_height // 2
        self._clamp_camera()

    def _clamp_camera(self):
        max_px = max(0, self.city_map.width * self.tile_width - 1)
        max_py = max(0, self.city_map.height * self.tile_height - 1)
        self.camera_x = max(0, min(self.camera_x, max_px))
        self.camera_y = max(0, min(self.camera_y, max_py))

    def tile_to_screen(self, x: int, y: int) -> Tuple[int, int]:
        sx = x * self.tile_width - self.camera_x
        sy = y * self.tile_height - self.camera_y
        return int(sx), int(sy)

    def screen_to_tile(self, sx: int, sy: int) -> Tuple[int, int]:
        tx = (sx + self.camera_x) // self.tile_width
        ty = (sy + self.camera_y) // self.tile_height
        return int(tx), int(ty)

    # ---------------- Dibujo ----------------
    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        viewport_w, viewport_h = (self.viewport_size if self.viewport_size else (sw, sh))

        # rango visible en tiles (clamped al mapa)
        start_x = max(0, self.camera_x // self.tile_width)
        start_y = max(0, self.camera_y // self.tile_height)
        end_x = min(self.city_map.width, (self.camera_x + viewport_w) // self.tile_width + 1)
        end_y = min(self.city_map.height, (self.camera_y + viewport_h) // self.tile_height + 1)

        for y in range(start_y, end_y): #dibuja los tiles de x y y, usando los sprites que corresponden.
            fila = self.city_map.tiles[y]
            for x in range(start_x, end_x):
                code = fila[x]
                sx, sy = self.tile_to_screen(x, y)
                rect = pygame.Rect(sx, sy, self.tile_width, self.tile_height)
                sprite = self.sprites.get(code)
                if sprite:
                    screen.blit(sprite, rect.topleft)
                else:
                    color = self.TILE_COLORS.get(code, self.TILE_COLORS["default"])
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (50, 50, 50), rect, 1)

    def draw_package_icons(self, screen: pygame.Surface, pedidos_activos, pedidos_recogidos=None, pedidos_entregados=None) -> None:
        """Dibuja íconos de paquetes en las posiciones de recogida y entrega.
        
        Args:
            pedidos_activos: Lista de todos los pedidos activos
            pedidos_recogidos: Lista de pedidos que han sido recogidos (no mostrar pickup)
            pedidos_entregados: Lista de pedidos que han sido entregados (no mostrar dropoff)
        """
        if pedidos_recogidos is None:
            pedidos_recogidos = []
        if pedidos_entregados is None:
            pedidos_entregados = []
            
        for pedido in pedidos_activos:
            # Dibujar paquete en posición de recogida (pickup) SOLO si NO ha sido recogido
            if pedido not in pedidos_recogidos:
                pickup_x, pickup_y = pedido.pickup
                sx, sy = self.tile_to_screen(pickup_x, pickup_y)
                
                # Verificar que esté dentro del viewport
                if self._is_tile_visible(pickup_x, pickup_y):
                    package_sprite = self.sprites.get("package")
                    if package_sprite:
                        screen.blit(package_sprite, (sx, sy))
                    else:
                        pygame.draw.rect(screen, (255, 255, 0), (sx, sy, self.tile_width, self.tile_height))
                        pygame.draw.rect(screen, (200, 200, 0), (sx, sy, self.tile_width, self.tile_height), 2)
            
            # Dibujar punto de entrega (dropoff) SOLO si ha sido recogido pero NO entregado
            if pedido in pedidos_recogidos and pedido not in pedidos_entregados:
                dropoff_x, dropoff_y = pedido.dropoff
                sx, sy = self.tile_to_screen(dropoff_x, dropoff_y)
                
                # Verificar que esté dentro del viewport
                if self._is_tile_visible(dropoff_x, dropoff_y):
                    delivery_sprite = self.sprites.get("delivery_point")
                    if delivery_sprite:
                        screen.blit(delivery_sprite, (sx, sy))
                    else:
                        pygame.draw.rect(screen, (255, 100, 100), (sx, sy, self.tile_width, self.tile_height))
                        pygame.draw.rect(screen, (200, 50, 50), (sx, sy, self.tile_width, self.tile_height), 2)

    def _is_tile_visible(self, tx: int, ty: int) -> bool:
        """Verifica si una casilla está visible en el viewport (elemento gráfico) actual."""
        viewport_w, viewport_h = (self.viewport_size if self.viewport_size else (800, 600))
        
        start_x = max(0, self.camera_x // self.tile_width)
        start_y = max(0, self.camera_y // self.tile_height)
        end_x = min(self.city_map.width, (self.camera_x + viewport_w) // self.tile_width + 1)
        end_y = min(self.city_map.height, (self.camera_y + viewport_h) // self.tile_height + 1)
        
        return start_x <= tx < end_x and start_y <= ty < end_y
