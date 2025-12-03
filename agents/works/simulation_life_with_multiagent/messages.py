"""
Protocolos de mensajes para comunicación entre agentes
"""
import json
from typing import Dict, Any, Optional


# Tipos de mensajes
class MessageType:
    # Mensajes de registro y ciclo de vida
    REGISTER_BLOB = "register_blob"
    BLOB_DIED = "blob_died"
    BLOB_BORN = "blob_born"
    
    # Mensajes de comida
    FOOD_SPAWNED = "food_spawned"
    FOOD_CONSUMED = "food_consumed"
    FOOD_LOCATIONS = "food_locations"
    
    # Mensajes de ciclo de día
    DAY_START = "day_start"
    DAY_END = "day_end"
    DAY_END_ACK = "day_end_ack"
    
    # Mensajes de estado
    STATE_REQUEST = "state_request"
    STATE_RESPONSE = "state_response"
    
    # Mensajes entre blobs
    THREAT_DETECTED = "threat_detected"
    BLOB_POSITION = "blob_position"
    NEARBY_BLOBS = "nearby_blobs"


class Message:
    """Clase base para mensajes entre agentes"""
    
    @staticmethod
    def create(msg_type: str, data: Dict[str, Any]) -> str:
        """Crea un mensaje JSON"""
        return json.dumps({
            'type': msg_type,
            'data': data
        })
    
    @staticmethod
    def parse(msg_body: str) -> tuple[str, Dict[str, Any]]:
        """Parsea un mensaje JSON"""
        try:
            msg = json.loads(msg_body)
            return msg.get('type'), msg.get('data', {})
        except json.JSONDecodeError:
            return None, {}


# Mensajes específicos para facilitar creación

class RegisterBlobMessage:
    @staticmethod
    def create(blob_id: int, jid: str, x: float, y: float, 
               speed: float, size: float, sense: float) -> str:
        return Message.create(MessageType.REGISTER_BLOB, {
            'blob_id': blob_id,
            'jid': jid,
            'x': x,
            'y': y,
            'speed': speed,
            'size': size,
            'sense': sense
        })


class BlobDiedMessage:
    @staticmethod
    def create(blob_id: int, jid: str, reason: str = "no_food") -> str:
        return Message.create(MessageType.BLOB_DIED, {
            'blob_id': blob_id,
            'jid': jid,
            'reason': reason
        })


class FoodSpawnedMessage:
    @staticmethod
    def create(food_list: list) -> str:
        return Message.create(MessageType.FOOD_SPAWNED, {
            'food': food_list
        })


class FoodConsumedMessage:
    @staticmethod
    def create(blob_id: int, food_x: float, food_y: float) -> str:
        return Message.create(MessageType.FOOD_CONSUMED, {
            'blob_id': blob_id,
            'food_x': food_x,
            'food_y': food_y
        })


class DayEndMessage:
    @staticmethod
    def create(day: int) -> str:
        return Message.create(MessageType.DAY_END, {
            'day': day
        })


class DayEndAckMessage:
    @staticmethod
    def create(blob_id: int, survived: bool, food_collected: int, 
               at_home: bool, energy: float) -> str:
        return Message.create(MessageType.DAY_END_ACK, {
            'blob_id': blob_id,
            'survived': survived,
            'food_collected': food_collected,
            'at_home': at_home,
            'energy': energy
        })


class StateRequestMessage:
    @staticmethod
    def create() -> str:
        return Message.create(MessageType.STATE_REQUEST, {})


class StateResponseMessage:
    @staticmethod
    def create(blob_id: int, state: Dict[str, Any]) -> str:
        return Message.create(MessageType.STATE_RESPONSE, {
            'blob_id': blob_id,
            'state': state
        })


class BlobPositionMessage:
    @staticmethod
    def create(blob_id: int, x: float, y: float, size: float) -> str:
        return Message.create(MessageType.BLOB_POSITION, {
            'blob_id': blob_id,
            'x': x,
            'y': y,
            'size': size
        })
