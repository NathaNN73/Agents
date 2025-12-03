"""
Sistema de Zonas de Control para el estacionamiento
Define zonas de entrada (validación) y salida
"""

from typing import List, Dict, Tuple
from config import *

class ControlZones:
    """Zonas de control de entrada y salida del estacionamiento"""
    
    def __init__(self):
        self.entry_zones = []
        self.exit_zones = []
        self.validation_zones = []
        self._create_zones()
    
    def _create_zones(self):
        """Crea las zonas de entrada, validación y salida"""
        
        # ZONAS DE ENTRADA (spawn points) - Extremo izquierdo de cada pista
        self.entry_zones = [
            {
                'id': 0,
                'name': 'entry_top',
                'lane': 'top',
                'x': 10,  # Extremo izquierdo
                'y': 75,  # Pasillo superior
                'width': 20,
                'height': 50
            },
            {
                'id': 1,
                'name': 'entry_middle',
                'lane': 'middle',
                'x': 10,
                'y': MAP_HEIGHT / 2,  # Pasillo central
                'width': 20,
                'height': 60
            },
            {
                'id': 2,
                'name': 'entry_bottom',
                'lane': 'bottom',
                'x': 10,
                'y': MAP_HEIGHT - 75,  # Pasillo inferior
                'width': 20,
                'height': 50
            }
        ]
        
        # ZONAS DE VALIDACIÓN (franjas verdes) - Antes de entrar al área de parking
        validation_x = 120  # Más cerca del borde para reducir área de entrada
        self.validation_zones = [
            {
                'id': 0,
                'name': 'validation_top',
                'lane': 'top',
                'x': validation_x,
                'y': 75,
                'width': 15,
                'height': 50,
                'color': '#22c55e'  # Verde
            },
            {
                'id': 1,
                'name': 'validation_middle',
                'lane': 'middle',
                'x': validation_x,
                'y': MAP_HEIGHT / 2,
                'width': 15,
                'height': 60,
                'color': '#22c55e'
            },
            {
                'id': 2,
                'name': 'validation_bottom',
                'lane': 'bottom',
                'x': validation_x,
                'y': MAP_HEIGHT - 75,
                'width': 15,
                'height': 50,
                'color': '#22c55e'
            }
        ]
        
        # ZONAS DE SALIDA (franjas rojas) - Extremo derecho de cada pista
        exit_x = MAP_WIDTH - 10
        self.exit_zones = [
            {
                'id': 0,
                'name': 'exit_top',
                'lane': 'top',
                'x': exit_x,
                'y': 75,
                'width': 15,
                'height': 50,
                'color': '#ef4444'  # Rojo
            },
            {
                'id': 1,
                'name': 'exit_middle',
                'lane': 'middle',
                'x': exit_x,
                'y': MAP_HEIGHT / 2,
                'width': 15,
                'height': 60,
                'color': '#ef4444'
            },
            {
                'id': 2,
                'name': 'exit_bottom',
                'lane': 'bottom',
                'x': exit_x,
                'y': MAP_HEIGHT - 75,
                'width': 15,
                'height': 50,
                'color': '#ef4444'
            }
        ]
    
    def is_in_validation_zone(self, x: float, y: float) -> bool:
        """Verifica si un vehículo está en una zona de validación"""
        for zone in self.validation_zones:
            if self._is_in_zone(x, y, zone):
                return True
        return False
    
    def is_in_exit_zone(self, x: float, y: float) -> bool:
        """Verifica si un vehículo está en una zona de salida"""
        for zone in self.exit_zones:
            if self._is_in_zone(x, y, zone):
                return True
        return False
    
    def _is_in_zone(self, x: float, y: float, zone: Dict) -> bool:
        """Verifica si un punto está dentro de una zona"""
        left = zone['x'] - zone['width'] / 2
        right = zone['x'] + zone['width'] / 2
        top = zone['y'] - zone['height'] / 2
        bottom = zone['y'] + zone['height'] / 2
        
        return left <= x <= right and top <= y <= bottom
    
    def get_random_entry_zone(self) -> Dict:
        """Obtiene una zona de entrada aleatoria"""
        import random
        return random.choice(self.entry_zones)
    
    def get_exit_zone_for_lane(self, lane: str) -> Dict:
        """Obtiene la zona de salida correspondiente a una pista"""
        for zone in self.exit_zones:
            if zone['lane'] == lane:
                return zone
        return self.exit_zones[1]  # Default: middle
    
    def get_all_zones(self) -> Dict:
        """Retorna todas las zonas para visualización"""
        return {
            'entry': self.entry_zones,
            'validation': self.validation_zones,
            'exit': self.exit_zones
        }

# Instancia global
control_zones = ControlZones()
