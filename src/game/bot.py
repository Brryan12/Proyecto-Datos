"""
Bot AI para Courier Quest
Implementa 3 niveles de dificultad con diferentes algoritmos de pathfinding y estrategias.
"""

import pygame
import heapq
import random
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Set
from collections import deque
from src.game.player import Player
from src.game.stats_module import Stats
from src.game.reputation import Reputation
from src.game.save import Save


class Bot(Player):
    """
    Bot AI que hereda de Player y agrega capacidades de decisión autónoma.
    
    Niveles de dificultad:
    - EASY: Movimiento aleatorio con tendencia al objetivo (Random Walk)
    - MEDIUM: BFS (Breadth-First Search) - encuentra camino pero no el óptimo
    - HARD: Dijkstra - encuentra el camino más eficiente considerando costos
    """
    
    # Constantes para niveles de dificultad
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    
    def __init__(
        self, 
        sprites_dir: Path, 
        stats: Stats, 
        reputation: Reputation, 
        tile_width: int, 
        tile_height: int, 
        start_x: int = 0, 
        start_y: int = 0, 
        save_data: Save = None, 
        player_name: str = "Bot",
        difficulty: str = MEDIUM,
        map_logic = None,
        inventario = None
    ):
        """
        Inicializa el bot con un nivel de dificultad específico.
        
        Args:
            difficulty: Nivel de dificultad (EASY, MEDIUM, HARD)
            map_logic: Referencia al MapLogic para pathfinding
            inventario: Referencia al inventario para gestión de paquetes
        """
        super().__init__(
            sprites_dir=sprites_dir,
            stats=stats,
            reputation=reputation,
            tile_width=tile_width,
            tile_height=tile_height,
            start_x=start_x,
            start_y=start_y,
            save_data=save_data,
            player_name=player_name
        )
        
        self.difficulty = difficulty
        self.map_logic = map_logic
        self.inventario = inventario
        
        # Estado interno del bot
        self.current_path: List[Tuple[int, int]] = []
        self.current_goal: Optional[Tuple[int, int]] = None
        self.current_task: Optional[str] = None  # "pickup", "deliver", "explore"
        self.target_package = None
        
        # Configuración por dificultad
        self.config = self._get_difficulty_config()
        
        # Contador para decisiones periódicas
        self.decision_counter = 0
        self.decision_interval = self.config['decision_interval']
        
    def _get_difficulty_config(self) -> Dict:
        """Retorna configuración específica por dificultad"""
        configs = {
            self.EASY: {
                'decision_interval': 60,  # Frames entre decisiones
                'random_chance': 0.3,     # 30% chance de movimiento aleatorio
                'look_ahead': 3,          # Tiles que mira adelante
                'mistake_chance': 0.2,    # 20% chance de error
            },
            self.MEDIUM: {
                'decision_interval': 30,
                'random_chance': 0.1,
                'look_ahead': 10,
                'mistake_chance': 0.05,
            },
            self.HARD: {
                'decision_interval': 20,
                'random_chance': 0.0,
                'look_ahead': float('inf'),
                'mistake_chance': 0.0,
            }
        }
        return configs.get(self.difficulty, configs[self.MEDIUM])
    
    def update(self, dt: float, pedidos: List, clima_factor: float = 1.0):
        """
        Actualización principal del bot cada frame.
        
        Args:
            dt: Delta time
            pedidos: Lista de pedidos disponibles
            clima_factor: Factor de clima que afecta velocidad
        """
        # Guardar posición anterior para comparar
        old_pos = self._get_tile_pos()
        
        self.decision_counter += 1
        
        # Tomar decisiones periódicamente
        if self.decision_counter >= self.decision_interval:
            self.decision_counter = 0
            self._make_decision(pedidos)
        
        # Ejecutar movimiento según el path actual
        moved = False
        if self.current_path and self.stats.puede_moverse():
            self._follow_path(clima_factor)
            # Ver si realmente se movió
            new_pos = self._get_tile_pos()
            moved = (old_pos != new_pos)
        
        # Regenerar resistencia si NO se movió
        if not moved:
            self.stats.recupera(segundos=dt, rest_point=False)
    
    def _make_decision(self, pedidos: List):
        """Decide qué hacer basándose en el estado actual y pedidos disponibles"""
        
        # Verificar si cometemos un error (solo en dificultades bajas)
        if random.random() < self.config['mistake_chance']:
            self._make_random_decision()
            return
        
        # Prioridad 1: Si tenemos paquetes, entregarlos
        if self.inventario and len(self.inventario.get_orders()) > 0:
            packages = self.inventario.get_orders()
            # Ordenar por prioridad o tiempo
            packages = sorted(packages, key=lambda p: p.priority, reverse=True)
            target = packages[0]
            self.current_task = "deliver"
            self.target_package = target
            self.current_goal = tuple(target.dropoff)
            self._plan_path_to(self.current_goal)
            return
        
        # Prioridad 2: Recoger paquetes disponibles
        if pedidos:
            # Filtrar paquetes no recogidos
            available = [p for p in pedidos if not self._is_package_picked(p)]
            if available:
                # Elegir el más cercano o más prioritario según dificultad
                target = self._choose_best_package(available)
                self.current_task = "pickup"
                self.target_package = target
                self.current_goal = tuple(target.pickup)
                self._plan_path_to(self.current_goal)
                return
        
        # Prioridad 3: Explorar (movimiento aleatorio)
        self.current_task = "explore"
        self._make_random_decision()
    
    def _is_package_picked(self, package) -> bool:
        """Verifica si un paquete ya fue recogido"""
        if not self.inventario:
            return False
        return package in self.inventario.get_orders()
    
    def _choose_best_package(self, packages: List):
        """Elige el mejor paquete según la dificultad"""
        current_pos = self._get_tile_pos()
        
        if self.difficulty == self.EASY:
            # Easy: Aleatorio de los 3 más cercanos
            packages = sorted(packages, key=lambda p: self._manhattan_distance(current_pos, tuple(p.pickup)))
            candidates = packages[:min(3, len(packages))]
            return random.choice(candidates)
        
        elif self.difficulty == self.MEDIUM:
            # Medium: El más cercano
            return min(packages, key=lambda p: self._manhattan_distance(current_pos, tuple(p.pickup)))
        
        else:  # HARD
            # Hard: Mejor combinación de distancia y prioridad
            def score(p):
                dist = self._manhattan_distance(current_pos, tuple(p.pickup))
                priority = p.priority
                time_left = p.duration
                return (priority * 10) - (dist * 0.5) + (time_left * 0.1)
            
            return max(packages, key=score)
    
    def _plan_path_to(self, goal: Tuple[int, int]):
        """Planifica un camino al objetivo usando el algoritmo apropiado"""
        if not self.map_logic:
            return
        
        start = self._get_tile_pos()
        
        # Verificar si el objetivo está bloqueado
        if self.map_logic.is_blocked(goal[0], goal[1]):
            # Si el objetivo está bloqueado, buscar un tile adyacente válido
            neighbors = [
                (goal[0], goal[1] - 1),  # Arriba
                (goal[0], goal[1] + 1),  # Abajo
                (goal[0] - 1, goal[1]),  # Izquierda
                (goal[0] + 1, goal[1]),  # Derecha
            ]
            valid_neighbors = [n for n in neighbors if not self.map_logic.is_blocked(n[0], n[1])]
            if valid_neighbors:
                # Usar el vecino más cercano a nuestra posición actual
                goal = min(valid_neighbors, key=lambda n: self._manhattan_distance(start, n))
            else:
                # No hay vecinos válidos, cancelar
                self.current_path = []
                return
        
        if self.difficulty == self.EASY:
            # Easy: Movimiento aleatorio con tendencia
            self.current_path = self._random_walk_path(start, goal)
        
        elif self.difficulty == self.MEDIUM:
            # Medium: BFS
            self.current_path = self._bfs_path(start, goal)
        
        else:  # HARD
            # Hard: Dijkstra
            self.current_path = self._dijkstra_path(start, goal)
    
    def _random_walk_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Movimiento aleatorio con tendencia hacia el objetivo.
        No garantiza llegar, pero es más humano e impredecible.
        """
        path = []
        current = start
        max_steps = 20  # Límite para evitar loops infinitos
        
        for _ in range(max_steps):
            if current == goal:
                break
            
            # 70% chance de moverse hacia el objetivo
            if random.random() > self.config['random_chance']:
                # Movimiento inteligente
                neighbors = self._get_valid_neighbors(current)
                if neighbors:
                    # Elegir el vecino más cercano al objetivo
                    next_tile = min(neighbors, key=lambda n: self._manhattan_distance(n, goal))
                    path.append(next_tile)
                    current = next_tile
            else:
                # Movimiento aleatorio
                neighbors = self._get_valid_neighbors(current)
                if neighbors:
                    next_tile = random.choice(neighbors)
                    path.append(next_tile)
                    current = next_tile
        
        return path
    
    def _bfs_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Breadth-First Search: Encuentra un camino (no necesariamente el más corto).
        Bueno para dificultad media.
        """
        if start == goal:
            return []
        
        queue = deque([(start, [start])])
        visited: Set[Tuple[int, int]] = {start}
        
        while queue:
            current, path = queue.popleft()
            
            if current == goal:
                return path[1:]  # Excluir posición inicial
            
            for neighbor in self._get_valid_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []  # No se encontró camino
    
    def _dijkstra_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Algoritmo de Dijkstra: Encuentra el camino más corto considerando costos.
        Perfecto para dificultad difícil.
        """
        if start == goal:
            return []
        
        # Priority queue: (costo, nodo, camino)
        heap = [(0, start, [start])]
        visited: Dict[Tuple[int, int], float] = {start: 0}
        
        iterations = 0
        while heap and iterations < 1000:  # Límite de seguridad
            iterations += 1
            cost, current, path = heapq.heappop(heap)
            
            if current == goal:
                return path[1:]  # Excluir posición inicial
            
            # Explorar vecinos
            neighbors = self._get_valid_neighbors(current)
            
            for neighbor in neighbors:
                # Calcular costo del movimiento
                move_cost = self._get_tile_cost(neighbor)
                new_cost = cost + move_cost
                
                # Si encontramos un camino mejor o no hemos visitado este nodo
                if neighbor not in visited or new_cost < visited[neighbor]:
                    visited[neighbor] = new_cost
                    heapq.heappush(heap, (new_cost, neighbor, path + [neighbor]))
        
        # FALLBACK: Si no encontramos camino, crear un path parcial hacia el objetivo
        if visited:
            # Encontrar el nodo visitado más cercano al objetivo
            closest = min(visited.keys(), key=lambda n: self._manhattan_distance(n, goal))
            # Reconstruir path hasta el nodo más cercano usando BFS simple
            return self._build_partial_path(start, closest)
        
        return []  # No se encontró camino
    
    def _build_partial_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Construye un path parcial usando movimiento greedy hacia el objetivo"""
        path = []
        current = start
        max_steps = 20
        
        for _ in range(max_steps):
            if current == goal:
                break
            
            neighbors = self._get_valid_neighbors(current)
            if not neighbors:
                break
            
            # Elegir vecino más cercano al objetivo
            next_tile = min(neighbors, key=lambda n: self._manhattan_distance(n, goal))
            path.append(next_tile)
            current = next_tile
        
        return path
    
    def _get_tile_cost(self, tile: Tuple[int, int]) -> float:
        """Calcula el costo de moverse a un tile (para Dijkstra)"""
        if not self.map_logic:
            return 1.0
        
        tile_info = self.map_logic.get_tile_info(tile[0], tile[1])
        if not tile_info:
            return 1.0
        
        # Usar surface_weight si está disponible
        if hasattr(tile_info, 'surface_weight') and tile_info.surface_weight:
            return tile_info.surface_weight
        
        return 1.0
    
    def _get_valid_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Obtiene vecinos válidos (no bloqueados) de una posición"""
        x, y = pos
        neighbors = [
            (x, y - 1),  # Arriba
            (x, y + 1),  # Abajo
            (x - 1, y),  # Izquierda
            (x + 1, y),  # Derecha
        ]
        
        if not self.map_logic:
            return neighbors
        
        return [n for n in neighbors if not self.map_logic.is_blocked(n[0], n[1])]
    
    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calcula distancia de Manhattan entre dos posiciones"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _follow_path(self, clima_factor: float = 1.0):
        """Sigue el camino planificado moviendo al bot"""
        if not self.current_path:
            return
        
        # Verificar si el bot puede moverse
        if not self.stats.puede_moverse():
            # El bot está exhausto, no puede moverse
            return
        
        # Obtener siguiente tile en el camino
        next_tile = self.current_path[0]
        current_tile = self._get_tile_pos()
        
        # Si ya llegamos al siguiente tile, quitarlo del path
        if current_tile == next_tile:
            self.current_path.pop(0)
            if not self.current_path:
                self._on_goal_reached()
            return
        
        # Verificar si el siguiente tile está bloqueado
        if self.map_logic and self.map_logic.is_blocked(next_tile[0], next_tile[1]):
            # El tile está bloqueado, replanificar
            if self.current_goal:
                self._plan_path_to(self.current_goal)
            else:
                self.current_path = []
            return
        
        # Calcular dirección
        dx = next_tile[0] - current_tile[0]
        dy = next_tile[1] - current_tile[1]
        
        # Determinar dirección de movimiento
        if dy < 0:
            direccion = "up"
        elif dy > 0:
            direccion = "down"
        elif dx < 0:
            direccion = "izq"
        elif dx > 0:
            direccion = "der"
        else:
            return
        
        # Obtener información del tile para surface_weight
        tile_info = None
        if self.map_logic:
            tile_info = self.map_logic.get_tile_info(next_tile[0], next_tile[1])
        
        # Calcular peso del inventario
        peso_inventario = 0.0
        if self.inventario:
            pedidos_en_inventario = self.inventario.get_orders()
            peso_inventario = sum(pedido.weight for pedido in pedidos_en_inventario)
        
        # Mover el bot usando el método heredado
        self.mover(
            direccion=direccion,
            peso_total=peso_inventario,
            clima="clear",  # TODO: Obtener clima real
            clima_factor=clima_factor,
            tile_info=tile_info
        )
    
    def _get_tile_pos(self) -> Tuple[int, int]:
        """Obtiene la posición actual en tiles"""
        tile_x = int(self.x // self.tile_width)
        tile_y = int(self.y // self.tile_height)
        return (tile_x, tile_y)
    
    def _on_goal_reached(self):
        """Callback cuando el bot llega a su objetivo"""
        if self.current_task == "pickup":
            # Aquí se debería recoger el paquete
            # Esto se manejará desde el main loop
            pass
        elif self.current_task == "deliver":
            # Aquí se debería entregar el paquete
            # Esto se manejará desde el main loop
            pass
        
        # Limpiar estado
        self.current_goal = None
        self.current_task = None
    
    def _make_random_decision(self):
        """Genera un movimiento completamente aleatorio"""
        current_pos = self._get_tile_pos()
        neighbors = self._get_valid_neighbors(current_pos)
        
        if neighbors:
            self.current_path = [random.choice(neighbors)]
    
    def get_current_target(self) -> Optional[Tuple[int, int]]:
        """Retorna el objetivo actual del bot (útil para debugging)"""
        return self.current_goal
    
    def get_current_task(self) -> Optional[str]:
        """Retorna la tarea actual del bot"""
        return self.current_task
    
    def reset_path(self):
        """Limpia el camino actual (útil cuando hay cambios en el entorno)"""
        self.current_path = []
        self.current_goal = None
