from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio
import random
import math
from typing import List, Dict
from blob import Blob
from config import *


class SimulationBehaviour(CyclicBehaviour):
    """Comportamiento cíclico que actualiza la simulación"""
    
    async def run(self):
        # Esperar según la velocidad de simulación
        await asyncio.sleep(self.agent.step_delay)
        
        if self.agent.paused:
            return
        
        await self.agent.update_simulation()


class SimulationAgent(Agent):
    
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        
        # Estado de la simulación
        self.blobs: List[Blob] = []
        self.food: List[Dict] = []
        self.day = 0
        self.time_in_day = 0.0
        self.day_duration = 1000.0
        
        # Control
        self.paused = False
        self.step_delay = 0.05  # Base delay
        self.speed_multiplier = 1.0
        
        # Estadísticas
        self.stats = {
            'total_born': 0,
            'total_died': 0,
            'avg_speed': 0,
            'avg_size': 0,
            'avg_sense': 0,
            'population': 0
        }
        
    async def setup(self):
        """Inicializa el agente y la simulación"""
        print("Agente de simulación iniciado")
        
        # Crear población inicial FIJA
        self._create_initial_population()
        
        # Generar comida del primer día
        self._spawn_food()
        
        # Agregar comportamiento cíclico
        behaviour = SimulationBehaviour()
        self.add_behaviour(behaviour)
        
        print(f"Simulación inicializada con {INITIAL_POPULATION} blobs (fijo)")
    
    def _create_initial_population(self):
        self.blobs = []
        
        # Todos los blobs iniciales nacen con características mínimas iguales
        initial_speed = SPEED_RANGE[0]
        initial_size = SIZE_RANGE[0]
        initial_sense = SENSE_RANGE[0]
        
        for i in range(INITIAL_POPULATION):
            # Posición aleatoria en el borde del mapa
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            
            if edge == 'top':
                x, y = random.uniform(50, MAP_WIDTH - 50), 10
            elif edge == 'bottom':
                x, y = random.uniform(50, MAP_WIDTH - 50), MAP_HEIGHT - 10
            elif edge == 'left':
                x, y = 10, random.uniform(50, MAP_HEIGHT - 50)
            else:  # right
                x, y = MAP_WIDTH - 10, random.uniform(50, MAP_HEIGHT - 50)
            
            # Crear blobs
            blob = Blob(x, y, speed=initial_speed, size=initial_size, sense=initial_sense)
            self.blobs.append(blob)
            self.stats['total_born'] += 1
    
    def _spawn_food(self):
        """Genera comida aleatoria en el mapa"""
        self.food = []
        for _ in range(FOOD_PER_DAY):
            food = {
                'x': random.uniform(100, MAP_WIDTH - 100),
                'y': random.uniform(100, MAP_HEIGHT - 100),
                'consumed': False
            }
            self.food.append(food)
    
    async def update_simulation(self):
        """Actualiza el estado de la simulación en un paso de tiempo"""
        # Incremento basado en la velocidad del multiplicador
        self.time_in_day += 1 * self.speed_multiplier
        
        # Verificar fin del día por tiempo
        if self.time_in_day >= self.day_duration:
            await self._end_day()
            return
        
        # Actualizar cada blob
        for blob in self.blobs:
            if not blob.alive:
                continue
            
            # Fase 1: Buscar comida o cazar
            if not blob.at_home:
                await self._update_blob_behaviour(blob)
        
        # Verificar si todos los blobs están en casa o muertos (terminar día anticipadamente)
        all_done = True
        for blob in self.blobs:
            if blob.alive and not blob.at_home:
                all_done = False
                break
        
        if all_done and len(self.blobs) > 0:
            print(f"Todos los blobs han regresado a casa o muerto. Terminando día anticipadamente.")
            await self._end_day()
            return
        
        # Actualizar estadísticas
        self._update_stats()
    
    async def _update_blob_behaviour(self, blob: Blob):
        """Actualiza el comportamiento de un blob individual"""
        
        # PRIORIDAD 1: Si tiene comida o poca energía, volver a casa
        #if blob.food_collected >= 2 or blob.energy < BASE_ENERGY * 0.4:
        if blob.food_collected >= 2 or blob.energy < BASE_ENERGY * 0.4:
            blob.move_towards(blob.home_x, blob.home_y, 1.0)
            
            if blob.return_home():
                blob.at_home = True
            return
        
        # PRIORIDAD 2: Detectar amenazas (blobs más grandes)
        threat = None
        for other in self.blobs:
            if other.id == blob.id or not other.alive:
                continue
            
            dist = math.sqrt((other.x - blob.x)**2 + (other.y - blob.y)**2)
            
            if dist < blob.sense and other.can_eat(blob):
                threat = other
                break
        
        # Si hay amenaza, huir
        if threat:
            # Dirección opuesta
            dx = blob.x - threat.x
            dy = blob.y - threat.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                dx /= dist
                dy /= dist
                
                flee_x = blob.x + dx * blob.sense * FLEE_DISTANCE_MULTIPLIER
                flee_y = blob.y + dy * blob.sense * FLEE_DISTANCE_MULTIPLIER
                
                # Mantener dentro del mapa
                flee_x = max(0, min(MAP_WIDTH, flee_x))
                flee_y = max(0, min(MAP_HEIGHT, flee_y))
                
                blob.move_towards(flee_x, flee_y, 1.0)
            return
        
        # PRIORIDAD 3: Detectar presa (blobs más pequeños)
        prey_info = blob.detect_nearest(self.blobs, 'blob')
        if prey_info:
            _, _, prey = prey_info
            if blob.can_eat(prey):
                # Perseguir presa
                blob.move_towards(prey.x, prey.y, 1.0)
                
                # Verificar si alcanzó la presa
                dist = math.sqrt((prey.x - blob.x)**2 + (prey.y - blob.y)**2)
                if dist < blob.size * 5:
                    blob.eat_blob(prey)
                return
        
        # PRIORIDAD 4: Detectar comida
        available_food = [f for f in self.food if not f['consumed']]
        food_info = blob.detect_nearest(available_food, 'food')
        
        if food_info:
            fx, fy, food = food_info
            blob.move_towards(fx, fy, 1.0)
            
            # Verificar si alcanzó la comida
            dist = math.sqrt((food['x'] - blob.x)**2 + (food['y'] - blob.y)**2)
            if dist < 8:  # Radio de captura más grande
                food['consumed'] = True
                blob.eat_food()
        else:
            # PRIORIDAD 5: Movimiento aleatorio si no detecta nada
            if blob.target_x is None or \
               (abs(blob.x - blob.target_x) < 10 and abs(blob.y - blob.target_y) < 10):
                blob.target_x = random.uniform(100, MAP_WIDTH - 100)
                blob.target_y = random.uniform(100, MAP_HEIGHT - 100)
            
            blob.move_towards(blob.target_x, blob.target_y, 1.0)
    
    async def _end_day(self):
        """Finaliza el día y procesa supervivencia/replicación"""
        self.day += 1
        self.time_in_day = 0.0
        
        print(f"\n🌅 Día {self.day} completado")
        
        # Procesar cada blob
        new_blobs = []
        survived = 0
        died = 0
        replicated = 0
        
        for blob in self.blobs:
            if not blob.alive:
                died += 1
                self.stats['total_died'] += 1
                continue
            
            # Verificar si regresó a casa
            if not blob.at_home:
                blob.alive = False
                died += 1
                self.stats['total_died'] += 1
                continue
            
            # Procesar según comida recolectada
            if blob.food_collected == 0:
                blob.alive = False
                died += 1
                self.stats['total_died'] += 1
            elif blob.food_collected == 1:
                # Sobrevive
                survived += 1
                blob.energy = BASE_ENERGY
                blob.food_collected = 0
                blob.at_home = False
                new_blobs.append(blob)
            else:  # >= 2
                # Sobrevive y se replica
                survived += 1
                replicated += 1
                blob.energy = BASE_ENERGY
                blob.food_collected = 0
                blob.at_home = False
                new_blobs.append(blob)
                
                # Crear descendiente si no se excede la capacidad
                if len(new_blobs) < MAX_POPULATION:
                    offspring = blob.replicate()
                    new_blobs.append(offspring)
                    self.stats['total_born'] += 1
        
        self.blobs = new_blobs
        
        # Generar nueva comida
        self._spawn_food()
        
        print(f"Sobrevivieron: {survived} | Murieron: {died} | Se replicaron: {replicated}")
        print(f"👥 Población: {len(self.blobs)}")
        
        # Si la población está extinta, reiniciar con población FIJA
        if len(self.blobs) == 0:
            print(f"Población extinta. Reiniciando con {INITIAL_POPULATION} blobs...")
            self._create_initial_population()
            self.day = 0
    
    def _update_stats(self):
        """Actualiza las estadísticas de la simulación"""
        if len(self.blobs) == 0:
            return
        
        alive_blobs = [b for b in self.blobs if b.alive]
        
        if len(alive_blobs) > 0:
            self.stats['avg_speed'] = sum(b.speed for b in alive_blobs) / len(alive_blobs)
            self.stats['avg_size'] = sum(b.size for b in alive_blobs) / len(alive_blobs)
            self.stats['avg_sense'] = sum(b.sense for b in alive_blobs) / len(alive_blobs)
            self.stats['population'] = len(alive_blobs)
    
    def get_state(self) -> dict:
        """Obtiene el estado actual de la simulación para la GUI"""
        return {
            'day': self.day,
            'time_in_day': self.time_in_day,
            'day_duration': self.day_duration,
            'blobs': [b.to_dict() for b in self.blobs],
            'food': self.food,
            'stats': self.stats,
            'paused': self.paused,
            'speed': self.speed_multiplier
        }
    
    def set_speed(self, speed: float):
        """Establece la velocidad de la simulación"""
        self.speed_multiplier = max(0.1, min(10.0, speed))
        # Ajustar delay inversamente proporcional a la velocidad
        self.step_delay = 0.1 / self.speed_multiplier
    
    def toggle_pause(self):
        """Pausa/reanuda la simulación"""
        self.paused = not self.paused
        return self.paused