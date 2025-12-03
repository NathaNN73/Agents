# Sistema de Pathfinding Dinámico con A*

## 🎯 Problema Resuelto

Los vehículos se quedaban atascados al intentar llegar a sus espacios porque:
- Seguían rutas lineales fijas
- No podían esquivar vehículos estacionados
- No detectaban cuando estaban bloqueados
- No recalculaban rutas alternativas

## ✨ Solución Implementada

Se ha implementado un **sistema de pathfinding dinámico usando el algoritmo A*** que permite:

1. **Navegación Inteligente**: Los vehículos calculan rutas óptimas evitando obstáculos
2. **Detección de Bloqueos**: Sistema que detecta cuando un vehículo está atascado
3. **Recalculación Automática**: Rutas se recalculan automáticamente cuando hay bloqueos
4. **Esquive Dinámico**: Los vehículos pueden tomar rutas alternativas en tiempo real

## 🏗️ Arquitectura del Sistema

### 1. **pathfinding.py** - Módulo de Pathfinding

#### `PathfindingGrid`
- Grid discretizado del mapa (10x10 píxeles por celda)
- Mantiene información de obstáculos dinámicos
- Convierte entre coordenadas del mundo y coordenadas de grid

```python
# Crear grid
grid = PathfindingGrid(MAP_WIDTH, MAP_HEIGHT, cell_size=10)

# Agregar obstáculos
grid.add_obstacle(x, y, radius=15)  # Obstáculo circular
grid.add_rect_obstacle(x, y, width, height)  # Obstáculo rectangular
```

#### `AStarPathfinder`
- Implementa el algoritmo A* para búsqueda de caminos
- Usa **distancia de Manhattan** como heurística
- Soporta movimiento en **8 direcciones** (cardinal + diagonal)
- Simplifica rutas eliminando waypoints innecesarios

```python
# Encontrar camino
pathfinder = AStarPathfinder(grid)
path = pathfinder.find_path(start_x, start_y, goal_x, goal_y)
```

### 2. **parking_agent.py** - Integración del Pathfinding

#### Actualización del Grid Dinámico
```python
def _update_pathfinding_grid(self):
    # Limpiar grid
    self.pathfinding_grid.clear_obstacles()
    
    # Agregar plazas ocupadas
    for spot in self.parking_spots.values():
        if spot['occupied']:
            self.pathfinding_grid.add_rect_obstacle(...)
    
    # Agregar vehículos estacionados
    for vehicle in self.vehicles:
        if vehicle.state == "PARKED":
            self.pathfinding_grid.add_obstacle(...)
```

#### Generación de Rutas Dinámicas
```python
def _generate_path_to_spot(self, vehicle, spot):
    # Actualizar grid con obstáculos actuales
    self._update_pathfinding_grid()
    
    # Usar A* para encontrar camino
    path = self.pathfinder.find_path(
        vehicle.x, vehicle.y,
        spot['x'], spot['y']
    )
    
    return path
```

#### Detección de Bloqueos
```python
# En cada actualización del vehículo
dist_moved = sqrt((vehicle.x - vehicle.last_position[0])**2 + ...)

if dist_moved < 0.5:  # No se ha movido mucho
    vehicle.stuck_counter += 1
else:
    vehicle.stuck_counter = 0
    vehicle.last_position = (vehicle.x, vehicle.y)

# Si está muy atascado (>20 frames sin moverse)
if vehicle.stuck_counter > 20:
    await self._recalculate_path(vehicle)
```

### 3. **vehicle.py** - Atributos de Detección

```python
# Sistema de detección de bloqueos
self.stuck_counter = 0          # Contador de frames sin movimiento
self.last_position = (x, y)     # Última posición conocida
self.path_recalc_timer = 0.0    # Timer para evitar recalcular muy seguido
```

## 🔄 Flujo de Navegación

```
1. Vehículo necesita ir a una plaza
   ↓
2. Se actualiza el grid con obstáculos actuales
   ↓
3. A* calcula la ruta óptima
   ↓
4. Vehículo sigue waypoints
   ↓
5. Sistema detecta si está atascado
   ↓
6. Si stuck_counter > 20:
   - Recalcular ruta con A*
   - Reiniciar stuck_counter
   ↓
7. Continuar hasta llegar al destino
```

