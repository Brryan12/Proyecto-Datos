import pygame
from pathlib import Path
from src.game.player import Player

def test_player():
    pygame.init()
    screen = pygame.display.set_mode((200, 200))

    sprites_dir = Path("sprites")  # carpeta donde tienes tus PNGs
    player = Player(sprites_dir, start_x=50, start_y=50)

    print("Resistencia inicial:", player.stats.resistencia)
    print("Reputación inicial:", player.reputation.valor)

    # Mover hacia la derecha con peso 4 y clima lluvia
    player.mover(dx=1, dy=0, peso_total=4, clima="rain")
    print("Nueva posición:", player.x, player.y)
    print("Resistencia después de mover:", player.stats.resistencia)

    # Simular entrega a tiempo
    player.registrar_entrega("a_tiempo")
    print("Reputación tras entrega:", player.reputation.valor)

    # Render de prueba
    screen.fill((0, 0, 0))
    player.draw(screen)
    pygame.display.flip()

    pygame.time.wait(1000)
    pygame.quit()

if __name__ == "__main__":
    test_player()
    
    
    ###HOGLHAHFSJKLÑKDSJ