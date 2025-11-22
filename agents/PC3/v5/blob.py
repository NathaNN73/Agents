"""
Clase Blob - Representa una criatura en la simulación
"""
import random
import math
from typing import Tuple, Optional
from config import *


class Blob:
    _id_counter = 0
    
    def __init__(self, x: float, y: float, speed: float = None, 
                 size: float = None, sense: float = None, generation: int = 0):

        Blob._id_counter += 1
        self.id = Blob._id_counter
        
        # Posición
        self.x = x
        self.y = y
        self.home_x = x
        self.home_y = y
        
        # Rasgos
        self.speed = speed if speed is not None else random.uniform(*SPEED_RANGE)
        self.size = size if size is not None else random.uniform(*SIZE_RANGE)
        self.sense = sense if sense is not None else random.uniform(*SENSE_RANGE)
        
        # Estado
        self.energy = BASE_ENERGY
        self.food_collected = 0
        self.alive = True
        self.at_home = False
        self.generation = generation
        
        # Objetivo actual
        self.target_x = None
        self.target_y = None
        self.fleeing = False
        
    def get_energy_cost_per_step(self) -> float:
        """Calcula el costo de energía por paso de tiempo"""
        movement_cost = (self.size ** 3) * (self.speed ** 2)
        sense_cost = self.sense
        return movement_cost + sense_cost
    
    def can_reach_distance(self) -> float:
        """Calcula la distancia máxima que puede recorrer con su energía actual"""
        cost_per_step = self.get_energy_cost_per_step()
        if cost_per_step == 0:
            return float('inf')
        return self.energy / cost_per_step
    
    def move_towards(self, target_x: float, target_y: float, dt: float = 1.0):
        """
        Mueve el blob hacia un objetivo
        """
        if not self.alive:
            return
            
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 0.1:
            self.x = target_x
            self.y = target_y
            return
        
        # Normalizar dirección
        dx /= distance
        dy /= distance
        
        # Mover según velocidad
        move_distance = self.speed  # Movimiento directo basado en velocidad
        actual_distance = min(move_distance, distance)
        
        self.x += dx * actual_distance
        self.y += dy * actual_distance
        
        # Consumir energía (costo reducido)
        energy_cost = self.get_energy_cost_per_step() * 0.05  # ¡5% del costo original!
        self.energy -= energy_cost
        
        if self.energy <= 0:
            self.alive = False
    
    def detect_nearest(self, entities: list, entity_type: str = 'food') -> Optional[Tuple[float, float, object]]:
        """
        Detecta la entidad más cercana dentro del rango de sentido
        """
        nearest = None
        nearest_dist = self.sense
        
        for entity in entities:
            if entity_type == 'blob' and entity.id == self.id:
                continue
            if entity_type == 'blob' and not entity.alive:
                continue
                
            if entity_type == 'food':
                ex, ey = entity['x'], entity['y']
            else:
                ex, ey = entity.x, entity.y
            
            dist = math.sqrt((ex - self.x)**2 + (ey - self.y)**2)
            
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = (ex, ey, entity)
        
        return nearest
    
    def can_eat(self, other_blob: 'Blob') -> bool:
        """Verifica si este blob puede comer a otro"""
        return self.size >= other_blob.size * SIZE_EAT_THRESHOLD
    
    def eat_food(self):
        """Consume una pieza de comida"""
        self.food_collected += 1
        self.energy += FOOD_ENERGY
    
    def eat_blob(self, other_blob: 'Blob'):
        """Consume otro blob"""
        self.food_collected += 2  # Equivalente a 2 piezas de comida
        self.energy += BLOB_ENERGY
        other_blob.alive = False
    
    def return_home(self):
        """Verifica si el blob está en casa"""
        dist_home = math.sqrt((self.x - self.home_x)**2 + (self.y - self.home_y)**2)
        return dist_home < 5.0
    
    def replicate(self) -> 'Blob':
        """
        Crea una copia del blob con posible mutación
        """
        # Aplicar mutaciones
        new_speed = self._mutate(self.speed, *SPEED_RANGE)
        new_size = self._mutate(self.size, *SIZE_RANGE)
        new_sense = self._mutate(self.sense, *SENSE_RANGE)
        
        # Crear nuevo blob en la misma posición de casa
        offspring = Blob(
            self.home_x, 
            self.home_y,
            speed=new_speed,
            size=new_size,
            sense=new_sense,
            generation=self.generation + 1
        )
        
        return offspring
    
    def _mutate(self, value: float, min_val: float, max_val: float) -> float:
        """
        Aplica mutación a un valor
        """
        if random.random() < MUTATION_RATE:
            change = value * MUTATION_STRENGTH * random.choice([-1, 1])
            new_value = value + change
            return max(min_val, min(max_val, new_value))
        return value
    
    def to_dict(self) -> dict:
        """Convierte el blob a diccionario para serialización"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'home_x': self.home_x,
            'home_y': self.home_y,
            'speed': self.speed,
            'size': self.size,
            'sense': self.sense,
            'energy': self.energy,
            'food_collected': self.food_collected,
            'alive': self.alive,
            'at_home': self.at_home,
            'generation': self.generation
        }