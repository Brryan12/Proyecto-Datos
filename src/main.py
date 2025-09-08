import pygame
from api.ManejadorAPI import ManejadorAPI
import json
from pathlib import Path
from models.CityMap import CityMap

def main():
    # --- Configuración ---
    TILE_WIDTH = 20
    TILE_HEIGHT = 22
    
    # Tamaño inicial de la ventana
    WINDOW_WIDTH = 750
    WINDOW_HEIGHT = 600
    
    # Variables para el escalado
    scale_x = 1.0
    scale_y = 1.0

    # Colores para cualquier tile que no tenga sprite asignado
    TILE_COLORS = {
        "default": (150, 150, 150)  # Gris
    }

    # --- Rutas base ---
    PROJECT_ROOT = Path(__file__).resolve().parents[1]  # Raíz del proyecto
    CACHE_DIR = PROJECT_ROOT / "cache"
    SPRITES_DIR = PROJECT_ROOT / "sprites"

    # --- Cargar datos del mapa ---
    with open(CACHE_DIR / "map.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    city_map = CityMap(**data)

    # --- Inicializar Pygame ---
    pygame.init()
    screen = pygame.display.set_mode(
        (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE
    )
    pygame.display.set_caption(city_map.city_name)
    
    # Calcular el factor de escala inicial
    scale_x = WINDOW_WIDTH / (city_map.width * TILE_WIDTH)
    scale_y = WINDOW_HEIGHT / (city_map.height * TILE_HEIGHT)

    clock = pygame.time.Clock()

    # --- Función para cargar sprites originales ---
    def cargar_sprite_original(nombre_archivo):
        ruta = SPRITES_DIR / nombre_archivo
        return pygame.image.load(ruta).convert_alpha()
    
    # --- Función para escalar sprites según el tamaño actual ---
    def escalar_sprites(sprites_originales, nuevo_ancho, nuevo_alto):
        escalados = {}
        for nombre, sprite in sprites_originales.items():
            escalados[nombre] = pygame.transform.scale(sprite, (nuevo_ancho, nuevo_alto))
        return escalados

    # --- Cargar sprites originales ---
    sprites_originales = {
        "B": cargar_sprite_original("Spr_edificio1.png"),
        "C": cargar_sprite_original("Spr_acera.png"),
        "P": cargar_sprite_original("Spr_parque.png")
    }
    
    # --- Escalar sprites para el tamaño actual ---
    sprites = escalar_sprites(sprites_originales, int(TILE_WIDTH * scale_x), int(TILE_HEIGHT * scale_y))

    # --- Bucle principal ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                # Actualizar el tamaño de la pantalla
                WINDOW_WIDTH, WINDOW_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                
                # Recalcular factores de escala
                scale_x = WINDOW_WIDTH / (city_map.width * TILE_WIDTH)
                scale_y = WINDOW_HEIGHT / (city_map.height * TILE_HEIGHT)
                
                # Calcular tamaños escalados exactos
                tile_width_scaled = max(1, int(TILE_WIDTH * scale_x))
                tile_height_scaled = max(1, int(TILE_HEIGHT * scale_y))
                
                # Reescalar sprites con el nuevo tamaño
                sprites = escalar_sprites(sprites_originales, tile_width_scaled, tile_height_scaled)

        screen.fill((0, 0, 0))
        
        # Pre-calcular el tamaño escalado para evitar errores de redondeo
        tile_width_scaled = max(1, int(TILE_WIDTH * scale_x))
        tile_height_scaled = max(1, int(TILE_HEIGHT * scale_y))
        
        for y, fila in enumerate(city_map.tiles):
            for x, code in enumerate(fila):
                # Calcular la posición escalada - usar multiplicación por enteros para evitar huecos
                pos_x = int(x * tile_width_scaled)
                pos_y = int(y * tile_height_scaled)
                
                rect = pygame.Rect(
                    pos_x,
                    pos_y,
                    tile_width_scaled,
                    tile_height_scaled
                )

                if code in sprites:
                    screen.blit(sprites[code], rect.topleft)
                else:
                    color = TILE_COLORS.get(code, TILE_COLORS["default"])
                    pygame.draw.rect(screen, color, rect)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()

