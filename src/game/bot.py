import pygame
import heapq
import random
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from src.game.player import Player
from src.game.stats_module import Stats
from src.game.reputation import Reputation
from src.game.save import Save
from pathlib import Path as _Path


class Bot(Player):
    """
    hereda de Player.
    
    Niveles de dificultad:
    - EASY: Movimiento random
    - MEDIUM: Expectimax - Evalúa movimientos futuros
    - HARD: Dijkstra + TSP - Optimiza rutas y secuencia de entregas con clima
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
        # --- Intent: usar sprites específicos del bot si existen en la carpeta ---
        
        # Reemplazar directamente los sprites del bot (se asume que existen)
        sprites_dir = _Path(sprites_dir)
        self.sprites.update({
            "up": pygame.transform.scale(pygame.image.load(sprites_dir / "Spr_delivery_bot_up.png").convert_alpha(), (self.tile_width, self.tile_height)),
            "down": pygame.transform.scale(pygame.image.load(sprites_dir / "Spr_delivery_bot_down.png").convert_alpha(), (self.tile_width, self.tile_height)),
            "izq": pygame.transform.scale(pygame.image.load(sprites_dir / "Spr_delivery_bot_izq.png").convert_alpha(), (self.tile_width, self.tile_height)),
            "der": pygame.transform.scale(pygame.image.load(sprites_dir / "Spr_delivery_bot_der.png").convert_alpha(), (self.tile_width, self.tile_height)),
        })

        # Actualizar imagen actual manteniendo el centro si existe
        current_center = getattr(self.rect, 'center', None)
        self.image = self.sprites.get(self.direccion, next(iter(self.sprites.values())))
        if current_center:
            self.rect = self.image.get_rect(center=current_center)

        
        self.difficulty = difficulty
        self.map_logic = map_logic
        self.inventario = inventario
        
        # Estado interno del bot
        self.current_path: List[Tuple[int, int]] = []
        self.current_goal: Optional[Tuple[int, int]] = None
        self.current_task: Optional[str] = None
        self.target_package = None
        
        # Para nivel HARD: secuencia de entregas optimizada
        self.delivery_sequence: List = []
        
        # Para replanificación dinámica (HARD)
        self.last_clima_factor: float = 1.0
        self.replan_threshold: float = 0.3
        
        # Configuración por dificultad
        self.config = self._get_difficulty_config()
        
        # Contador para decisiones periódicas
        self.decision_counter = 0
        self.decision_interval = self.config['decision_interval']
        
    def _get_difficulty_config(self) -> Dict:
        """Retorna configuración específica por dificultad"""
        configs = {
            self.EASY: {
                'decision_interval': 60,
                'random_chance': 0.3,
                'mistake_chance': 0.2,
                'expectimax_depth': 0,
            },
            self.MEDIUM: {
                'decision_interval': 30,
                'random_chance': 0.1,
                'mistake_chance': 0.05,
                'expectimax_depth': 2,
            },
            self.HARD: {
                'decision_interval': 20,
                'random_chance': 0.0,
                'mistake_chance': 0.0,
                'expectimax_depth': 3,
            }
        }
        return configs.get(self.difficulty, configs[self.MEDIUM])
    
    def update(self, dt: float, pedidos: List, clima_factor: float = 1.0):
        """
        Actualización del bot cada tile.

        """
        # Guardar posición anterior para comparar
        old_pos = self._get_tile_pos()
        
        # Detectar cambio significativo en clima para replanificar (HARD)
        if self.difficulty == self.HARD:
            if abs(clima_factor - self.last_clima_factor) > self.replan_threshold:
                if self.current_goal:
                    self._plan_path_to(self.current_goal, clima_factor)
                self.last_clima_factor = clima_factor
        
        self.decision_counter += 1
        
        # Tomar decisiones periódicamente
        if self.decision_counter >= self.decision_interval:
            self.decision_counter = 0
            self._make_decision(pedidos, clima_factor)
        
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
    
    def _make_decision(self, pedidos: List, clima_factor: float = 1.0):
        """Decide qué hacer basándose en el estado actual y pedidos disponibles"""
        
        # Verificar si cometemos un error (solo en dificultades bajas)
        if random.random() < self.config['mistake_chance']:
            self._make_random_decision()
            return
        
        # Para HARD
        if self.difficulty == self.HARD and self.inventario and len(self.inventario.get_orders()) > 1:
            self._optimize_delivery_sequence(clima_factor)
        
        # Si hay paquetes, entregarlos
        if self.inventario and len(self.inventario.get_orders()) > 0:
            packages = self.inventario.get_orders()
            
            # usar la secuencia optimizada
            if self.difficulty == self.HARD and self.delivery_sequence:
                target = self.delivery_sequence[0]
            else:
                packages = sorted(packages, key=lambda p: p.priority, reverse=True)
                target = packages[0]
            
            self.current_task = "deliver"
            self.target_package = target
            self.current_goal = tuple(target.dropoff)
            self._plan_path_to(self.current_goal, clima_factor)
            return

        # Recoger paquetes
        if pedidos:
            # Filtrar no recogidos
            available = [p for p in pedidos if not self._is_package_picked(p)]
            if available:
                target = self._choose_best_package(available, clima_factor)
                self.current_task = "pickup"
                self.target_package = target
                self.current_goal = tuple(target.pickup)
                self._plan_path_to(self.current_goal, clima_factor)
                return
        
        # movimiento aleatorio
        self.current_task = "explore"
        self._make_random_decision()
    
    def _is_package_picked(self, package) -> bool:
        if not self.inventario:
            return False
        return package in self.inventario.get_orders()
    
    def _choose_best_package(self, packages: List, clima_factor: float = 1.0):
        current_pos = self._get_tile_pos()
        
        if self.difficulty == self.EASY:
            # Easy: Aleatorio de los 3 más cercanos
            packages = sorted(packages, key=lambda p: self._manhattan_distance(current_pos, tuple(p.pickup)))
            candidates = packages[:min(3, len(packages))]
            return random.choice(candidates)
        
        elif self.difficulty == self.MEDIUM:
            # Medium: Usar Expectimax para evaluar mejor opción
            return self._expectimax_choose_package(packages, clima_factor)
        
        else: 
            # Hard: Mejor combinación de distancia, prioridad y clima
            def score(p):
                dist = self._manhattan_distance(current_pos, tuple(p.pickup))
                priority = p.priority
                time_left = p.duration
                # Ajustar score por clima
                clima_penalty = (1.0 - clima_factor) * dist * 0.5
                return (priority * 10) - (dist * 0.5) + (time_left * 0.1) - clima_penalty
            
            return max(packages, key=score)
    
    def _plan_path_to(self, goal: Tuple[int, int], clima_factor: float = 1.0):
        if not self.map_logic:
            return
        
        start = self._get_tile_pos()
        
        if self.map_logic.is_blocked(goal[0], goal[1]):
            neighbors = [
                (goal[0], goal[1] - 1),
                (goal[0], goal[1] + 1),
                (goal[0] - 1, goal[1]),
                (goal[0] + 1, goal[1]),
            ]
            valid_neighbors = [n for n in neighbors if not self.map_logic.is_blocked(n[0], n[1])]
            if valid_neighbors:
                goal = min(valid_neighbors, key=lambda n: self._manhattan_distance(start, n))
            else:
                self.current_path = []
                return
        
        if self.difficulty == self.EASY:
            self.current_path = self._random_walk_path(start, goal)
        elif self.difficulty == self.MEDIUM:
            self.current_path = self._expectimax_path(start, goal, clima_factor)
        else:
            self.current_path = self._dijkstra_path(start, goal, clima_factor)
    
    def _random_walk_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Movimiento aleatorio per va hacia el objetivo (EASY).
        """
        path = []
        current = start
        max_steps = 20
        
        for _ in range(max_steps):
            if current == goal:
                break
            
            if random.random() > self.config['random_chance']:
                neighbors = self._get_valid_neighbors(current)
                if neighbors:
                    next_tile = min(neighbors, key=lambda n: self._manhattan_distance(n, goal))
                    path.append(next_tile)
                    current = next_tile
            else:
                neighbors = self._get_valid_neighbors(current)
                if neighbors:
                    next_tile = random.choice(neighbors)
                    path.append(next_tile)
                    current = next_tile
        
        return path
    
    def _expectimax_path(self, start: Tuple[int, int], goal: Tuple[int, int], clima_factor: float = 1.0) -> List[Tuple[int, int]]:
        """
        Función heurística: score = α*(payout) – β*(distance) – γ*(weather_penalty)
        """
        if start == goal:
            return []
        
        depth = self.config['expectimax_depth']
        
        def expectimax_value(pos: Tuple[int, int], current_depth: int, is_max: bool) -> float:
            """Calcular valor expectimax de una posición"""
            if current_depth == 0 or pos == goal:
                return self._evaluate_position(pos, goal, clima_factor)
            
            neighbors = self._get_valid_neighbors(pos)
            if not neighbors:
                return self._evaluate_position(pos, goal, clima_factor)
            
            if is_max:
                return max(expectimax_value(n, current_depth - 1, False) for n in neighbors)
            else:
                values = [expectimax_value(n, current_depth - 1, True) for n in neighbors]
                weights = []
                for n in neighbors:
                    dist_to_goal = self._manhattan_distance(n, goal)
                    weight = 1.0 / (1.0 + dist_to_goal * 0.1)
                    weights.append(weight)
                
                total_weight = sum(weights)
                if total_weight == 0:
                    return sum(values) / len(values)
                
                return sum(v * w / total_weight for v, w in zip(values, weights))
        
        path = []
        current = start
        visited = {start}
        max_steps = 50
        
        for _ in range(max_steps):
            if current == goal:
                break
            
            neighbors = self._get_valid_neighbors(current)
            unvisited_neighbors = [n for n in neighbors if n not in visited]
            
            if not unvisited_neighbors:
                unvisited_neighbors = neighbors
            
            if not unvisited_neighbors:
                break
            
            best_neighbor = max(
                unvisited_neighbors,
                key=lambda n: expectimax_value(n, depth - 1, False)
            )
            
            path.append(best_neighbor)
            visited.add(best_neighbor)
            current = best_neighbor
        
        return path
    
    def _evaluate_position(self, pos: Tuple[int, int], goal: Tuple[int, int], clima_factor: float) -> float:
        """
        Función heurística para Expectimax.
        """
        α, β, γ = 1.0, 0.5, 0.3
        
        dist_to_goal = self._manhattan_distance(pos, goal)
        expected_payout = 100.0 / (1.0 + dist_to_goal)
        distance_cost = dist_to_goal
        weather_penalty = (1.0 - clima_factor) * 10.0
        tile_cost = self._get_tile_cost(pos)
        terrain_bonus = (2.0 - tile_cost) * 5.0
        
        return α * expected_payout - β * distance_cost - γ * weather_penalty + terrain_bonus
    
    def _expectimax_choose_package(self, packages: List, clima_factor: float) -> any:
        current_pos = self._get_tile_pos()
        
        def evaluate_package(package) -> float:
            α, β, γ = 1.0, 0.4, 0.3
            
            payout = package.payout
            dist_to_pickup = self._manhattan_distance(current_pos, tuple(package.pickup))
            weather_penalty = (1.0 - clima_factor) * dist_to_pickup * 0.5
            priority_bonus = package.priority * 5.0
            time_left = package.duration
            time_penalty = 0 if time_left > 60 else (60 - time_left) * 0.5
            
            return α * payout - β * dist_to_pickup - γ * weather_penalty + priority_bonus - time_penalty
        
        return max(packages, key=evaluate_package)
    
    def _dijkstra_path(self, start: Tuple[int, int], goal: Tuple[int, int], clima_factor: float = 1.0) -> List[Tuple[int, int]]:
        """
        Algoritmo de Dijkstra para nivel HARD.
        """
        if start == goal:
            return []
        
        heap = [(0, start, [start])]
        visited: Dict[Tuple[int, int], float] = {start: 0}
        
        iterations = 0
        while heap and iterations < 1000:
            iterations += 1
            cost, current, path = heapq.heappop(heap)
            
            if current == goal:
                return path[1:]
            
            neighbors = self._get_valid_neighbors(current)
            
            for neighbor in neighbors:
                base_cost = self._get_tile_cost(neighbor)
                clima_multiplier = 1.0 + (1.0 - clima_factor) * 0.5
                move_cost = base_cost * clima_multiplier
                new_cost = cost + move_cost
                
                if neighbor not in visited or new_cost < visited[neighbor]:
                    visited[neighbor] = new_cost
                    heapq.heappush(heap, (new_cost, neighbor, path + [neighbor]))
        
        if visited:
            closest = min(visited.keys(), key=lambda n: self._manhattan_distance(n, goal))
            return self._build_partial_path(start, closest)
        
        return []
    
    def _build_partial_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        path = []
        current = start
        max_steps = 20
        
        for _ in range(max_steps):
            if current == goal:
                break
            
            neighbors = self._get_valid_neighbors(current)
            if not neighbors:
                break
            
            next_tile = min(neighbors, key=lambda n: self._manhattan_distance(n, goal))
            path.append(next_tile)
            current = next_tile
        
        return path
    
    def _optimize_delivery_sequence(self, clima_factor: float = 1.0):
        if not self.inventario:
            return
        
        packages = self.inventario.get_orders()
        if len(packages) <= 1:
            self.delivery_sequence = packages.copy()
            return
        
        current_pos = self._get_tile_pos()
        unvisited = packages.copy()
        sequence = []
        
        while unvisited:
            best_package = None
            best_score = float('-inf')
            
            for package in unvisited:
                dropoff_pos = tuple(package.dropoff)
                path_cost = self._estimate_path_cost(current_pos, dropoff_pos, clima_factor)
                
                priority_weight = 10.0
                cost_weight = 0.5
                time_left = package.duration
                urgency = 100.0 / (1.0 + time_left) if time_left > 0 else 100.0
                
                score = (package.priority * priority_weight) - (path_cost * cost_weight) + urgency
                
                if score > best_score:
                    best_score = score
                    best_package = package
            
            if best_package:
                sequence.append(best_package)
                unvisited.remove(best_package)
                current_pos = tuple(best_package.dropoff)
        
        self.delivery_sequence = sequence
    
    def _estimate_path_cost(self, start: Tuple[int, int], goal: Tuple[int, int], clima_factor: float) -> float:
        """costo estimado de un camino usando distancia Manhattan ajustada por clima"""
        base_distance = self._manhattan_distance(start, goal)
        clima_multiplier = 1.0 + (1.0 - clima_factor) * 0.5
        return base_distance * clima_multiplier
    
    def _get_tile_cost(self, tile: Tuple[int, int]) -> float:
        """Calcula el costo de moverse a un tile usando surface_weight"""
        if not self.map_logic:
            return 1.0
        
        tile_info = self.map_logic.get_tile_info(tile[0], tile[1])
        if not tile_info:
            return 1.0
        
        if hasattr(tile_info, 'surface_weight') and tile_info.surface_weight:
            return tile_info.surface_weight
        
        return 1.0
    
    def _get_valid_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Obtiene vecinos válidos (no bloqueados) de una posición"""
        x, y = pos
        neighbors = [
            (x, y - 1),
            (x, y + 1),
            (x - 1, y),
            (x + 1, y),
        ]
        
        if not self.map_logic:
            return neighbors
        
        return [n for n in neighbors if not self.map_logic.is_blocked(n[0], n[1])]
    
    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calcula distancia de Manhattan entre dos posiciones"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _follow_path(self, clima_factor: float = 1.0):
        """Sigue el camino planificado moviendo al bot"""
        if not self.current_path or not self.stats.puede_moverse():
            return
        
        next_tile = self.current_path[0]
        current_tile = self._get_tile_pos()
        
        if current_tile == next_tile:
            self.current_path.pop(0)
            if not self.current_path:
                self._on_goal_reached()
            return
        
        if self.map_logic and self.map_logic.is_blocked(next_tile[0], next_tile[1]):
            if self.current_goal:
                self._plan_path_to(self.current_goal, clima_factor)
            else:
                self.current_path = []
            return
        
        dx = next_tile[0] - current_tile[0]
        dy = next_tile[1] - current_tile[1]
        
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
        
        tile_info = None
        if self.map_logic:
            tile_info = self.map_logic.get_tile_info(next_tile[0], next_tile[1])
        
        peso_inventario = 0.0
        if self.inventario:
            pedidos_en_inventario = self.inventario.get_orders()
            peso_inventario = sum(pedido.weight for pedido in pedidos_en_inventario)
        
        self.mover(
            direccion=direccion,
            peso_total=peso_inventario,
            clima="clear",
            clima_factor=clima_factor,
            tile_info=tile_info
        )
    
    def _get_tile_pos(self) -> Tuple[int, int]:
        """Obtiene la posición actual"""
        tile_x = int(self.x // self.tile_width)
        tile_y = int(self.y // self.tile_height)
        return (tile_x, tile_y)
    
    def _on_goal_reached(self):
        """Callback cuando el bot llega a su objetivo"""
        if self.current_task == "deliver":
            if self.delivery_sequence and self.target_package in self.delivery_sequence:
                self.delivery_sequence.remove(self.target_package)
        
        self.current_goal = None
        self.current_task = None
    
    def _make_random_decision(self):
        """Genera un movimiento random"""
        current_pos = self._get_tile_pos()
        neighbors = self._get_valid_neighbors(current_pos)
        
        if neighbors:
            self.current_path = [random.choice(neighbors)]

