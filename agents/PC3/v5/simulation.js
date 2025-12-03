const canvas = document.getElementById('simulationCanvas');
const ctx = canvas.getContext('2d');

let isPaused = false;
let currentSpeed = 1.0;

// Actualiza el estado cada 100ms
async function updateSimulation() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();

        if (data.error) {
            document.getElementById('status').textContent = 'Error: ' + data.error;
            document.getElementById('status').className = 'status error';
            return;
        }

        // Actualizar estado de conexión
        document.getElementById('status').textContent = 'Conectado';
        document.getElementById('status').className = 'status connected';

        // Renderizar simulación
        render(data);

        // Actualizar estadísticas
        updateStats(data);

    } catch (error) {
        console.error('Error fetching simulation state:', error);
        document.getElementById('status').textContent = 'Error de conexión';
        document.getElementById('status').className = 'status error';
    }
}

function render(data) {
    // Limpiar canvas
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Dibujar carriles/pasillos primero (fondo)
    drawParkingLanes();

    // Dibujar plazas de estacionamiento
    if (data.parking_spots) {
        data.parking_spots.forEach(spot => {
            drawParkingSpot(spot);
        });
    }

    // Dibujar vehículos
    if (data.vehicles) {
        data.vehicles.forEach(vehicle => {
            drawVehicle(vehicle);
        });
    }

    // Dibujar entrada y salida
    drawEntranceExit();
}

function drawParkingSpot(spot) {
    const spotWidth = 35;
    const spotHeight = 35;
    const x = spot.x - spotWidth / 2;
    const y = spot.y - spotHeight / 2;

    // Color según estado
    let color;
    if (spot.occupied) {
        color = '#ef4444'; // Rojo (ocupada)
    } else if (spot.reserved_by !== null) {
        color = '#fbbf24'; // Amarillo (reservada)
    } else {
        color = '#4ade80'; // Verde (libre)
    }

    // Dibujar rectángulo de plaza
    ctx.fillStyle = color;
    ctx.fillRect(x, y, spotWidth, spotHeight);

    // Borde
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, spotWidth, spotHeight);

    // NUEVO: Número de plaza con fondo semi-transparente
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.fillRect(x + 2, y + 2, spotWidth - 4, 14);

    ctx.fillStyle = '#fff';
    ctx.font = 'bold 11px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(spot.id, spot.x, y + 9);

    // Indicador de tipo especial (movido más abajo)
    if (spot.type === 'discapacitado') {
        ctx.fillStyle = '#fff';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('♿', spot.x, spot.y + 8);
    } else if (spot.type === 'electrico') {
        ctx.fillStyle = '#fff';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('⚡', spot.x, spot.y + 8);
    }
}

function drawVehicle(vehicle) {
    const size = 12;

    // Color según tipo
    let color;
    if (vehicle.type === 'discapacitado') {
        color = '#8b5cf6'; // Púrpura
    } else if (vehicle.type === 'electrico') {
        color = '#06b6d4'; // Cian
    } else {
        color = '#3b82f6'; // Azul
    }

    // Dibujar vehículo como círculo
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(vehicle.x, vehicle.y, size, 0, Math.PI * 2);
    ctx.fill();

    // Borde
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // ID del vehículo
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 10px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(vehicle.id, vehicle.x, vehicle.y + 1);

    // NUEVO: Mostrar destino si está en camino
    if (vehicle.assigned_spot !== null && vehicle.assigned_spot !== undefined &&
        (vehicle.state === 'ARRIVING' || vehicle.state === 'MOVING_TO_SPOT')) {
        // Fondo para el número de destino
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(vehicle.x - 15, vehicle.y + size + 5, 30, 16);

        // Número de destino con flecha
        ctx.fillStyle = '#fbbf24';
        ctx.font = 'bold 11px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('→' + vehicle.assigned_spot, vehicle.x, vehicle.y + size + 13);
    }

    // Indicador de estado
    if (vehicle.state === 'ARRIVING') {
        // Círculo parpadeante amarillo
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(vehicle.x, vehicle.y, size + 5, 0, Math.PI * 2);
        ctx.stroke();
    } else if (vehicle.state === 'PARKED') {
        // Pequeño punto verde arriba
        ctx.fillStyle = '#4ade80';
        ctx.beginPath();
        ctx.arc(vehicle.x, vehicle.y - size - 5, 3, 0, Math.PI * 2);
        ctx.fill();
    }
}

