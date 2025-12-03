from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio
import random
import math
from typing import List, Dict, Optional, Tuple
from vehicle import Vehicle
from config import *

class ParkingBehaviour(CyclicBehaviour):
    async def run(self):
        await asyncio.sleep(self.agent.step_delay)
        if self.agent.paused:
            return
        await self.agent.update_parking_system()

class ParkingAgent(Agent):
    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        
        self.vehicles: List[Vehicle] = []
        self.parking_spots: Dict[int, Dict] = {}
        self.simulation_time = 0.0
        self.next_arrival_time = 0.0
        
        self.paused = False
        self.step_delay = 0.1
        self.speed_multiplier = 1.0
        
        self.stats = {
            'total_arrived': 0,
            'total_parked': 0,
            'total_left': 0,
            'avg_search_time': 0.0,
            'avg_parking_time': 0.0,
            'current_occupancy': 0,
            'total_reassignments': 0,
            'spots_free': TOTAL_SPOTS,
            'spots_occupied': 0,
            'vehicles_waiting': 0
        }
        
        self.search_times = []
        self.parking_times = []
        
        # Layout del parking
        self.parking_layout = {
            'entrance_x': 50,
            'entrance_y': MAP_HEIGHT / 2,
            'exit_x': MAP_WIDTH - 50,
            'exit_y': MAP_HEIGHT / 2,
            'main_aisle_y': MAP_HEIGHT / 2,
            'rows_start_x': 100
        }
    
    async def setup(self):
        print("🅿️ Agente de Parking iniciado")
        self._create_parking_spots()
        self._create_initial_vehicles()
        
        behaviour = ParkingBehaviour()
        self.add_behaviour(behaviour)
        
        print(f"Sistema inicializado: {TOTAL_SPOTS} plazas, {len(self.vehicles)} vehículos")
    
    def _create_parking_spots(self):
        """Crea layout de parking con plazas organizadas en filas"""
        self.parking_spots = {}
        spot_id = 0
        
        # Distribución de tipos especiales
        special_spots = []
        for _ in range(SPOTS_DISCAPACITADOS):
            special_spots.append("discapacitado")
        for _ in range(SPOTS_ELECTRICOS):
            special_spots.append("electrico")
        while len(special_spots) < TOTAL_SPOTS:
            special_spots.append("normal")
        random.shuffle(special_spots)
        
        # Organizar plazas en filas
        rows_start_x = self.parking_layout['rows_start_x']
        row_spacing = (MAP_WIDTH - rows_start_x - 100) / PARKING_COLS
        
        for row in range(PARKING_ROWS):
            # Alternar lados (arriba y abajo del pasillo principal)
            if row < PARKING_ROWS // 2:
                # Plazas arriba
                y = 100 + row * (SPOT_HEIGHT + 10)
                side = "top"
            else:
                # Plazas abajo
                y = MAP_HEIGHT - 100 - (row - PARKING_ROWS // 2) * (SPOT_HEIGHT + 10)
                side = "bottom"
            
            for col in range(PARKING_COLS):
                x = rows_start_x + col * row_spacing + row_spacing / 2
                
                # Calcular zona
                if col < PARKING_COLS // 3:
                    zone = "near"
                elif col < 2 * PARKING_COLS // 3:
                    zone = "middle"
                else:
                    zone = "far"
                
                self.parking_spots[spot_id] = {
                    'id': spot_id,
                    'x': x,
                    'y': y,
                    'row': row,
                    'col': col,
                    'side': side,
                    'type': special_spots[spot_id],
                    'zone': zone,
                    'occupied': False,
                    'reserved_by': None,
                    'distance_to_entrance': math.sqrt(
                        (x - self.parking_layout['entrance_x'])**2 + 
                        (y - self.parking_layout['entrance_y'])**2
                    )
                }
                spot_id += 1
    
    def _generate_path_to_spot(self, vehicle: Vehicle, spot: Dict) -> List[Tuple[float, float]]:
        """Genera ruta de waypoints desde posición actual hasta la plaza"""
        waypoints = []
        
        # 1. Moverse hacia el pasillo principal si no está ahí
        main_aisle_y = self.parking_layout['main_aisle_y']
        if abs(vehicle.y - main_aisle_y) > 20:
            waypoints.append((vehicle.x, main_aisle_y))
        
        # 2. Moverse horizontalmente por el pasillo principal hasta la columna de la plaza
        target_col_x = spot['x']
        waypoints.append((target_col_x, main_aisle_y))
        
        # 3. Girar hacia el pasillo vertical de esa columna
        if spot['side'] == "top":
            # Plaza está arriba del pasillo principal
            aisle_y = spot['y'] + SPOT_HEIGHT / 2 + AISLE_WIDTH / 2
        else:
            # Plaza está abajo
            aisle_y = spot['y'] - SPOT_HEIGHT / 2 - AISLE_WIDTH / 2
        
        waypoints.append((target_col_x, aisle_y))
        
        # 4. Finalmente, entrar a la plaza
        waypoints.append((spot['x'], spot['y']))
        
        return waypoints
    
    def _create_initial_vehicles(self):
        """Crea vehículos iniciales con separación"""
        entrance_x = self.parking_layout['entrance_x']
        entrance_y = self.parking_layout['entrance_y']
        
        for i in range(INITIAL_VEHICLES):
            vehicle_type = random.choices(
                ["normal", "discapacitado", "electrico"],
                weights=[0.85, 0.05, 0.10]
            )[0]
            
            # Posicionar con separación horizontal
            offset_x = i * 15  # Separación de 15 píxeles
            vehicle = Vehicle(entrance_x + offset_x, entrance_y, vehicle_type)
            vehicle.arrival_time = self.simulation_time
            self.vehicles.append(vehicle)
            self.stats['total_arrived'] += 1
    
    async def update_parking_system(self):
        dt = 0.1 * self.speed_multiplier
        self.simulation_time += dt
        
        if self.simulation_time >= self.next_arrival_time and len(self.vehicles) < MAX_VEHICLES:
            await self._spawn_vehicle()
            self.next_arrival_time = self.simulation_time + VEHICLE_ARRIVAL_INTERVAL
        
        for vehicle in self.vehicles[:]:
            if not vehicle.active:
                continue
            await self._update_vehicle_behaviour(vehicle, dt)
        
        self._update_stats()
    
    async def _spawn_vehicle(self):
        """Genera un nuevo vehículo con posición libre"""
        entrance_x = self.parking_layout['entrance_x']
        entrance_y = self.parking_layout['entrance_y']
        
        # Buscar posición libre en la entrada
        offset = 0
        max_attempts = 10
        for attempt in range(max_attempts):
            test_x = entrance_x + offset
            test_y = entrance_y
            
            # Verificar si hay espacio
            collision = False
            for other in self.vehicles:
                if not other.active:
                    continue
                dist = math.sqrt((other.x - test_x)**2 + (other.y - test_y)**2)
                if dist < VEHICLE_SIZE * 3:
                    collision = True
                    break
            
            if not collision:
                break
            
            offset += 15
        
        vehicle_type = random.choices(
            ["normal", "discapacitado", "electrico"],
            weights=[0.85, 0.05, 0.10]
        )[0]
        
        vehicle = Vehicle(entrance_x + offset, entrance_y, vehicle_type)
        vehicle.arrival_time = self.simulation_time
        self.vehicles.append(vehicle)
        self.stats['total_arrived'] += 1
    
    async def _update_vehicle_behaviour(self, vehicle: Vehicle, dt: float):
        if vehicle.state == "ARRIVING":
            spot = self._assign_spot(vehicle)
            if spot:
                vehicle.assigned_spot = spot['id']
                vehicle.spot_x = spot['x']
                vehicle.spot_y = spot['y']
                vehicle.spot_row = spot['row']
                vehicle.spot_col = spot['col']
                vehicle.state = "MOVING_TO_SPOT"
                vehicle.assignment_time = self.simulation_time
                vehicle.search_time = vehicle.assignment_time - vehicle.arrival_time
                
                # Generar ruta
                waypoints = self._generate_path_to_spot(vehicle, spot)
                vehicle.set_waypoints(waypoints)
                
                self.parking_spots[spot['id']]['reserved_by'] = vehicle.id
        
        elif vehicle.state == "MOVING_TO_SPOT":
            # Mover siguiendo waypoints, evitando colisiones
            arrived = vehicle.move_along_path(
                list(self.parking_spots.values()),
                self.vehicles
            )
            
            if arrived or vehicle.has_reached_spot():
                self.parking_spots[vehicle.assigned_spot]['occupied'] = True
                self.parking_spots[vehicle.assigned_spot]['reserved_by'] = None
                vehicle.state = "PARKED"
                vehicle.parking_time = self.simulation_time
                self.stats['total_parked'] += 1
                self.search_times.append(vehicle.search_time)
        
        elif vehicle.state == "PARKED":
            vehicle.parked_time += dt
            
            if vehicle.parked_time >= vehicle.parking_duration:
                vehicle.state = "LEAVING"
                self.parking_spots[vehicle.assigned_spot]['occupied'] = False
                total_time = self.simulation_time - vehicle.arrival_time
                self.parking_times.append(total_time)
        
        elif vehicle.state == "LEAVING":
            exit_x = self.parking_layout['exit_x']
            exit_y = self.parking_layout['exit_y']
            arrived = vehicle.move_towards(exit_x, exit_y)
            
            if arrived:
                vehicle.active = False
                self.vehicles.remove(vehicle)
                self.stats['total_left'] += 1
    
    def _assign_spot(self, vehicle: Vehicle) -> Optional[Dict]:
        if ASSIGNMENT_STRATEGY == "greedy":
            return self._assign_greedy(vehicle)
        elif ASSIGNMENT_STRATEGY == "balanced":
            return self._assign_balanced(vehicle)
        elif ASSIGNMENT_STRATEGY == "priority":
            return self._assign_priority(vehicle)
        return self._assign_greedy(vehicle)
    
    def _assign_greedy(self, vehicle: Vehicle) -> Optional[Dict]:
        available = [
            spot for spot in self.parking_spots.values()
            if not spot['occupied'] and spot['reserved_by'] is None
        ]
        
        if not available:
            return None
        
        available.sort(key=lambda s: s['distance_to_entrance'])
        return available[0]
    
    def _assign_balanced(self, vehicle: Vehicle) -> Optional[Dict]:
        available = [
            spot for spot in self.parking_spots.values()
            if not spot['occupied'] and spot['reserved_by'] is None
        ]
        
        if not available:
            return None
        
        zone_occupancy = {'near': 0, 'middle': 0, 'far': 0}
        zone_total = {'near': 0, 'middle': 0, 'far': 0}
        
        for spot in self.parking_spots.values():
            zone_total[spot['zone']] += 1
            if spot['occupied']:
                zone_occupancy[spot['zone']] += 1
        
        zone_percent = {
            zone: (zone_occupancy[zone] / zone_total[zone] if zone_total[zone] > 0 else 0)
            for zone in zone_occupancy
        }
        
        min_zone = min(zone_percent, key=zone_percent.get)
        zone_spots = [s for s in available if s['zone'] == min_zone]
        
        if zone_spots:
            zone_spots.sort(key=lambda s: s['distance_to_entrance'])
            return zone_spots[0]
        
        available.sort(key=lambda s: s['distance_to_entrance'])
        return available[0]
    
    def _assign_priority(self, vehicle: Vehicle) -> Optional[Dict]:
        available = [
            spot for spot in self.parking_spots.values()
            if not spot['occupied'] and spot['reserved_by'] is None
        ]
        
        if not available:
            return None
        
        if vehicle.vehicle_type != "normal":
            type_spots = [s for s in available if s['type'] == vehicle.vehicle_type]
            if type_spots:
                type_spots.sort(key=lambda s: s['distance_to_entrance'])
                return type_spots[0]
        
        available.sort(key=lambda s: s['distance_to_entrance'])
        return available[0]
    
    def _update_stats(self):
        occupied = sum(1 for s in self.parking_spots.values() if s['occupied'])
        waiting = sum(1 for v in self.vehicles if v.state == "ARRIVING" and v.active)
        
        self.stats['spots_occupied'] = occupied
        self.stats['spots_free'] = TOTAL_SPOTS - occupied
        self.stats['current_occupancy'] = (occupied / TOTAL_SPOTS) * 100 if TOTAL_SPOTS > 0 else 0
        self.stats['vehicles_waiting'] = waiting
        
        if self.search_times:
            self.stats['avg_search_time'] = sum(self.search_times) / len(self.search_times)
        if self.parking_times:
            self.stats['avg_parking_time'] = sum(self.parking_times) / len(self.parking_times)
    
    def get_state(self) -> dict:
        return {
            'simulation_time': self.simulation_time,
            'vehicles': [v.to_dict() for v in self.vehicles if v.active],
            'parking_spots': list(self.parking_spots.values()),
            'stats': self.stats,
            'paused': self.paused,
            'speed': self.speed_multiplier,
            'strategy': ASSIGNMENT_STRATEGY
        }
    
    def set_speed(self, speed: float):
        self.speed_multiplier = max(0.1, min(10.0, speed))
        self.step_delay = 0.1 / self.speed_multiplier
    
    def toggle_pause(self):
        self.paused = not self.paused
        return self.paused