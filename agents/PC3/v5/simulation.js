// Configuración del canvas
const canvas = document.getElementById('simulation-canvas');
const ctx = canvas.getContext('2d');

// Estado de la simulación
let simulationState = null;
let isPaused = false;
let lastUpdateTime = Date.now();

// Constantes
const API_BASE = '';
const UPDATE_INTERVAL = 100; // ms entre actualizaciones

// Inicializar
window.addEventListener('load', () => {
    console.log('🚀 Interfaz cargada');
    startPolling();
    animate();
});

async function fetchState() {
    try {
        const response = await fetch(`${API_BASE}/api/state`);
        if (!response.ok) throw new Error('Error fetching state');
        const data = await response.json();

        if (!data.error) {
            simulationState = data;
            updateConnectionStatus(true);
        }
    } catch (error) {
        console.error('Error:', error);
        updateConnectionStatus(false);
    }
}

async function togglePause() {
    try {
        const response = await fetch(`${API_BASE}/api/toggle_pause`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            isPaused = data.paused;
            updatePauseButton();
        }
    } catch (error) {
        console.error('Error toggling pause:', error);
    }
}

async function setSpeed(speed) {
    try {
        const response = await fetch(`${API_BASE}/api/set_speed/${speed}`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            console.log(`Velocidad cambiada a ${speed}x`);
        }
    } catch (error) {
        console.error('Error setting speed:', error);
    }
}

function updateSpeedDisplay(value) {
    document.getElementById('speed-value').textContent = parseFloat(value).toFixed(1);
}

// POLLING

function startPolling() {
    setInterval(async () => {
        await fetchState();
    }, UPDATE_INTERVAL);
}

// UI UPDATES

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (connected) {
        statusElement.textContent = 'Conectado';
        statusElement.className = 'status-connected';
    } else {
        statusElement.textContent = 'Desconectado';
        statusElement.className = 'status-disconnected';
    }
}

function updatePauseButton() {
    const btn = document.getElementById('pause-btn');
    if (isPaused) {
        btn.textContent = '▶️ Reanudar';
        btn.style.background = '#4CAF50';
    } else {
        btn.textContent = '⏸️ Pausar';
        btn.style.background = '#667eea';
    }
}

function updateStats(state) {
    document.getElementById('day').textContent = state.day;
    document.getElementById('population').textContent = state.stats.population;
    document.getElementById('total-born').textContent = state.stats.total_born;
    document.getElementById('total-died').textContent = state.stats.total_died;

    document.getElementById('avg-speed').textContent = state.stats.avg_speed.toFixed(2);
    document.getElementById('avg-size').textContent = state.stats.avg_size.toFixed(2);
    document.getElementById('avg-sense').textContent = state.stats.avg_sense.toFixed(2);
}

function updateProgressBar(state) {
    const progress = (state.time_in_day / state.day_duration) * 100;
    document.getElementById('progress-fill').style.width = `${progress}%`;
    document.getElementById('progress-text').textContent =
        `Día ${state.day} - ${progress.toFixed(0)}%`;
}

// RENDERING

function drawGrid() {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;

    const gridSize = 50;

    for (let x = 0; x <= canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }

    for (let y = 0; y <= canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
}

function drawFood(foodList) {
    foodList.forEach(food => {
        if (food.consumed) return;

        // Efecto de brillo animado
        const time = Date.now() / 1000;
        const pulse = Math.sin(time * 3) * 0.3 + 0.7;

        ctx.fillStyle = '#4CAF50';
        ctx.beginPath();
        ctx.arc(food.x, food.y, 4, 0, Math.PI * 2);
        ctx.fill();

        // Efecto de brillo
        ctx.fillStyle = `rgba(76, 175, 80, ${0.2 * pulse})`;
        ctx.beginPath();
        ctx.arc(food.x, food.y, 8, 0, Math.PI * 2);
        ctx.fill();
    });
}

function drawBlobs(blobs) {
    blobs.forEach(blob => {
        if (!blob.alive) return;

        const x = blob.x;
        const y = blob.y;
        const radius = blob.size * 8;

        // Dibujar rango de detección (sentido) - solo para algunos blobs seleccionados
        if (blob.id % 5 === 0) { // Mostrar solo 1 de cada 5 para no saturar
            ctx.strokeStyle = 'rgba(255, 152, 0, 0.15)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(x, y, blob.sense, 0, Math.PI * 2);
            ctx.stroke();
        }

        // Dibujar línea a casa si no está en casa
        if (!blob.at_home) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(blob.home_x, blob.home_y);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // Color basado en velocidad (más brillante = más rápido)
        const speedIntensity = Math.min(1, blob.speed / 5);
        const hue = 210; // Azul
        const lightness = 35 + speedIntensity * 35;

        // Sombra
        ctx.shadowColor = `hsl(${hue}, 80%, ${lightness}%)`;
        ctx.shadowBlur = 10;

        // Dibujar blob
        ctx.fillStyle = `hsl(${hue}, 80%, ${lightness}%)`;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0;

        // Borde
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Indicador de energía (barra)
        const energyRatio = Math.max(0, Math.min(1, blob.energy / 100));
        const barWidth = radius * 2;
        const barHeight = 4;
        const barX = x - radius;
        const barY = y - radius - 10;

        // Fondo de la barra
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(barX, barY, barWidth, barHeight);

        // Barra de energía con color según nivel
        if (energyRatio > 0.5) {
            ctx.fillStyle = '#4CAF50';
        } else if (energyRatio > 0.25) {
            ctx.fillStyle = '#FF9800';
        } else {
            ctx.fillStyle = '#f44336';
        }
        ctx.fillRect(barX, barY, barWidth * energyRatio, barHeight);

        // Indicador de comida recolectada
        if (blob.food_collected > 0) {
            ctx.fillStyle = '#FFD700';
            ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`🍎${blob.food_collected}`, x, y - radius - 18);
        }

        // Indicador de generación (pequeño)
        if (blob.generation > 0 && blob.generation < 10) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.font = '9px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`G${blob.generation}`, x, y + radius + 10);
        }

        // Punto de casa
        ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';
        ctx.beginPath();
        ctx.arc(blob.home_x, blob.home_y, 4, 0, Math.PI * 2);
        ctx.fill();
    });
}

function render() {
    if (!simulationState) return;

    // Limpiar canvas
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Dibujar grid
    drawGrid();

    // Dibujar comida
    drawFood(simulationState.food);

    // Dibujar blobs
    drawBlobs(simulationState.blobs);

    // Actualizar UI
    updateStats(simulationState);
    updateProgressBar(simulationState);
}

// ANIMATION LOOP

function animate() {
    render();
    requestAnimationFrame(animate);
}

function setSpeedPreset(speed) {
    document.getElementById('speed-slider').value = speed;
    updateSpeedDisplay(speed);
    setSpeed(speed);
}