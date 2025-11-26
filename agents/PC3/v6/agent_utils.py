"""
Utilidades para manejo de agentes
"""
import random
import math
from typing import Tuple
from config import *


class AgentUtils:
    """Funciones de utilidad para agentes"""
    
    _blob_counter = 0
    
    @staticmethod
    def generate_blob_jid(blob_id: int) -> str:
        """Genera un JID único para un blob (blob_001@xmpp.jp, blob_002@xmpp.jp, etc.)"""
        return f"{BLOB_JID_PREFIX}{blob_id:03d}{XMPP_DOMAIN}"
    
    @staticmethod
    def get_next_blob_id() -> int:
        """Obtiene el siguiente ID de blob"""
        AgentUtils._blob_counter += 1
        return AgentUtils._blob_counter
    
    @staticmethod
    def reset_blob_counter():
        """Reinicia el contador de blobs"""
        AgentUtils._blob_counter = 0
    
    @staticmethod
    def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
        """Calcula la distancia euclidiana entre dos puntos"""
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    @staticmethod
    def mutate_value(value: float, min_val: float, max_val: float) -> float:
        """Aplica mutación a un valor"""
        if random.random() < MUTATION_RATE:
            change = value * MUTATION_STRENGTH * random.choice([-1, 1])
            new_value = value + change
            return max(min_val, min(max_val, new_value))
        return value
    
    @staticmethod
    def generate_random_position(edge: str = None) -> Tuple[float, float]:
        """Genera una posición aleatoria en el mapa"""
        if edge is None:
            edge = random.choice(['top', 'bottom', 'left', 'right'])
        
        if edge == 'top':
            return random.uniform(50, MAP_WIDTH - 50), 10
        elif edge == 'bottom':
            return random.uniform(50, MAP_WIDTH - 50), MAP_HEIGHT - 10
        elif edge == 'left':
            return 10, random.uniform(50, MAP_HEIGHT - 50)
        else:  # right
            return MAP_WIDTH - 10, random.uniform(50, MAP_HEIGHT - 50)
    
    @staticmethod
    def generate_food_position() -> Tuple[float, float]:
        """Genera una posición aleatoria para comida"""
        return (
            random.uniform(100, MAP_WIDTH - 100),
            random.uniform(100, MAP_HEIGHT - 100)
        )
    
    @staticmethod
    def normalize_direction(dx: float, dy: float) -> Tuple[float, float]:
        """Normaliza un vector de dirección"""
        distance = math.sqrt(dx**2 + dy**2)
        if distance == 0:
            return 0, 0
        return dx / distance, dy / distance
    
    @staticmethod
    def clamp_position(x: float, y: float) -> Tuple[float, float]:
        """Mantiene una posición dentro de los límites del mapa"""
        x = max(0, min(MAP_WIDTH, x))
        y = max(0, min(MAP_HEIGHT, y))
        return x, y
    
    @staticmethod
    def get_initial_traits() -> Tuple[float, float, float]:
        """Obtiene los rasgos iniciales mínimos para la primera generación"""
        return (
            SPEED_RANGE[0],  # Velocidad mínima
            SIZE_RANGE[0],   # Tamaño mínimo
            SENSE_RANGE[0]   # Sentido mínimo
        )
    
    @staticmethod
    def can_eat(size1: float, size2: float) -> bool:
        """Verifica si un blob puede comer a otro"""
        return size1 >= size2 * SIZE_EAT_THRESHOLD
