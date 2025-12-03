"""
Sistema de Red de Pistas (Pasillos) para navegación realista
Define las áreas permitidas donde los vehículos pueden moverse
"""

from typing import List, Tuple, Dict
from config import *

class LaneNetwork:
    """Red de pistas/pasillos del estacionamiento"""
    
    def __init__(self):
        self.lanes = []
        self._create_lane_network()
    
    def _create_lane_network(self):
        """Crea la red de pistas del estacionamiento"""
        self.lanes = []
        
        # 1. PASILLO HORIZONTAL SUPERIOR (nuevo)
        self.lanes.append({
            'type': 'horizontal',
            'name': 'top_aisle',
            'x1': 0,
            'x2': MAP_WIDTH,
            'y': 75,  # Altura del pasillo superior
            'width': 50
        })
        
        # 2. PASILLO HORIZONTAL PRINCIPAL (centro)
        self.lanes.append({
            'type': 'horizontal',
            'name': 'main_aisle',
            'x1': 0,
            'x2': MAP_WIDTH,
            'y': MAP_HEIGHT / 2,
            'width': 60
        })
        
        # 3. PASILLO HORIZONTAL INFERIOR (nuevo)
        self.lanes.append({
            'type': 'horizontal',
            'name': 'bottom_aisle',
            'x1': 0,
            'x2': MAP_WIDTH,
            'y': MAP_HEIGHT - 75,  # Altura del pasillo inferior
            'width': 50
        })
        
        # 4. PASILLOS VERTICALES (entre columnas de plazas)
        rows_start_x = 200
        row_spacing = (MAP_WIDTH - rows_start_x - 100) / PARKING_COLS
        
        for i in range(PARKING_COLS + 1):
            x = rows_start_x + i * row_spacing
            
            self.lanes.append({
                'type': 'vertical',
                'name': f'vertical_aisle_{i}',
                'x': x,
                'y1': 50,  # Desde arriba
                'y2': MAP_HEIGHT - 50,  # Hasta abajo
                'width': 50
            })
        
        # 5. PASILLO DE ENTRADA (desde punto de entrada hasta pasillo superior)
        self.lanes.append({
            'type': 'vertical',
            'name': 'entry_lane',
            'x': ENTRY_POINT_X,
            'y1': ENTRY_POINT_Y,
            'y2': 100,
            'width': 40
        })
        
        # 6. CONEXIÓN ENTRADA-PARKING (horizontal)
        self.lanes.append({
            'type': 'horizontal',
            'name': 'entry_connection',
            'x1': ENTRY_POINT_X,
            'x2': 200,
            'y': 75,
            'width': 40
        })
    
    def is_on_lane(self, x: float, y: float, tolerance: float = 5) -> bool:
        """Verifica si un punto está sobre una pista"""
        for lane in self.lanes:
            if lane['type'] == 'horizontal':
                # Verificar si está dentro del rango horizontal y vertical
                y_min = lane['y'] - lane['width'] / 2 - tolerance
                y_max = lane['y'] + lane['width'] / 2 + tolerance
                
                if lane['x1'] <= x <= lane['x2'] and y_min <= y <= y_max:
                    return True
            
            elif lane['type'] == 'vertical':
                # Verificar si está dentro del rango vertical y horizontal
                x_min = lane['x'] - lane['width'] / 2 - tolerance
                x_max = lane['x'] + lane['width'] / 2 + tolerance
                
                if x_min <= x <= x_max and lane['y1'] <= y <= lane['y2']:
                    return True
        
        return False
    
    def get_nearest_lane_point(self, x: float, y: float) -> Tuple[float, float]:
        """Encuentra el punto más cercano sobre una pista"""
        min_dist = float('inf')
        nearest_point = (x, y)
        
        for lane in self.lanes:
            if lane['type'] == 'horizontal':
                # Proyectar sobre el pasillo horizontal
                lane_y = lane['y']
                lane_x = max(lane['x1'], min(x, lane['x2']))
                
                dist = abs(y - lane_y) + abs(x - lane_x)
                if dist < min_dist:
                    min_dist = dist
                    nearest_point = (lane_x, lane_y)
            
            elif lane['type'] == 'vertical':
                # Proyectar sobre el pasillo vertical
                lane_x = lane['x']
                lane_y = max(lane['y1'], min(y, lane['y2']))
                
                dist = abs(x - lane_x) + abs(y - lane_y)
                if dist < min_dist:
                    min_dist = dist
                    nearest_point = (lane_x, lane_y)
        
        return nearest_point
    
    def get_lane_intersections(self) -> List[Tuple[float, float]]:
        """Obtiene todos los puntos de intersección entre pistas"""
        intersections = []
        
        # Encontrar intersecciones entre pistas horizontales y verticales
        horizontal_lanes = [l for l in self.lanes if l['type'] == 'horizontal']
        vertical_lanes = [l for l in self.lanes if l['type'] == 'vertical']
        
        for h_lane in horizontal_lanes:
            for v_lane in vertical_lanes:
                # Verificar si se intersectan
                if (h_lane['x1'] <= v_lane['x'] <= h_lane['x2'] and
                    v_lane['y1'] <= h_lane['y'] <= v_lane['y2']):
                    intersections.append((v_lane['x'], h_lane['y']))
        
        return intersections
    
    def get_lanes_data(self) -> List[Dict]:
        """Retorna información de todas las pistas para visualización"""
        return self.lanes

# Instancia global de la red de pistas
lane_network = LaneNetwork()
