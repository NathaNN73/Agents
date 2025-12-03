# Dimensiones del mapa
MAP_WIDTH = 800
MAP_HEIGHT = 600

# Parámetros de parking
PARKING_ROWS = 4  # Reducido de 5 a 4 filas
PARKING_COLS = 6  # 6 columnas
TOTAL_SPOTS = PARKING_ROWS * PARKING_COLS  # 24 plazas

# Tipos de plazas
SPOTS_DISCAPACITADOS = 2
SPOTS_ELECTRICOS = 3  # Reducido proporcionalmente

# Layout del parking
SPOT_WIDTH = 40
SPOT_HEIGHT = 40
AISLE_WIDTH = 50  # Ancho de pasillos para vehículos

# Parámetros de vehículos
INITIAL_VEHICLES = 5  # Reducido proporcionalmente
MAX_VEHICLES = 25     # Reducido proporcionalmente
VEHICLE_ARRIVAL_INTERVAL = 4.0
VEHICLE_SPAWN_DELAY = 7.5  # Delay entre spawns de vehículos (segundos)
VEHICLE_SPEED = 5
VEHICLE_SIZE = 10  # Radio de colisión

# Punto de entrada (esquina superior izquierda)
ENTRY_POINT_X = 50
ENTRY_POINT_Y = 50

# Estrategia de asignación
ASSIGNMENT_STRATEGY = "greedy"  # "greedy", "balanced", "priority"

# Parámetros de comportamiento
PARKING_TIME_MIN = 60
PARKING_TIME_MAX = 300

# Servidor web
WEB_PORT = 10000

# XMPP (SPADE)
XMPP_SERVER = "localhost"
AGENT_JID = "z3r007@xmpp.jp"
AGENT_PASSWORD = "12356890"