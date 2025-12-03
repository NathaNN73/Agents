from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio
import random
import math
from typing import List, Dict, Optional, Tuple
from vehicle import Vehicle
from config import *
from pathfinding import PathfindingGrid, AStarPathfinder

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
        
        # Sistema de spawn con delay
        self.spawn_queue = []  # Cola de vehículos pendientes de spawn
        self.last_spawn_time = 0.0
        
        # Sistema de pathfinding dinámico
        self.pathfinding_grid = PathfindingGrid(MAP_WIDTH, MAP_HEIGHT, cell_size=10)
        self.pathfinder = AStarPathfinder(self.pathfinding_grid)
        
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
            'vehicles_waiting': 0,
            'path_recalculations': 0
        }
        
        self.search_times = []
        self.parking_times = []
        
        # Layout del parking - entrada desde arriba-izquierda
        self.parking_layout = {
            'entry_x': ENTRY_POINT_X,
            'entry_y': ENTRY_POINT_Y,
            'entry_turn_y': MAP_HEIGHT / 2,  # Punto donde gira hacia la derecha
            'entrance_x': 150,  # Punto de entrada al área de parking
            'entrance_y': MAP_HEIGHT / 2,
            'exit_x': MAP_WIDTH - 50,
            'exit_y': MAP_HEIGHT / 2,
            'main_aisle_y': MAP_HEIGHT / 2,
            'rows_start_x': 200
        }
    
    async def setup(self):
        print("🅿️ Agente de Parking iniciado")
        self._create_parking_spots()
        self._create_initial_vehicles()
        
        behaviour = ParkingBehaviour()
        self.add_behaviour(behaviour)
        
        print(f"Sistema inicializado: {TOTAL_SPOTS} plazas, {len(self.spawn_queue)} vehículos en cola")
        print("✨ Sistema de pathfinding A* activado")
    
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
    
    def _update_pathfinding_grid(self):
        """Actualiza el grid de pathfinding con obstáculos dinámicos"""
        # Limpiar grid
        self.pathfinding_grid.clear_obstacles()
        
        # Agregar plazas ocupadas como obstáculos
        for spot in self.parking_spots.values():
            if spot['occupied']:
                self.pathfinding_grid.add_rect_obstacle(
                    spot['x'], spot['y'], 
                    SPOT_WIDTH + 5, SPOT_HEIGHT + 5
                )
        
        # Agregar vehículos estacionados y bloqueados como obstáculos
        for vehicle in self.vehicles:
            if not vehicle.active:
                continue
            
            # Solo agregar como obstáculo si está estacionado o bloqueado
            if vehicle.state == "PARKED":
                self.pathfinding_grid.add_obstacle(vehicle.x, vehicle.y, VEHICLE_SIZE + 5)
            elif vehicle.state == "MOVING_TO_SPOT":
                # Agregar vehículos que están atascados (no se han movido recientemente)
                if hasattr(vehicle, 'stuck_counter') and vehicle.stuck_counter > 10:
                    self.pathfinding_grid.add_obstacle(vehicle.x, vehicle.y, VEHICLE_SIZE + 3)
    
    def _generate_entry_path(self, vehicle: Vehicle) -> List[Tuple[float, float]]:
        """Genera ruta desde el punto de entrada hasta el área de parking usando A*"""
        self._update_pathfinding_grid()
        
        # Usar A* para encontrar camino
        path = self.pathfinder.find_path(
            vehicle.x, vehicle.y,
            self.parking_layout['entrance_x'], 
            self.parking_layout['entrance_y']
        )
        
        if path:
            return path
        
        # Fallback: ruta simple si A* falla
        waypoints = []
        entry_turn_y = self.parking_layout['entry_turn_y']
        waypoints.append((ENTRY_POINT_X, entry_turn_y))
        entrance_x = self.parking_layout['entrance_x']
        waypoints.append((entrance_x, entry_turn_y))
        return waypoints
    
    def _generate_path_to_spot(self, vehicle: Vehicle, spot: Dict) -> List[Tuple[float, float]]:
        """Genera ruta dinámica desde posición actual hasta la plaza usando A*"""
        self._update_pathfinding_grid()
        
        # Temporalmente marcar la plaza destino como libre para pathfinding
        # (para que el vehículo pueda planear llegar ahí)
        target_x = spot['x']
        target_y = spot['y']
        
        # Usar A* para encontrar el camino
        path = self.pathfinder.find_path(
            vehicle.x, vehicle.y,
            target_x, target_y
        )
        
        if path and len(path) > 0:
            return path
        
        # Fallback: ruta simple si A* falla
        waypoints = []
        main_aisle_y = self.parking_layout['main_aisle_y']
        
        if abs(vehicle.y - main_aisle_y) > 20:
            waypoints.append((vehicle.x, main_aisle_y))
        
        target_col_x = spot['x']
        waypoints.append((target_col_x, main_aisle_y))
        
        if spot['side'] == "top":
            aisle_y = spot['y'] + SPOT_HEIGHT / 2 + AISLE_WIDTH / 2
        else:
            aisle_y = spot['y'] - SPOT_HEIGHT / 2 - AISLE_WIDTH / 2
        
        waypoints.append((target_col_x, aisle_y))
        waypoints.append((spot['x'], spot['y']))
        
        return waypoints
    
    def _create_initial_vehicles(self):
        """Crea vehículos iniciales en la cola de spawn"""
        for i in range(INITIAL_VEHICLES):
            vehicle_type = random.choices(
                ["normal", "discapacitado", "electrico"],
                weights=[0.85, 0.05, 0.10]
            )[0]
            
            # Agregar a la cola de spawn con tiempo de spawn
            spawn_time = i * VEHICLE_SPAWN_DELAY
            self.spawn_queue.append({
                'spawn_time': spawn_time,
                'vehicle_type': vehicle_type
            })
    
    async def update_parking_system(self):
        dt = 0.1 * self.speed_multiplier
        self.simulation_time += dt
        
        # Procesar cola de spawn con delay
        await self._process_spawn_queue()
        
        # Generar nuevos vehículos según intervalo
        if self.simulation_time >= self.next_arrival_time and len(self.vehicles) + len(self.spawn_queue) < MAX_VEHICLES:
            await self._queue_vehicle()
            self.next_arrival_time = self.simulation_time + VEHICLE_ARRIVAL_INTERVAL
        
        for vehicle in self.vehicles[:]:
            if not vehicle.active:
                continue
            await self._update_vehicle_behaviour(vehicle, dt)
        
        self._update_stats()
    
    async def _queue_vehicle(self):
        """Agrega un nuevo vehículo a la cola de spawn"""
        vehicle_type = random.choices(
            ["normal", "discapacitado", "electrico"],
            weights=[0.85, 0.05, 0.10]
        )[0]
        
        self.spawn_queue.append({
            'spawn_time': self.simulation_time,
            'vehicle_type': vehicle_type
        })
    
    async def _process_spawn_queue(self):
        """Procesa la cola de spawn con delay entre vehículos"""
        if not self.spawn_queue:
            return
        
        # Verificar si ha pasado suficiente tiempo desde el último spawn
        if self.simulation_time - self.last_spawn_time < VEHICLE_SPAWN_DELAY:
            return
        
        # Spawn del siguiente vehículo en la cola
        next_vehicle = self.spawn_queue[0]
        if self.simulation_time >= next_vehicle['spawn_time']:
            self.spawn_queue.pop(0)
            await self._spawn_vehicle(next_vehicle['vehicle_type'])
            self.last_spawn_time = self.simulation_time
    
    async def _spawn_vehicle(self, vehicle_type: str):
        """Genera un nuevo vehículo en el punto de entrada"""
        entry_x = self.parking_layout['entry_x']
        entry_y = self.parking_layout['entry_y']
        
        # Crear vehículo en el punto de entrada (arriba-izquierda)
        vehicle = Vehicle(entry_x, entry_y, vehicle_type)
        vehicle.arrival_time = self.simulation_time
        vehicle.state = "ENTERING"  # Nuevo estado para entrada
        vehicle.stuck_counter = 0  # Contador para detectar bloqueos
        vehicle.last_position = (entry_x, entry_y)
        vehicle.path_recalc_timer = 0
        
        # Generar ruta de entrada
        entry_waypoints = self._generate_entry_path(vehicle)
        vehicle.set_waypoints(entry_waypoints)
        
        self.vehicles.append(vehicle)
        self.stats['total_arrived'] += 1
    
    async def _update_vehicle_behaviour(self, vehicle: Vehicle, dt: float):
        # Detectar si el vehículo está atascado
        if vehicle.state in ["ENTERING", "MOVING_TO_SPOT"]:
            dist_moved = math.sqrt(
                (vehicle.x - vehicle.last_position[0])**2 + 
                (vehicle.y - vehicle.last_position[1])**2
            )
            
            if dist_moved < 0.5:  # No se ha movido mucho
                vehicle.stuck_counter = getattr(vehicle, 'stuck_counter', 0) + 1
            else:
                vehicle.stuck_counter = 0
                vehicle.last_position = (vehicle.x, vehicle.y)
            
            # Si está muy atascado, recalcular ruta
            vehicle.path_recalc_timer = getattr(vehicle, 'path_recalc_timer', 0) + dt
            if vehicle.stuck_counter > 20 and vehicle.path_recalc_timer > 2.0:
                await self._recalculate_path(vehicle)
                vehicle.path_recalc_timer = 0
                self.stats['path_recalculations'] += 1
        
        if vehicle.state == "ENTERING":
            # Vehículo está siguiendo la ruta de entrada
            arrived = vehicle.move_along_path(
                list(self.parking_spots.values()),
                self.vehicles
            )
            
            if arrived:
                # Llegó al área de parking, cambiar a estado ARRIVING
                vehicle.state = "ARRIVING"
                vehicle.stuck_counter = 0
        
        elif vehicle.state == "ARRIVING":
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
                
                # Generar ruta usando A*
                waypoints = self._generate_path_to_spot(vehicle, spot)
                vehicle.set_waypoints(waypoints)
                vehicle.stuck_counter = 0
                
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
                vehicle.stuck_counter = 0
        
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
    
    async def _recalculate_path(self, vehicle: Vehicle):
        """Recalcula la ruta de un vehículo atascado"""
        if vehicle.state == "ENTERING":
            # Recalcular ruta de entrada
            new_path = self._generate_entry_path(vehicle)
            if new_path:
                vehicle.set_waypoints(new_path)
                print(f"🔄 Vehículo {vehicle.id}: Ruta de entrada recalculada")
        
        elif vehicle.state == "MOVING_TO_SPOT" and vehicle.assigned_spot is not None:
            # Recalcular ruta a la plaza
            spot = self.parking_spots[vehicle.assigned_spot]
            new_path = self._generate_path_to_spot(vehicle, spot)
            if new_path:
                vehicle.set_waypoints(new_path)
                print(f"🔄 Vehículo {vehicle.id}: Ruta a plaza {vehicle.assigned_spot} recalculada")
    
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