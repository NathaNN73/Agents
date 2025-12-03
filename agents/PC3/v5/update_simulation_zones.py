"""
Script para actualizar simulation.js con visualización de zonas de control
"""

# Leer el archivo
with open('simulation.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Agregar función para dibujar zonas de control
draw_zones_function = '''
function drawControlZones(zones) {
    if (!zones) return;
    
    // Dibujar zonas de validación (verdes)
    if (zones.validation) {
        zones.validation.forEach(zone => {
            ctx.fillStyle = 'rgba(34, 197, 94, 0.4)'; // Verde semi-transparente
            ctx.fillRect(
                zone.x - zone.width / 2,
                zone.y - zone.height / 2,
                zone.width,
                zone.height
            );
            
            // Borde verde
            ctx.strokeStyle = '#22c55e';
            ctx.lineWidth = 3;
            ctx.strokeRect(
                zone.x - zone.width / 2,
                zone.y - zone.height / 2,
                zone.width,
                zone.height
            );
        });
    }
    
    // Dibujar zonas de salida (rojas)
    if (zones.exit) {
        zones.exit.forEach(zone => {
            ctx.fillStyle = 'rgba(239, 68, 68, 0.4)'; // Rojo semi-transparente
            ctx.fillRect(
                zone.x - zone.width / 2,
                zone.y - zone.height / 2,
                zone.width,
                zone.height
            );
            
            // Borde rojo
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 3;
            ctx.strokeRect(
                zone.x - zone.width / 2,
                zone.y - zone.height / 2,
                zone.width,
                zone.height
            );
        });
    }
}
'''

# Insertar la función antes de drawEntranceExit
if 'function drawControlZones' not in content:
    content = content.replace(
        'function drawEntranceExit()',
        draw_zones_function + '\nfunction drawEntranceExit()'
    )

# 2. Llamar a drawControlZones en la función render
old_render = '''    // Dibujar plazas de estacionamiento
    if (data.parking_spots) {
        data.parking_spots.forEach(spot => {
            drawParkingSpot(spot);
        });
    }'''

new_render = '''    // Dibujar zonas de control (validación y salida)
    if (data.control_zones) {
        drawControlZones(data.control_zones);
    }
    
    // Dibujar plazas de estacionamiento
    if (data.parking_spots) {
        data.parking_spots.forEach(spot => {
            drawParkingSpot(spot);
        });
    }'''

if old_render in content:
    content = content.replace(old_render, new_render)

# 3. Actualizar estadísticas para mostrar rechazados
old_stats = '''    document.getElementById('statLeft').textContent = stats.total_left || 0;

    document.getElementById('statSearchTime').textContent ='''

new_stats = '''    document.getElementById('statLeft').textContent = stats.total_left || 0;
    
    // Mostrar vehículos rechazados si existe la estadística
    if (stats.total_rejected !== undefined) {
        if (!document.getElementById('statRejected')) {
            // Crear elemento si no existe
            const rejectedStat = document.createElement('div');
            rejectedStat.className = 'stat-item';
            rejectedStat.innerHTML = '<span class="stat-label">🚫 Rechazados:</span><span class="stat-value" id="statRejected">0</span>';
            document.querySelector('.metrics-panel').appendChild(rejectedStat);
        }
        document.getElementById('statRejected').textContent = stats.total_rejected || 0;
    }

    document.getElementById('statSearchTime').textContent ='''

if old_stats in content:
    content = content.replace(old_stats, new_stats)

# Guardar
with open('simulation.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ simulation.js actualizado con visualización de zonas de control")
print("   - Zonas verdes de validación")
print("   - Zonas rojas de salida")
print("   - Estadística de vehículos rechazados")