function drawParkingLanes() {
    const aisleColor = '#475569'; // Gris asfalto
    const lineColor = '#f1f5f9';
    
    // 1. PASILLO HORIZONTAL SUPERIOR (nuevo)
    const topAisleY = 75;
    const topAisleHeight = 50;
    ctx.fillStyle = aisleColor;
    ctx.fillRect(0, topAisleY - topAisleHeight / 2, canvas.width, topAisleHeight);
    
    // Línea central del pasillo superior
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.setLineDash([10, 5]);
    ctx.beginPath();
    ctx.moveTo(0, topAisleY);
    ctx.lineTo(canvas.width, topAisleY);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // 2. PASILLO HORIZONTAL PRINCIPAL (centro)
    const mainAisleY = canvas.height / 2;
    const mainAisleHeight = 60;
    ctx.fillStyle = aisleColor;
    ctx.fillRect(0, mainAisleY - mainAisleHeight / 2, canvas.width, mainAisleHeight);
    
    // Línea central del pasillo principal
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.setLineDash([10, 5]);
    ctx.beginPath();
    ctx.moveTo(0, mainAisleY);
    ctx.lineTo(canvas.width, mainAisleY);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // 3. PASILLO HORIZONTAL INFERIOR (nuevo)
    const bottomAisleY = canvas.height - 75;
    const bottomAisleHeight = 50;
    ctx.fillStyle = aisleColor;
    ctx.fillRect(0, bottomAisleY - bottomAisleHeight / 2, canvas.width, bottomAisleHeight);
    
    // Línea central del pasillo inferior
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 2;
    ctx.setLineDash([10, 5]);
    ctx.beginPath();
    ctx.moveTo(0, bottomAisleY);
    ctx.lineTo(canvas.width, bottomAisleY);
    ctx.stroke();
    ctx.setLineDash([]);

    // 4. PASILLOS VERTICALES (entre columnas)
    const rowsStartX = 200;
    const rowSpacing = (canvas.width - rowsStartX - 100) / 8; // 8 columnas

    for (let i = 0; i <= 8; i++) {
        const x = rowsStartX + i * rowSpacing;

        // Pasillo vertical completo (de arriba a abajo)
        ctx.fillStyle = aisleColor;
        ctx.fillRect(x - 25, 50, 50, canvas.height - 100);
    }
    
    // 5. PASILLO DE ENTRADA (vertical desde arriba-izquierda)
    ctx.fillStyle = aisleColor;
    ctx.fillRect(50 - 20, 50, 40, 50); // Conecta con el pasillo superior
}


function drawEntranceExit() {
    // Entrada (izquierda)
    ctx.fillStyle = '#22c55e';
    ctx.fillRect(5, canvas.height / 2 - 30, 10, 60);
    ctx.fillStyle = '#fff';
    ctx.font = '12px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('ENTRADA', 20, canvas.height / 2);

    // Salida (derecha)
    ctx.fillStyle = '#ef4444';
    ctx.fillRect(canvas.width - 15, canvas.height / 2 - 30, 10, 60);
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'right';
    ctx.fillText('SALIDA', canvas.width - 20, canvas.height / 2);
}

function updateStats(data) {
    const stats = data.stats || {};

    // Tiempo
    document.getElementById('statTime').textContent =
        data.simulation_time ? data.simulation_time.toFixed(1) + 's' : '0s';

    // Ocupación
    document.getElementById('statOccupancy').textContent =
        stats.current_occupancy ? stats.current_occupancy.toFixed(1) + '%' : '0%';

    document.getElementById('statFree').textContent = stats.spots_free || 0;
    document.getElementById('statOccupied').textContent = stats.spots_occupied || 0;
    document.getElementById('statWaiting').textContent = stats.vehicles_waiting || 0;

    // Métricas
    document.getElementById('statArrived').textContent = stats.total_arrived || 0;
    document.getElementById('statParked').textContent = stats.total_parked || 0;
    document.getElementById('statLeft').textContent = stats.total_left || 0;

    document.getElementById('statSearchTime').textContent =
        stats.avg_search_time ? stats.avg_search_time.toFixed(2) + 's' : '0.0s';

    document.getElementById('statStrategy').textContent =
        data.strategy || '-';

    // Nueva estadística: Recalculaciones de pathfinding
    document.getElementById('statRecalcs').textContent = stats.path_recalculations || 0;
}

// Control de pausa
document.getElementById('pauseBtn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/toggle_pause', { method: 'POST' });
        const data = await response.json();
        isPaused = data.paused;

        const btn = document.getElementById('pauseBtn');
        btn.textContent = isPaused ? '▶️ Reanudar' : '⏸️ Pausar';
    } catch (error) {
        console.error('Error toggling pause:', error);
    }
});

// Control de velocidad
document.getElementById('speedSlider').addEventListener('input', (e) => {
    const speed = parseFloat(e.target.value);
    setSpeed(speed);
});

async function setSpeed(speed) {
    try {
        currentSpeed = speed;
        document.getElementById('speedValue').textContent = speed.toFixed(1) + 'x';
        document.getElementById('speedSlider').value = speed;

        await fetch(`/api/set_speed/${speed}`, { method: 'POST' });
    } catch (error) {
        console.error('Error setting speed:', error);
    }
}

// Iniciar actualización periódica
setInterval(updateSimulation, 100);

// Primera actualización inmediata
updateSimulation();