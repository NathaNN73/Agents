"""
BlobAgent - Agente SPADE que representa una criatura en la simulación
"""
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message as SpadeMessage
from spade.template import Template
import asyncio
import math
import random
from typing import Optional, List, Dict, Tuple
from config import *
from messages import *
from agent_utils import AgentUtils


class BlobAgent(Agent):
    """Agente que representa un blob en la simulación"""
    
    def __init__(self, jid: str, password: str, blob_id: int, 
                 x: float, y: float, speed: float, size: float, 
                 sense: float, generation: int = 0):
        super().__init__(jid, password)
        
        # Identificación
        self.blob_id = blob_id
        self.generation = generation
        
        # Posición
        self.x = x
        self.y = y
        self.home_x = x
        self.home_y = y
        
        # Rasgos
        self.speed = speed
        self.size = size
        self.sense = sense
        
        # Estado
        self.energy = BASE_ENERGY
        self.food_collected = 0
        self.alive = True
        self.at_home = False
        
        # Objetivo actual
        self.target_x = None
        self.target_y = None
        
        # Conocimiento del entorno
        self.known_food: List[Dict] = []
        self.nearby_blobs: List[Dict] = []
        
        # JID del agente de entorno
        self.environment_jid = ENVIRONMENT_JID
        
    async def setup(self):
        """Inicializa el agente y sus comportamientos"""
        print(f"🐛 Blob {self.blob_id} iniciado en ({self.x:.1f}, {self.y:.1f})")
        
        # Agregar comportamiento de registro (OneShot)
        self.add_behaviour(self.RegisterBehaviour())
        
        # Agregar otros comportamientos
        template = Template()
        template.set_metadata("performative", "inform") # Opcional, pero buena práctica
        self.add_behaviour(MessageHandlerBehaviour(), template)
        
        self.add_behaviour(SurvivalBehaviour())
        
    class RegisterBehaviour(OneShotBehaviour):
        """Comportamiento para registrar el blob al iniciar"""
        
        async def run(self):
            print(f"📤 Blob {self.agent.blob_id} enviando registro a {self.agent.environment_jid}")
            msg = SpadeMessage(to=self.agent.environment_jid)
            msg.body = RegisterBlobMessage.create(
                self.agent.blob_id, str(self.agent.jid), self.agent.x, self.agent.y,
                self.agent.speed, self.agent.size, self.agent.sense
            )
            await self.send(msg)
            print(f"✅ Blob {self.agent.blob_id} registro enviado")
    
    def get_energy_cost_per_step(self) -> float:
        """Calcula el costo de energía por paso"""
        movement_cost = (self.size ** 3) * (self.speed ** 2)
        sense_cost = self.sense
        return movement_cost + sense_cost
    
    def move_towards(self, target_x: float, target_y: float):
        """Mueve el blob hacia un objetivo"""
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
        dx, dy = AgentUtils.normalize_direction(dx, dy)
        
        # Mover según velocidad
        move_distance = self.speed
        actual_distance = min(move_distance, distance)
        
        self.x += dx * actual_distance
        self.y += dy * actual_distance
        
        # Mantener dentro del mapa
        self.x, self.y = AgentUtils.clamp_position(self.x, self.y)
        
        # Consumir energía
        energy_cost = self.get_energy_cost_per_step() * 0.05
        self.energy -= energy_cost
        
        if self.energy <= 0:
            self.alive = False
    
    def is_at_home(self) -> bool:
        """Verifica si el blob está en casa"""
        dist = AgentUtils.calculate_distance(self.x, self.y, self.home_x, self.home_y)
        return dist < 5.0
    
    def find_nearest_food(self) -> Optional[Dict]:
        """Encuentra la comida más cercana dentro del rango de sentido"""
        nearest = None
        nearest_dist = self.sense
        
        for food in self.known_food:
            if food.get('consumed', False):
                continue
            
            dist = AgentUtils.calculate_distance(
                self.x, self.y, food['x'], food['y']
            )
            
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = food
        
        return nearest
    
    def find_threat(self) -> Optional[Dict]:
        """Encuentra amenazas (blobs más grandes) cercanas"""
        for blob in self.nearby_blobs:
            if blob['blob_id'] == self.blob_id:
                continue
            
            dist = AgentUtils.calculate_distance(
                self.x, self.y, blob['x'], blob['y']
            )
            
            if dist < self.sense and blob['size'] >= self.size * SIZE_EAT_THRESHOLD:
                return blob
        
        return None
    
    def find_prey(self) -> Optional[Dict]:
        """Encuentra presas (blobs más pequeños) cercanas"""
        for blob in self.nearby_blobs:
            if blob['blob_id'] == self.blob_id:
                continue
            
            dist = AgentUtils.calculate_distance(
                self.x, self.y, blob['x'], blob['y']
            )
            
            if dist < self.sense and self.size >= blob['size'] * SIZE_EAT_THRESHOLD:
                return blob
        
        return None
    
    async def notify_death(self, reason: str = "no_energy"):
        """Notifica al entorno que este blob ha muerto (solo actualiza estado interno)"""
        # La notificación real se hará en el comportamiento
        pass
    
    async def consume_food(self, food: Dict):
        """Consume una pieza de comida"""
        self.food_collected += 1
        self.energy += FOOD_ENERGY
        
        # Marcar como consumida localmente
        food['consumed'] = True
        
        # Retornar datos para que el comportamiento envíe el mensaje
        return food
    
    def get_state(self) -> Dict:
        """Obtiene el estado actual del blob"""
        return {
            'id': self.blob_id,
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


class MessageHandlerBehaviour(CyclicBehaviour):
    """Comportamiento para manejar mensajes entrantes"""
    
    async def run(self):
        msg = await self.receive(timeout=0.1)
        
        if msg:
            msg_type, data = Message.parse(msg.body)
            
            if msg_type == MessageType.FOOD_SPAWNED:
                # Actualizar lista de comida conocida
                self.agent.known_food = data.get('food', [])
            
            elif msg_type == MessageType.NEARBY_BLOBS:
                # Actualizar lista de blobs cercanos
                self.agent.nearby_blobs = data.get('blobs', [])
            
            elif msg_type == MessageType.DAY_END:
                # Procesar fin de día
                await self._handle_day_end(data)
            
            elif msg_type == MessageType.STATE_REQUEST:
                # Responder con estado actual
                await self._send_state()
        
        await asyncio.sleep(0.05)
    
    async def _handle_day_end(self, data: Dict):
        """Maneja el fin del día"""
        day = data.get('day', 0)
        
        # Determinar si sobrevivió
        survived = self.agent.alive and self.agent.at_home and self.agent.food_collected >= 1
        
        # Enviar ACK al entorno
        msg = SpadeMessage(to=self.agent.environment_jid)
        msg.body = DayEndAckMessage.create(
            self.agent.blob_id,
            survived,
            self.agent.food_collected,
            self.agent.at_home,
            self.agent.energy
        )
        await self.send(msg)
        
        # Si no sobrevivió, notificar muerte
        if not survived:
            reason = "unknown"
            if not self.agent.alive:
                reason = "no_energy"
            elif not self.agent.at_home:
                reason = "not_home"
            else:
                reason = "no_food"
            
            # Notificar muerte
            msg = SpadeMessage(to=self.agent.environment_jid)
            msg.body = BlobDiedMessage.create(self.agent.blob_id, str(self.agent.jid), reason)
            await self.send(msg)
            
            # Detener el agente
            await self.agent.stop()
    
    async def _send_state(self):
        """Envía el estado actual al entorno"""
        msg = SpadeMessage(to=self.agent.environment_jid)
        msg.body = StateResponseMessage.create(
            self.agent.blob_id,
            self.agent.get_state()
        )
        await self.send(msg)


class SurvivalBehaviour(CyclicBehaviour):
    """Comportamiento principal de supervivencia del blob"""
    
    async def run(self):
        if not self.agent.alive:
            await asyncio.sleep(0.1)
            return
        
        # PRIORIDAD 1: Si tiene suficiente comida o poca energía, volver a casa
        if self.agent.food_collected >= 2 or self.agent.energy < BASE_ENERGY * 0.4:
            self.agent.move_towards(self.agent.home_x, self.agent.home_y)
            
            if self.agent.is_at_home():
                self.agent.at_home = True
            
            await asyncio.sleep(0.05)
            return
        
        # PRIORIDAD 2: Detectar amenazas y huir
        threat = self.agent.find_threat()
        if threat:
            # Huir en dirección opuesta
            dx = self.agent.x - threat['x']
            dy = self.agent.y - threat['y']
            dx, dy = AgentUtils.normalize_direction(dx, dy)
            
            flee_x = self.agent.x + dx * self.agent.sense * FLEE_DISTANCE_MULTIPLIER
            flee_y = self.agent.y + dy * self.agent.sense * FLEE_DISTANCE_MULTIPLIER
            flee_x, flee_y = AgentUtils.clamp_position(flee_x, flee_y)
            
            self.agent.move_towards(flee_x, flee_y)
            await asyncio.sleep(0.05)
            return
        
        # PRIORIDAD 3: Cazar presas
        prey = self.agent.find_prey()
        if prey:
            self.agent.move_towards(prey['x'], prey['y'])
            
            # Verificar si alcanzó la presa (esto se manejará en el entorno)
            dist = AgentUtils.calculate_distance(
                self.agent.x, self.agent.y, prey['x'], prey['y']
            )
            if dist < self.agent.size * 5:
                # El entorno manejará la depredación
                pass
            
            await asyncio.sleep(0.05)
            return
        
        # PRIORIDAD 4: Buscar comida
        food = self.agent.find_nearest_food()
        if food:
            self.agent.move_towards(food['x'], food['y'])
            
            # Verificar si alcanzó la comida
            dist = AgentUtils.calculate_distance(
                self.agent.x, self.agent.y, food['x'], food['y']
            )
            if dist < 8:
                consumed_food = await self.agent.consume_food(food)
                if consumed_food:
                    # Enviar mensaje de comida consumida
                    msg = SpadeMessage(to=self.agent.environment_jid)
                    msg.body = FoodConsumedMessage.create(self.agent.blob_id, consumed_food['x'], consumed_food['y'])
                    await self.send(msg)
            
            await asyncio.sleep(0.05)
            return
        
        # PRIORIDAD 5: Movimiento aleatorio
        if self.agent.target_x is None or \
           AgentUtils.calculate_distance(self.agent.x, self.agent.y, 
                                        self.agent.target_x, self.agent.target_y) < 10:
            self.agent.target_x, self.agent.target_y = AgentUtils.generate_food_position()
        
        self.agent.move_towards(self.agent.target_x, self.agent.target_y)
        
        # Verificar si murió por falta de energía
        if not self.agent.alive:
            # Notificar muerte
            msg = SpadeMessage(to=self.agent.environment_jid)
            msg.body = BlobDiedMessage.create(self.agent.blob_id, str(self.agent.jid), "no_energy")
            await self.send(msg)
            
            await self.agent.stop()
        
        await asyncio.sleep(0.05)
