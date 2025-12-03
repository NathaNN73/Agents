# Refactorización del Sistema de Estacionamiento v5

## Resumen de Cambios

Se ha refactorizado el proyecto v5 para implementar un sistema de generación de vehículos con delay y una nueva ruta de entrada desde la esquina superior izquierda.

## Cambios Principales

### 1. **config.py**
- ✅ Agregado `VEHICLE_SPAWN_DELAY = 2.0` - Controla el delay entre spawns de vehículos
- ✅ Agregado `ENTRY_POINT_X = 50` y `ENTRY_POINT_Y = 50` - Punto de entrada en esquina superior izquierda

### 2. **parking_agent.py**
- ✅ **Sistema de Cola de Spawn**: Implementado `spawn_queue` para gestionar vehículos pendientes
- ✅ **Spawn con Delay**: Los vehículos se generan con un delay de 2 segundos entre ellos
- ✅ **Nueva Ruta de Entrada**: 
  - Los vehículos entran desde (50, 50) - esquina superior izquierda
  - Bajan verticalmente hasta la mitad del mapa
  - Giran a la derecha para entrar al área de parking
- ✅ **Nuevo Estado ENTERING**: Estado adicional para vehículos que están siguiendo la ruta de entrada
- ✅ **Método `_generate_entry_path()`**: Genera waypoints para la ruta de entrada
- ✅ **Método `_process_spawn_queue()`**: Procesa la cola respetando el delay configurado
- ✅ **Método `_queue_vehicle()`**: Agrega vehículos a la cola de spawn

### 3. **vehicle.py**
- ✅ **Detección de Colisiones Mejorada**: 
  - Vehículos en estado ENTERING ignoran colisiones entre sí
  - Permite que múltiples vehículos sigan la ruta de entrada sin bloquearse
  - Mantiene la detección de colisiones para otros estados

## Flujo de Vehículos

1. **Generación**: Vehículos se agregan a `spawn_queue` con tiempo de spawn
2. **Spawn con Delay**: Sistema espera 2 segundos entre cada spawn
3. **Estado ENTERING**: Vehículo sigue ruta desde (50,50) → (50, 300) → (150, 300)
4. **Estado ARRIVING**: Vehículo espera asignación de plaza
5. **Estado MOVING_TO_SPOT**: Vehículo se dirige a su plaza asignada
6. **Estado PARKED**: Vehículo estacionado
7. **Estado LEAVING**: Vehículo sale del parking

## Beneficios

- ✅ **Menos Colisiones**: El delay entre spawns evita aglomeraciones en la entrada
- ✅ **Entrada Más Realista**: Los vehículos entran desde arriba-izquierda como en un parking real
- ✅ **Mejor Flujo**: La ruta de entrada está separada del área de parking principal
- ✅ **Escalabilidad**: El sistema de cola permite gestionar mejor múltiples vehículos

## Parámetros Configurables

En `config.py` puedes ajustar:
- `VEHICLE_SPAWN_DELAY`: Delay entre spawns (default: 2.0 segundos)
- `VEHICLE_ARRIVAL_INTERVAL`: Intervalo entre generación de nuevos vehículos (default: 4.0 segundos)
- `ENTRY_POINT_X`, `ENTRY_POINT_Y`: Coordenadas del punto de entrada
- `INITIAL_VEHICLES`: Número de vehículos iniciales en la cola (default: 8)

## Prueba del Sistema

Para ejecutar el sistema refactorizado:

```bash
python main.py
```

Luego abre http://localhost:10000 en tu navegador para ver la simulación.