## 📊 Características del Algoritmo A*

### Heurística: Distancia de Manhattan
```python
h(n) = |x1 - x2| + |y1 - y2|
```

### Función de Costo
```python
f(n) = g(n) + h(n)

donde:
- g(n) = costo desde el inicio
- h(n) = heurística al objetivo
- f(n) = costo total estimado
```

### Costos de Movimiento
- **Movimiento Cardinal** (↑↓←→): Costo = 1.0
- **Movimiento Diagonal** (↖↗↙↘): Costo = 1.414 (√2)

### Simplificación de Rutas
El algoritmo simplifica rutas eliminando waypoints innecesarios:
- Calcula cambios de dirección entre waypoints consecutivos
- Elimina waypoints si el cambio de dirección es < 25°
- Reduce el número de waypoints manteniendo la forma general del camino

## 🎮 Parámetros Configurables

### En `pathfinding.py`
```python
# Tamaño de celda del grid
cell_size = 10  # píxeles

# Radio de obstáculos
vehicle_obstacle_radius = 15  # para vehículos
spot_obstacle_margin = 5      # para plazas
```

### En `parking_agent.py`
```python
# Detección de bloqueo
stuck_threshold = 20          # frames sin movimiento
movement_threshold = 0.5      # píxeles mínimos de movimiento
recalc_cooldown = 2.0         # segundos entre recalculaciones
```

## 📈 Estadísticas Nuevas

El sistema ahora rastrea:
```python
stats['path_recalculations']  # Número de veces que se recalcularon rutas
```

## 🚀 Ventajas del Sistema

### ✅ Navegación Inteligente
- Los vehículos encuentran rutas óptimas automáticamente
- Evitan obstáculos estáticos (plazas ocupadas)
- Evitan obstáculos dinámicos (otros vehículos)

### ✅ Robustez
- Detecta bloqueos automáticamente
- Recalcula rutas cuando es necesario
- Tiene fallback a rutas simples si A* falla

### ✅ Eficiencia
- Grid discretizado reduce complejidad computacional
- Simplificación de rutas reduce waypoints
- Cooldown evita recalculaciones excesivas

### ✅ Escalabilidad
- Funciona con cualquier número de vehículos
- Se adapta a diferentes layouts de parking
- Configurable para diferentes tamaños de mapa

## 🔧 Debugging

Para ver cuando se recalculan rutas, busca en la consola:
```
🔄 Vehículo 5: Ruta a plaza 12 recalculada
🔄 Vehículo 3: Ruta de entrada recalculada
```

## 📝 Ejemplo de Uso

```python
# El sistema se usa automáticamente, pero puedes:

# 1. Ajustar sensibilidad de detección de bloqueos
vehicle.stuck_counter > 20  # Cambiar umbral

# 2. Modificar frecuencia de recalculación
vehicle.path_recalc_timer > 2.0  # Cambiar cooldown

# 3. Cambiar tamaño de grid para más/menos precisión
PathfindingGrid(MAP_WIDTH, MAP_HEIGHT, cell_size=5)  # Más preciso
PathfindingGrid(MAP_WIDTH, MAP_HEIGHT, cell_size=20) # Más rápido
```

## 🎯 Resultados Esperados

Con este sistema:
- ✅ Los vehículos NO se quedan atascados permanentemente
- ✅ Encuentran rutas alternativas cuando hay bloqueos
- ✅ El flujo de tráfico es más fluido
- ✅ Menos colisiones y esperas innecesarias
- ✅ Mayor throughput del parking

## 🔮 Posibles Mejoras Futuras

1. **Predicción de Movimiento**: Predecir dónde estarán otros vehículos
2. **Priorización**: Dar prioridad a vehículos según tiempo de espera
3. **Reserva de Caminos**: Reservar celdas del grid para evitar conflictos
4. **Heurística Adaptativa**: Ajustar heurística según congestión
5. **Cooperative Pathfinding**: Coordinar rutas entre múltiples vehículos
