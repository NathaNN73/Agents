"""
Sistema de Pathfinding usando A* para navegación dinámica de vehículos
Modificado para navegación realista solo por pistas/pasillos
"""

import math
import heapq
from typing import List, Tuple, Optional, Set
from config import *

class Node:
    """Nodo para el algoritmo A*"""
    def __init__(self, x: int, y: int, g: float = 0, h: float = 0, parent: Optional['Node'] = None):
        self.x = x
        self.y = y
        self.g = g  # Costo desde el inicio
        self.h = h  # Heurística al objetivo
        self.f = g + h  # Costo total
        self.parent = parent
    
    def __lt__(self, other):
        return self.f < other.f
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))

class PathfindingGrid:
    """Grid para pathfinding con obstáculos dinámicos y restricción a pistas"""
    
    def __init__(self, width: int, height: int, cell_size: int = 10, lane_network=None):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid_width = width // cell_size
        self.grid_height = height // cell_size
        self.lane_network = lane_network
        
        # Grid de obstáculos (True = bloqueado)
        self.obstacles = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Marcar áreas fuera de pistas como obstáculos
        if self.lane_network:
            self._mark_non_lane_areas()
    
    def _mark_non_lane_areas(self):
        """Marca todas las áreas que NO son pistas como obstáculos"""
        # Primero marcar todo como obstáculo
        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                self.obstacles[gy][gx] = True
        
        # Luego desmarcar las áreas que SÍ son pistas
        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                wx, wy = self.grid_to_world(gx, gy)
                if self.lane_network.is_on_lane(wx, wy, tolerance=0):
                    self.obstacles[gy][gx] = False
    
    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Convierte coordenadas del mundo a coordenadas de grid"""
        grid_x = int(x / self.cell_size)
        grid_y = int(y / self.cell_size)
        grid_x = max(0, min(self.grid_width - 1, grid_x))
        grid_y = max(0, min(self.grid_height - 1, grid_y))
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """Convierte coordenadas de grid a coordenadas del mundo"""
        x = (grid_x + 0.5) * self.cell_size
        y = (grid_y + 0.5) * self.cell_size
        return x, y
    
    def is_valid(self, grid_x: int, grid_y: int) -> bool:
        """Verifica si una celda es válida y no está bloqueada"""
        if grid_x < 0 or grid_x >= self.grid_width:
            return False
        if grid_y < 0 or grid_y >= self.grid_height:
            return False
        return not self.obstacles[grid_y][grid_x]
    
    def clear_dynamic_obstacles(self):
        """Limpia solo los obstáculos dinámicos (vehículos), mantiene las restricciones de pistas"""
        if self.lane_network:
            self._mark_non_lane_areas()
        else:
            self.obstacles = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
    
    def add_obstacle(self, x: float, y: float, radius: float = 15):
        """Agrega un obstáculo circular en el grid"""
        grid_x, grid_y = self.world_to_grid(x, y)
        grid_radius = int(radius / self.cell_size) + 1
        
        for dy in range(-grid_radius, grid_radius + 1):
            for dx in range(-grid_radius, grid_radius + 1):
                nx, ny = grid_x + dx, grid_y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    # Verificar si está dentro del radio
                    wx, wy = self.grid_to_world(nx, ny)
                    dist = math.sqrt((wx - x)**2 + (wy - y)**2)
                    if dist <= radius:
                        self.obstacles[ny][nx] = True
    
    def add_rect_obstacle(self, x: float, y: float, width: float, height: float):
        """Agrega un obstáculo rectangular"""
        left = x - width / 2
        right = x + width / 2
        top = y - height / 2
        bottom = y + height / 2
        
        grid_left, grid_top = self.world_to_grid(left, top)
        grid_right, grid_bottom = self.world_to_grid(right, bottom)
        
        for gy in range(grid_top, grid_bottom + 1):
            for gx in range(grid_left, grid_right + 1):
                if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
                    self.obstacles[gy][gx] = True

class AStarPathfinder:
    """Pathfinder usando algoritmo A*"""
    
    def __init__(self, grid: PathfindingGrid):
        self.grid = grid
    
    def heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Heurística: Distancia de Manhattan"""
        return abs(x1 - x2) + abs(y1 - y2)
    
    def get_neighbors(self, node: Node) -> List[Node]:
        """Obtiene vecinos válidos de un nodo (8 direcciones)"""
        neighbors = []
        
        # 8 direcciones: arriba, abajo, izq, der, y diagonales
        directions = [
            (0, -1), (0, 1), (-1, 0), (1, 0),  # Cardinal
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal
        ]
        
        for dx, dy in directions:
            nx, ny = node.x + dx, node.y + dy
            
            if self.grid.is_valid(nx, ny):
                # Costo: 1.0 para movimientos cardinales, 1.414 para diagonales
                cost = 1.414 if dx != 0 and dy != 0 else 1.0
                neighbors.append(Node(nx, ny))
        
        return neighbors
    
    def find_path(self, start_x: float, start_y: float, 
                  goal_x: float, goal_y: float) -> Optional[List[Tuple[float, float]]]:
        """
        Encuentra un camino desde start hasta goal usando A*
        Retorna lista de waypoints en coordenadas del mundo, o None si no hay camino
        """
        # Convertir a coordenadas de grid
        start_gx, start_gy = self.grid.world_to_grid(start_x, start_y)
        goal_gx, goal_gy = self.grid.world_to_grid(goal_x, goal_y)
        
        # Verificar que inicio y fin sean válidos
        if not self.grid.is_valid(start_gx, start_gy):
            # Buscar celda válida cercana al inicio
            start_gx, start_gy = self._find_nearest_valid(start_gx, start_gy)
            if start_gx is None:
                return None
        
        if not self.grid.is_valid(goal_gx, goal_gy):
            # Buscar celda válida cercana al objetivo
            goal_gx, goal_gy = self._find_nearest_valid(goal_gx, goal_gy)
            if goal_gx is None:
                return None
        
        # Inicializar A*
        start_node = Node(start_gx, start_gy, 0, self.heuristic(start_gx, start_gy, goal_gx, goal_gy))
        goal_node = Node(goal_gx, goal_gy)
        
        open_set = []
        heapq.heappush(open_set, start_node)
        closed_set: Set[Tuple[int, int]] = set()
        node_map = {(start_gx, start_gy): start_node}
        
        while open_set:
            current = heapq.heappop(open_set)
            
            # Llegamos al objetivo
            if current == goal_node:
                return self._reconstruct_path(current)
            
            closed_set.add((current.x, current.y))
            
            # Explorar vecinos
            for neighbor in self.get_neighbors(current):
                if (neighbor.x, neighbor.y) in closed_set:
                    continue
                
                # Calcular costo
                dx = abs(neighbor.x - current.x)
                dy = abs(neighbor.y - current.y)
                move_cost = 1.414 if (dx + dy) == 2 else 1.0
                tentative_g = current.g + move_cost
                
                neighbor_key = (neighbor.x, neighbor.y)
                
                if neighbor_key not in node_map or tentative_g < node_map[neighbor_key].g:
                    neighbor.g = tentative_g
                    neighbor.h = self.heuristic(neighbor.x, neighbor.y, goal_gx, goal_gy)
                    neighbor.f = neighbor.g + neighbor.h
                    neighbor.parent = current
                    
                    node_map[neighbor_key] = neighbor
                    heapq.heappush(open_set, neighbor)
        
        # No se encontró camino
        return None
    
    def _find_nearest_valid(self, gx: int, gy: int, max_radius: int = 10) -> Tuple[Optional[int], Optional[int]]:
        """Encuentra la celda válida más cercana"""
        for radius in range(1, max_radius + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    nx, ny = gx + dx, gy + dy
                    if self.grid.is_valid(nx, ny):
                        return nx, ny
        return None, None
    
    def _reconstruct_path(self, node: Node) -> List[Tuple[float, float]]:
        """Reconstruye el camino desde el nodo final"""
        path = []
        current = node
        
        while current is not None:
            wx, wy = self.grid.grid_to_world(current.x, current.y)
            path.append((wx, wy))
            current = current.parent
        
        path.reverse()
        
        # Simplificar el camino (eliminar waypoints innecesarios)
        return self._simplify_path(path)
    
    def _simplify_path(self, path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Simplifica el camino eliminando waypoints innecesarios"""
        if len(path) <= 2:
            return path
        
        simplified = [path[0]]
        
        for i in range(1, len(path) - 1):
            prev = path[i - 1]
            current = path[i]
            next_point = path[i + 1]
            
            # Calcular si hay cambio de dirección significativo
            dx1 = current[0] - prev[0]
            dy1 = current[1] - prev[1]
            dx2 = next_point[0] - current[0]
            dy2 = next_point[1] - current[1]
            
            # Normalizar
            len1 = math.sqrt(dx1**2 + dy1**2)
            len2 = math.sqrt(dx2**2 + dy2**2)
            
            if len1 > 0 and len2 > 0:
                dx1 /= len1
                dy1 /= len1
                dx2 /= len2
                dy2 /= len2
                
                # Si la dirección cambia significativamente, mantener el waypoint
                dot_product = dx1 * dx2 + dy1 * dy2
                if dot_product < 0.9:  # Ángulo > ~25 grados
                    simplified.append(current)
        
        simplified.append(path[-1])
        return simplified
