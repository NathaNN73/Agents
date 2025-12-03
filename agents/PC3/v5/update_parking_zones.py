"""
Script para actualizar parking_agent.py con sistema de zonas de control
"""

# Leer el archivo actual
with open('parking_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Agregar import de control_zones
if 'from control_zones import ControlZones' not in content:
    content = content.replace(
        'from lane_network import LaneNetwork',
        'from lane_network import LaneNetwork\nfrom control_zones import ControlZones'
    )

# 2. Agregar inicialización de control_zones
if 'self.control_zones = ControlZones()' not in content:
    content = content.replace(
        '# Red de pistas para navegación realista\n        self.lane_network = LaneNetwork()',
        '# Red de pistas para navegación realista\n        self.lane_network = LaneNetwork()\n        \n        # Sistema de zonas de control (entrada/validación/salida)\n        self.control_zones = ControlZones()'
    )

# 3. Modificar spawn para usar zonas de entrada aleatorias
old_spawn = '''    async def _spawn_vehicle(self, vehicle_type: str):
        """Genera un nuevo vehículo en el punto de entrada"""
        entry_x = self.parking_layout['entry_x']
        entry_y = self.parking_layout['entry_y']
        
        # Crear vehículo en el punto de entrada (arriba-izquierda)
        vehicle = Vehicle(entry_x, entry_y, vehicle_type)
        vehicle.arrival_time = self.simulation_time
        vehicle.state = "ENTERING"  # Nuevo estado para entrada'''

new_spawn = '''    async def _spawn_vehicle(self, vehicle_type: str):
        """Genera un nuevo vehículo en una zona de entrada aleatoria"""
        # Seleccionar zona de entrada aleatoria
        entry_zone = self.control_zones.get_random_entry_zone()
        entry_x = entry_zone['x']
        entry_y = entry_zone['y']
        
        # Crear vehículo en la zona de entrada
        vehicle = Vehicle(entry_x, entry_y, vehicle_type)
        vehicle.arrival_time = self.simulation_time
        vehicle.state = "ENTERING"  # Estado inicial
        vehicle.entry_lane = entry_zone['lane']  # Recordar por qué pista entró'''

if old_spawn in content:
    content = content.replace(old_spawn, new_spawn)

# 4. Modificar comportamiento para validar en zona verde
old_behavior = '''        elif vehicle.state == "ARRIVING":
            spot = self._assign_spot(vehicle)
            if spot:'''

new_behavior = '''        elif vehicle.state == "ENTERING":
            # Verificar si llegó a la zona de validación (franja verde)
            if self.control_zones.is_in_validation_zone(vehicle.x, vehicle.y):
                # Validar si hay espacios disponibles
                spot = self._assign_spot(vehicle)
                if spot:
                    # Hay espacio disponible, asignar y continuar
                    vehicle.state = "ARRIVING"
                else:
                    # NO hay espacio, regresar por donde vino
                    vehicle.state = "REJECTED"
                    print(f"🚫 Vehículo {vehicle.id}: Sin espacios disponibles, regresando...")
                    self.stats['total_rejected'] = self.stats.get('total_rejected', 0) + 1
        
        elif vehicle.state == "ARRIVING":
            # Ya fue validado y tiene espacio asignado
            spot = self.parking_spots.get(vehicle.assigned_spot)
            if spot:'''

if old_behavior in content:
    content = content.replace(old_behavior, new_behavior)

# 5. Agregar estado REJECTED para vehículos rechazados
rejected_state = '''
        elif vehicle.state == "REJECTED":
            # Vehículo rechazado, regresar a la salida de su pista
            exit_zone = self.control_zones.get_exit_zone_for_lane(vehicle.entry_lane)
            exit_x = exit_zone['x']
            exit_y = exit_zone['y']
            
            # Moverse hacia la salida
            arrived = vehicle.move_towards(exit_x, exit_y)
            if arrived or vehicle.x < 0:
                vehicle.active = False
                self.vehicles.remove(vehicle)
'''

# Insertar antes del estado LEAVING
if 'elif vehicle.state == "LEAVING":' in content and rejected_state not in content:
    content = content.replace(
        '        elif vehicle.state == "LEAVING":',
        rejected_state + '        elif vehicle.state == "LEAVING":'
    )

# 6. Modificar LEAVING para usar zonas de salida
old_leaving = '''        elif vehicle.state == "LEAVING":
            exit_x = self.parking_layout['exit_x']
            exit_y = self.parking_layout['exit_y']
            arrived = vehicle.move_towards(exit_x, exit_y)
            
            if arrived:
                vehicle.active = False
                self.vehicles.remove(vehicle)
                self.stats['total_left'] += 1'''

new_leaving = '''        elif vehicle.state == "LEAVING":
            # Usar zona de salida aleatoria
            import random
            exit_zone = random.choice(self.control_zones.exit_zones)
            exit_x = exit_zone['x']
            exit_y = exit_zone['y']
            
            arrived = vehicle.move_towards(exit_x, exit_y)
            
            if arrived or vehicle.x >= MAP_WIDTH - 10:
                vehicle.active = False
                self.vehicles.remove(vehicle)
                self.stats['total_left'] += 1'''

if old_leaving in content:
    content = content.replace(old_leaving, new_leaving)

# 7. Agregar estadística de rechazados
if "'total_rejected': 0," not in content:
    content = content.replace(
        "'vehicles_waiting': 0",
        "'vehicles_waiting': 0,\n            'total_rejected': 0"
    )

# 8. Actualizar get_state para incluir zonas
old_get_state = '''    def get_state(self) -> dict:
        return {
            'simulation_time': self.simulation_time,
            'vehicles': [v.to_dict() for v in self.vehicles if v.active],
            'parking_spots': list(self.parking_spots.values()),
            'stats': self.stats,
            'paused': self.paused,
            'speed': self.speed_multiplier,
            'strategy': ASSIGNMENT_STRATEGY
        }'''

new_get_state = '''    def get_state(self) -> dict:
        return {
            'simulation_time': self.simulation_time,
            'vehicles': [v.to_dict() for v in self.vehicles if v.active],
            'parking_spots': list(self.parking_spots.values()),
            'control_zones': self.control_zones.get_all_zones(),
            'stats': self.stats,
            'paused': self.paused,
            'speed': self.speed_multiplier,
            'strategy': ASSIGNMENT_STRATEGY
        }'''

if old_get_state in content:
    content = content.replace(old_get_state, new_get_state)

# Guardar el archivo actualizado
with open('parking_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ parking_agent.py actualizado con sistema de zonas de control")
print("   - Spawn aleatorio desde 3 pistas")
print("   - Zonas verdes de validación")
print("   - Zonas rojas de salida")
print("   - Lógica de rechazo si no hay espacios")
