import pygame

class Events:
    """
    Clase encargada de manejar todos los eventos del juego.
    Controla:
    - Movimiento del jugador
    - Sistema de deshacer
    - Interacción con el notificador
    - Pausa y salida del juego
    """

    def __init__(self, player, gestor, notificador, undo_system, inventario=None):
        self.player = player
        self.gestor = gestor
        self.notificador = notificador
        self.undo_system = undo_system
        self.inventario = inventario

        # Velocidad base del jugador
        self.velocidad = 5

    def procesar_eventos(self):
        """
        Procesa los eventos de pygame.

        Retorna:
            "salir"  -> si el usuario cierra la ventana
            "pausa"  -> si el usuario presiona ESC
            None     -> si no hay evento de control
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "salir"
            
            # Manejar eventos del notificador (Z/X para aceptar/rechazar pedidos)
            if self.notificador.manejar_eventos(event, self.gestor):
                continue  # Evento ya procesado por el notificador
            
            # Manejar sistema de deshacer
            if event.type == pygame.KEYDOWN:
                # Alternar inventario (tecla I)
                if event.key == pygame.K_i and self.inventario:
                    self.inventario.toggle_inventario()

                # Deshacer un movimiento (tecla U)
                elif event.key == pygame.K_u and not self.notificador.activo:
                    self.undo_system.undo_last_move(self.player, self.gestor)

                # Deshacer múltiples movimientos (tecla R + número)
                elif event.key == pygame.K_r and not self.notificador.activo:
                    keys_pressed = pygame.key.get_pressed()
                    undo_count = 1
                    
                    # Permitir deshacer más pasos con números
                    if keys_pressed[pygame.K_1]: undo_count = 1
                    elif keys_pressed[pygame.K_2]: undo_count = 2
                    elif keys_pressed[pygame.K_3]: undo_count = 3
                    elif keys_pressed[pygame.K_4]: undo_count = 4
                    elif keys_pressed[pygame.K_5]: undo_count = 5
                    
                    self.undo_system.undo_n_moves(self.player, undo_count, self.gestor)

        # Movimiento del jugador (WASD o flechas)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -self.velocidad
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = self.velocidad
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -self.velocidad
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = self.velocidad

        # Actualizar posición del jugador
        if dx != 0 or dy != 0:
            self.player.mover(dx, dy)

        # Pausar el juego
        if keys[pygame.K_ESCAPE]:
            return "pausa"

        return None
