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

    def __init__(self, player, gestor, notificador, undo_system, inventario=None, recoger_callback=None, entregar_callback=None, pedidos_data=None, 
                 map_logic=None, sistema_clima=None, tiempo_actual=None):
        self.player = player
        self.gestor = gestor
        self.notificador = notificador
        self.undo_system = undo_system
        self.inventario = inventario
        self.recoger_callback = recoger_callback
        self.entregar_callback = entregar_callback
        self.pedidos_data = pedidos_data  # Para acceder a pedidos, pedidos_recogidos, pedidos_entregados
        
        # Para el sistema de movimiento integrado
        self.map_logic = map_logic
        self.sistema_clima = sistema_clima
        self.tiempo_actual = tiempo_actual
        
        # Estado de movimiento
        self.moved = False

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

                # Recoger paquete (tecla N)
                elif event.key == pygame.K_n and self.recoger_callback and self.pedidos_data:
                    self._manejar_recoger_paquete()

                # Entregar paquete (tecla M)
                elif event.key == pygame.K_m and self.entregar_callback and self.pedidos_data:
                    self._manejar_entregar_paquete()

                # Pausar el juego
                elif event.key == pygame.K_ESCAPE:
                    return "pausa"

        return None

    def _manejar_recoger_paquete(self):
        """Maneja la acción de recoger un paquete con la tecla N"""
        if not self.pedidos_data or not self.recoger_callback:
            return
        
        pedidos = self.pedidos_data.get('pedidos', [])
        pedidos_recogidos = self.pedidos_data.get('pedidos_recogidos', [])
        es_adyacente = self.pedidos_data.get('es_adyacente_func')
        
        if not es_adyacente:
            return
        
        # Convertir posición del jugador a coordenadas de tile
        if self.map_logic:
            player_tile_pos = self.map_logic.get_player_tile_pos(self.player.rect)
        else:
            # Fallback usando posición directa
            player_tile_pos = (self.player.x // self.player.tile_width, self.player.y // self.player.tile_height)
        
        # Buscar pedidos adyacentes que no han sido recogidos
        for pedido in pedidos:
            if pedido not in pedidos_recogidos:
                if es_adyacente(player_tile_pos, tuple(pedido.pickup)):
                    self.recoger_callback(pedido)
                    break

    def _manejar_entregar_paquete(self):
        """Maneja la acción de entregar un paquete con la tecla M"""
        if not self.pedidos_data or not self.entregar_callback or not self.inventario:
            return
        
        pedidos_entregados = self.pedidos_data.get('pedidos_entregados', [])
        es_adyacente = self.pedidos_data.get('es_adyacente_func')
        
        if not es_adyacente:
            return
        
        # Convertir posición del jugador a coordenadas de tile
        if self.map_logic:
            player_tile_pos = self.map_logic.get_player_tile_pos(self.player.rect)
        else:
            # Fallback usando posición directa
            player_tile_pos = (self.player.x // self.player.tile_width, self.player.y // self.player.tile_height)
        
        # Buscar pedidos en el inventario que pueden ser entregados
        pedidos_en_inventario = self.inventario.get_orders()
        for pedido in pedidos_en_inventario:
            if pedido not in pedidos_entregados and es_adyacente(player_tile_pos, tuple(pedido.dropoff)):
                self.entregar_callback(pedido)
                break

    def manejar_movimiento(self, keys, dt):
        """Maneja el movimiento del jugador con el sistema integrado"""
        if not self.map_logic or not self.sistema_clima:
            return False
        
        self.moved = False
        
        # Solo procesar movimiento si no hay notificación activa
        if self.notificador.activo:
            return False
        
        # Obtener posición actual del jugador en tiles
        px, py = self.map_logic.get_player_tile_pos(self.player.rect)
        new_x, new_y = px, py
        direccion = None
        
        # Determinar dirección basada en teclas presionadas
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= 1
            direccion = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += 1
            direccion = "down"
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= 1
            direccion = "izq"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += 1
            direccion = "der"
        
        # Si hay movimiento y no hay colisión
        if direccion and not self.map_logic.is_blocked(new_x, new_y):
            # Obtener información del tile para surface_weight
            tile_info = self.map_logic.get_tile_info(new_x, new_y)
            
            # Obtener datos del clima
            condicion = self.sistema_clima.obtener_condicion()
            efectos = self.sistema_clima.obtener_efectos()
            clima_factor = efectos["factor_velocidad"]
            
            # Calcular peso del inventario
            peso_inventario = self.gestor.inventory.current_weight()
            
            # Mover al jugador con todos los factores
            self.player.mover(
                direccion=direccion,
                peso_total=peso_inventario,
                clima=condicion,
                clima_factor=clima_factor,
                tile_info=tile_info,
            )
            self.moved = True
            
            # Guardar estado después de un movimiento exitoso
            pedidos_activos_ids = [p.id for p in self.gestor.ver_pedidos()]
            self.undo_system.save_state(self.player, self.tiempo_actual(), pedidos_activos_ids)
        
        # Si no se movió, recuperar resistencia
        if not self.moved:
            self.player.stats.recupera(segundos=dt, rest_point=False)
        
        return self.moved
