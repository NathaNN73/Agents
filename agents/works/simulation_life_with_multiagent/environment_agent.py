"""
EnvironmentAgent - Agente central que coordina la simulación
"""
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message as SpadeMessage
import asyncio
import random
from typing import List, Dict
from config import *
from messages import *
from agent_utils import AgentUtils
from blob_agent import BlobAgent


class EnvironmentAgent(Agent):
    """Agente que maneja el entorno y coordina la simulación"""
    
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        
        # Estado de la simulación
        self.day = 0
        self.time_in_day = 0.0
        self.day_duration = 1000.0
        
        # Registro de blobs
        self.registered_blobs: Dict[int, Dict] = {}  # blob_id -> info
        self.blob_agents: List[BlobAgent] = []  # Referencias a agentes blob
        
        # Comida
        self.food: List[Dict] = []
        
        # Control
        self.paused = False
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
        
        # Respuestas de fin de día
        self.day_end_acks: Dict[int, Dict] = {}

        self.day_cycle_started = False
        
    async def setup(self):
        """Inicializa el agente de entorno"""
        print("🌍 Agente de entorno iniciado")
        
        # Generar comida inicial
        self._spawn_food()
        
        # Agregar comportamientos
        self.add_behaviour(MessageHandlerBehaviour())
        self.add_behaviour(DayCycleBehaviour(period=0.01))  # Cada 100ms
        self.add_behaviour(BroadcastFoodBehaviour(period=2.0))  # Cada 2s
        self.add_behaviour(BroadcastPositionsBehaviour(period=POSITION_BROADCAST_INTERVAL))
        self.add_behaviour(RequestStateBehaviour(period=STATE_UPDATE_INTERVAL))
        
        print(f"✅ Entorno listo. Comida inicial: {len(self.food)} piezas")
    
    def _spawn_food(self):
        """Genera comida aleatoria en el mapa"""
        self.food = []
        for i in range(FOOD_PER_DAY):
            x, y = AgentUtils.generate_food_position()
            food = {
                'id': i,
                'x': x,
                'y': y,
                'consumed': False
            }
            self.food.append(food)
    
    def register_blob(self, blob_id: int, jid: str, x: float, y: float,
                     speed: float, size: float, sense: float):
        """Registra un nuevo blob"""
        self.registered_blobs[blob_id] = {
            'blob_id': blob_id,
            'jid': jid,  # JID completo con recurso (z3r007@xmpp.jp/blob_1)
            'x': x,
            'y': y,
            'speed': speed,
            'size': size,
            'sense': sense,
            'alive': True
        }
        self.stats['total_born'] += 1
        self.stats['population'] = len([b for b in self.registered_blobs.values() if b['alive']])
        print(f"📝 Blob {blob_id} registrado. Población: {self.stats['population']}")
    
    def unregister_blob(self, blob_id: int, reason: str = "unknown"):
        """Desregistra un blob muerto"""
        if blob_id in self.registered_blobs:
            self.registered_blobs[blob_id]['alive'] = False
            self.stats['total_died'] += 1
            self.stats['population'] = len([b for b in self.registered_blobs.values() if b['alive']])
            print(f"💀 Blob {blob_id} murió ({reason}). Población: {self.stats['population']}")
    
    def mark_food_consumed(self, food_x: float, food_y: float):
        """Marca una pieza de comida como consumida"""
        for food in self.food:
            if not food['consumed']:
                dist = AgentUtils.calculate_distance(food['x'], food['y'], food_x, food_y)
                if dist < 10:  # Tolerancia
                    food['consumed'] = True
                    break
    
    async def broadcast_food_locations(self):
        """Devuelve la lista de comida disponible para enviar"""
        return [f for f in self.food if not f['consumed']]
    
    async def get_nearby_blobs(self, blob_info):
        """Calcula blobs cercanos para un blob específico"""
        alive_blobs = [b for b in self.registered_blobs.values() if b['alive']]
        nearby = []
        for other in alive_blobs:
            if other['blob_id'] == blob_info['blob_id']:
                continue
            
            dist = AgentUtils.calculate_distance(
                blob_info['x'], blob_info['y'],
                other['x'], other['y']
            )
            
            if dist < blob_info['sense'] * 1.5:
                nearby.append({
                    'blob_id': other['blob_id'],
                    'x': other['x'],
                    'y': other['y'],
                    'size': other['size']
                })
        return nearby
    
    async def end_day(self):
        """Finaliza el día actual"""
        self.day += 1
        self.time_in_day = 0.0
        self.day_end_acks = {}
        
        print(f"\n🌅 Finalizando día {self.day}...")
        return self.day
    
    async def _process_day_end(self):
        """Procesa la supervivencia y replicación al final del día"""
        survived = 0
        died = 0
        replicated = 0
        
        # Procesar cada blob
        for blob_id, ack_data in self.day_end_acks.items():
            if ack_data['survived']:
                survived += 1
                
                # Si recolectó 2+ comida, se replica
                if ack_data['food_collected'] >= 2:
                    replicated += 1
                    # La replicación se manejará creando nuevos agentes
                    # (esto se hará en main.py después de recibir la señal)
        
        # Contar muertes
        for blob_info in self.registered_blobs.values():
            if not blob_info['alive']:
                died += 1
        
        print(f"Sobrevivieron: {survived} | Murieron: {died} | Se replicarán: {replicated}")
        
        # Generar nueva comida
        self._spawn_food()
        
        # Actualizar estadísticas
        self._update_stats()
    
    def _update_stats(self):
        """Actualiza las estadísticas de la simulación"""
        alive_blobs = [b for b in self.registered_blobs.values() if b['alive']]
        
        if len(alive_blobs) > 0:
            self.stats['avg_speed'] = sum(b['speed'] for b in alive_blobs) / len(alive_blobs)
            self.stats['avg_size'] = sum(b['size'] for b in alive_blobs) / len(alive_blobs)
            self.stats['avg_sense'] = sum(b['sense'] for b in alive_blobs) / len(alive_blobs)
            self.stats['population'] = len(alive_blobs)
    
    def get_state(self) -> Dict:
        """Obtiene el estado actual de la simulación"""
        # Construir lista de blobs con estado actualizado
        blobs_state = []
        for blob_info in self.registered_blobs.values():
            blobs_state.append({
                'id': blob_info['blob_id'],
                'x': blob_info['x'],
                'y': blob_info['y'],
                'speed': blob_info['speed'],
                'size': blob_info['size'],
                'sense': blob_info['sense'],
                'alive': blob_info['alive']
            })
        
        return {
            'day': self.day,
            'time_in_day': self.time_in_day,
            'day_duration': self.day_duration,
            'blobs': blobs_state,
            'food': self.food,
            'stats': self.stats,
            'paused': self.paused,
            'speed': self.speed_multiplier
        }
    
    def set_speed(self, speed: float):
        """Establece la velocidad de la simulación"""
        self.speed_multiplier = max(0.1, min(10.0, speed))
    
    def toggle_pause(self):
        """Pausa/reanuda la simulación"""
        self.paused = not self.paused
        return self.paused


