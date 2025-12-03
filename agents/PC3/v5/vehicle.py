"""
Clase Vehicle - Vehículo con navegación por pasillos y detección de colisiones
"""

import random
import math
from typing import Optional, List, Tuple
from config import *

class Vehicle:
    _id_counter = 0
    
    def __init__(self, x: float, y: float, vehicle_type: str = "normal"):
        Vehicle._id_counter += 1
        self.id = Vehicle._id_counter
        
        # Posición
        self.x = x
        self.y = y
        
        # Tipo de vehículo
        self.vehicle_type = vehicle_type
        
        # Estado
        self.state = "ARRIVING"
        self.active = True
        
        # Plaza asignada
        self.assigned_spot = None
        self.spot_x = None
        self.spot_y = None
        self.spot_row = None
        self.spot_col = None
        
        # Navegación por waypoints
        self.waypoints = []
        self.current_waypoint_index = 0
        
        # Tiempo
        self.parking_duration = random.uniform(PARKING_TIME_MIN, PARKING_TIME_MAX)
        self.parked_time = 0.0
        
        # Métricas
        self.arrival_time = 0.0
        self.assignment_time = 0.0
        self.parking_time = 0.0
        self.search_time = 0.0
    
    def set_waypoints(self, waypoints: List[Tuple[float, float]]):
        """Establece la ruta de waypoints a seguir"""
        self.waypoints = waypoints
        self.current_waypoint_index = 0
    
    def get_current_target(self) -> Optional[Tuple[float, float]]:
        """Obtiene el waypoint actual"""
        if self.current_waypoint_index < len(self.waypoints):
            return self.waypoints[self.current_waypoint_index]
        return None
    
    def move_along_path(self, obstacles: List[dict], other_vehicles: List['Vehicle']) -> bool:
        """
        Mueve el vehículo siguiendo waypoints, evitando colisiones
        Retorna True si llegó al destino final
        """
        if not self.active:
            return False
        
        target = self.get_current_target()
        if not target:
            return True  # Ya llegó al final
        
        target_x, target_y = target
        
        # Calcular dirección
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Si llegó al waypoint actual, pasar al siguiente
        if distance < 3.0:
            self.current_waypoint_index += 1
            return self.current_waypoint_index >= len(self.waypoints)
        
        # Normalizar dirección
        if distance > 0:
            dx /= distance
            dy /= distance
        
        # Calcular nueva posición
        move_distance = VEHICLE_SPEED
        new_x = self.x + dx * move_distance
        new_y = self.y + dy * move_distance
        
        # Verificar colisiones antes de mover
        if self._check_collision(new_x, new_y, obstacles, other_vehicles):
            # Si hay colisión, no mover
            return False
        
        # Mover
        self.x = new_x
        self.y = new_y
        
        return False
    
    def _check_collision(self, new_x: float, new_y: float, 
                        obstacles: List[dict], other_vehicles: List['Vehicle']) -> bool:
        """
        Verifica si la nueva posición colisiona con obstáculos o vehículos
        """
        # Colisión con plazas de estacionamiento
        for spot in obstacles:
            # Si es mi plaza asignada y estoy cerca, permitir entrada
            if spot['id'] == self.assigned_spot:
                if self.state == "MOVING_TO_SPOT":
                    # Permitir entrar a mi plaza asignada
                    continue
            
            # Verificar colisión con rectángulo de plaza
            spot_left = spot['x'] - SPOT_WIDTH / 2
            spot_right = spot['x'] + SPOT_WIDTH / 2
            spot_top = spot['y'] - SPOT_HEIGHT / 2
            spot_bottom = spot['y'] + SPOT_HEIGHT / 2
            
            # Expandir un poco para dar margen
            margin = VEHICLE_SIZE / 2
            if (new_x + margin > spot_left and new_x - margin < spot_right and
                new_y + margin > spot_top and new_y - margin < spot_bottom):
                return True
        
        # Colisión con otros vehículos
        for other in other_vehicles:
            if other.id == self.id or not other.active:
                continue
            
            # Si el otro está estacionado, no contar colisión
            if other.state == "PARKED":
                continue
            
            # IMPORTANTE: Si ambos están en ARRIVING, ignorar colisión
            # (permite que múltiples vehículos esperen en la entrada)
            if self.state == "ARRIVING" and other.state == "ARRIVING":
                continue
            
            dist = math.sqrt((other.x - new_x)**2 + (other.y - new_y)**2)
            if dist < VEHICLE_SIZE * 2:  # Reducir margen de seguridad
                return True
        
        return False

    
    def move_towards(self, target_x: float, target_y: float) -> bool:
        """Método simple para movimiento directo (usado al salir)"""
        if not self.active:
            return False
        
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 1.0:
            self.x = target_x
            self.y = target_y
            return True
        
        if distance > 0:
            dx /= distance
            dy /= distance
        
        move_distance = VEHICLE_SPEED
        actual_distance = min(move_distance, distance)
        
        self.x += dx * actual_distance
        self.y += dy * actual_distance
        
        return False
    
    def has_reached_spot(self) -> bool:
        """Verifica si llegó a la plaza asignada"""
        if self.spot_x is None or self.spot_y is None:
            return False
        
        dist = math.sqrt((self.x - self.spot_x)**2 + (self.y - self.spot_y)**2)
        return dist < 5.0
    
    def to_dict(self) -> dict:
        """Serialización"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'type': self.vehicle_type,
            'state': self.state,
            'active': self.active,
            'assigned_spot': self.assigned_spot,
            'parked_time': self.parked_time,
            'parking_duration': self.parking_duration,
            'search_time': self.search_time
        }