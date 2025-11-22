# Dimensiones del mapa
MAP_WIDTH = 800
MAP_HEIGHT = 600

# Parámetros de población
INITIAL_POPULATION = 25 
MAX_POPULATION = 200
FOOD_PER_DAY = 40

# Parámetros de mutación
MUTATION_RATE = 0.1  # 10% de probabilidad de mutación
MUTATION_STRENGTH = 0.15  # ±15% de cambio en el rasgo

# Rangos iniciales de rasgos (AJUSTADOS para movimiento más visible)
SPEED_RANGE = (2.0, 5.0)  # Velocidades más altas
SIZE_RANGE = (0.5, 2.0)
SENSE_RANGE = (80.0, 180.0)  # Mayor rango de detección

# Parámetros de energía (AJUSTADOS para días más largos)
BASE_ENERGY = 500.0  # Más energía inicial
FOOD_ENERGY = 80.0
BLOB_ENERGY = 200.0  # Energía al comer otro blob

# Parámetros de comportamiento
SIZE_EAT_THRESHOLD = 1.2  # 20% más grande para poder comer
FLEE_DISTANCE_MULTIPLIER = 1.5

# Servidor web
WEB_PORT = 10000


# XMPP (SPADE) - Configuración básica
XMPP_SERVER = "localhost"
AGENT_JID = "z3r007@xmpp.jp"
AGENT_PASSWORD = "12356890"