class MessageHandlerBehaviour(CyclicBehaviour):
    """Maneja mensajes entrantes de los blobs"""
    
    async def run(self):
        msg = await self.receive(timeout=0.1)
        
        if msg:
            msg_type, data = Message.parse(msg.body)
            
            if msg_type == MessageType.REGISTER_BLOB:
                # Registrar nuevo blob
                # El JID viene completo (z3r007@xmpp.jp/blob_1), extraer el recurso
                jid = data['jid']
                self.agent.register_blob(
                    data['blob_id'],
                    jid,  # Pasar JID completo
                    data['x'],
                    data['y'],
                    data['speed'],
                    data['size'],
                    data['sense']
                )
            
            elif msg_type == MessageType.BLOB_DIED:
                # Desregistrar blob muerto
                self.agent.unregister_blob(
                    data['blob_id'],
                    data.get('reason', 'unknown')
                )
            
            elif msg_type == MessageType.FOOD_CONSUMED:
                # Marcar comida como consumida
                self.agent.mark_food_consumed(data['food_x'], data['food_y'])
            
            elif msg_type == MessageType.DAY_END_ACK:
                # Recibir confirmación de fin de día
                self.agent.day_end_acks[data['blob_id']] = data
            
            elif msg_type == MessageType.STATE_RESPONSE:
                # Actualizar posición del blob
                blob_id = data['blob_id']
                if blob_id in self.agent.registered_blobs:
                    state = data['state']
                    self.agent.registered_blobs[blob_id].update({
                        'x': state['x'],
                        'y': state['y'],
                        'energy': state.get('energy', 0),
                        'food_collected': state.get('food_collected', 0),
                        'at_home': state.get('at_home', False)
                    })
        
        await asyncio.sleep(0.05)


class DayCycleBehaviour(PeriodicBehaviour):
    """Maneja el ciclo de día"""
    
    async def run(self):
        if self.agent.paused:
            return
        
        # Incrementar tiempo
        self.agent.time_in_day += 1 * self.agent.speed_multiplier
        
        # Verificar fin del día
        if self.agent.time_in_day >= self.agent.day_duration:
            day = await self.agent.end_day()
            
            # Enviar mensaje de fin de día a todos los blobs vivos
            alive_blobs = [b for b in self.agent.registered_blobs.values() if b['alive']]
            
            for blob_info in alive_blobs:
                msg = SpadeMessage(to=blob_info['jid'])
                msg.body = DayEndMessage.create(day)
                await self.send(msg)
            
            # Esperar respuestas (con timeout)
            await asyncio.sleep(2.0)
            
            # Procesar supervivencia y replicación
            await self.agent._process_day_end()
            
            # Broadcast nueva comida (lo hará BroadcastFoodBehaviour)


class BroadcastFoodBehaviour(PeriodicBehaviour):
    """Envía ubicaciones de comida periódicamente"""
    
    async def run(self):
        if not self.agent.paused:
            available_food = await self.agent.broadcast_food_locations()
            
            for blob_info in self.agent.registered_blobs.values():
                if not blob_info['alive']:
                    continue
                
                msg = SpadeMessage(to=blob_info['jid'])
                msg.body = FoodSpawnedMessage.create(available_food)
                await self.send(msg)


class BroadcastPositionsBehaviour(PeriodicBehaviour):
    """Envía posiciones de blobs cercanos periódicamente"""
    
    async def run(self):
        if not self.agent.paused:
            alive_blobs = [b for b in self.agent.registered_blobs.values() if b['alive']]
            
            for blob_info in alive_blobs:
                nearby = await self.agent.get_nearby_blobs(blob_info)
                
                # Enviar mensaje
                msg = SpadeMessage(to=blob_info['jid'])
                msg.body = Message.create(MessageType.NEARBY_BLOBS, {'blobs': nearby})
                await self.send(msg)


class RequestStateBehaviour(PeriodicBehaviour):
    """Solicita el estado actual a todos los blobs periódicamente"""
    
    async def run(self):
        if not self.agent.paused:
            alive_blobs = [b for b in self.agent.registered_blobs.values() if b['alive']]
            
            for blob_info in alive_blobs:
                msg = SpadeMessage(to=blob_info['jid'])
                msg.body = Message.create(MessageType.STATE_REQUEST, {})
                await self.send(msg)
